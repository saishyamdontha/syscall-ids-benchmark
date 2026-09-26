"""LSTM system-call language model.

Trained on normal traces only to predict the next syscall. A trace's anomaly
score is how surprised the model is by it (negative log-likelihood per token).
Early stopping uses a slice of the TRAINING normals, never calibration or test.

Checkpointing: set checkpoint_dir (or env var SIDSB_CKPT_DIR). Training state is
saved after every epoch; rerunning the same config resumes where it stopped, and
a finished model is reloaded instead of retrained.
"""
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn

PAD, UNK = 0, 1


class _Net(nn.Module):
    def __init__(self, vocab, emb, hidden, layers, dropout):
        super().__init__()
        self.emb = nn.Embedding(vocab, emb, padding_idx=PAD)
        self.lstm = nn.LSTM(emb, hidden, layers, batch_first=True,
                            dropout=dropout if layers > 1 else 0.0)
        self.out = nn.Linear(hidden, vocab)

    def forward(self, x):
        h, _ = self.lstm(self.emb(x))
        return self.out(h)


class LstmLM:
    def __init__(self, emb=64, hidden=128, layers=2, dropout=0.2, chunk=64, stride=32,
                 batch_size=128, lr=2e-3, max_epochs=30, patience=4, holdout=0.1,
                 trace_agg="mean", agg_window=20, seed=42, device="auto",
                 checkpoint_dir=None):
        self.emb, self.hidden, self.layers, self.dropout = emb, hidden, layers, dropout
        self.chunk, self.stride, self.batch_size, self.lr = chunk, stride, batch_size, lr
        self.max_epochs, self.patience, self.holdout = max_epochs, patience, holdout
        self.trace_agg, self.agg_window, self.seed = trace_agg, agg_window, seed
        self.device = ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
        self.name = f"lstm_{trace_agg}_s{seed}"
        self.history = []
        self.checkpoint_dir = checkpoint_dir or os.environ.get("SIDSB_CKPT_DIR")

    # ---- checkpointing ----------------------------------------------------
    def _run_id(self, seqs):
        """Hash of everything that determines the trained weights (not trace_agg,
        which only affects scoring). Same id -> safe to resume or reuse."""
        h = hashlib.sha256()
        cfg = {k: getattr(self, k) for k in ("emb", "hidden", "layers", "dropout", "chunk",
               "stride", "batch_size", "lr", "max_epochs", "patience", "holdout", "seed")}
        h.update(json.dumps(cfg, sort_keys=True).encode())
        for s in seqs:
            h.update(np.asarray(s, dtype=np.int64).tobytes())
            h.update(b"|")
        return h.hexdigest()[:16]

    def _ckpt_path(self, run_id):
        d = Path(self.checkpoint_dir)
        d.mkdir(parents=True, exist_ok=True)
        return d / f"lstm_s{self.seed}_{run_id}.pt"

    def _save(self, path, epoch, best, best_state, bad, done):
        state = {
            "epoch": epoch, "best": best, "bad": bad, "done": done,
            "vocab": self.vocab, "history": self.history,
            "net": self.net.state_dict(), "best_state": best_state,
            "opt": self.opt.state_dict(),
            "np_rng": self.rng.bit_generator.state,
            "torch_rng": torch.get_rng_state(),
            "cuda_rng": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        }
        tmp = path.with_suffix(".tmp")
        torch.save(state, tmp)
        os.replace(tmp, path)  # atomic: a crash mid-save never corrupts the checkpoint

    # ---- data ---------------------------------------------------------------
    def _encode(self, seq):
        return [self.vocab.get(s, UNK) for s in seq]

    def _chunks(self, seqs):
        out = []
        for s in seqs:
            ids = self._encode(s)
            if len(ids) < 2:
                continue
            if len(ids) <= self.chunk + 1:
                out.append(ids)
                continue
            for i in range(0, len(ids) - self.chunk, self.stride):
                out.append(ids[i:i + self.chunk + 1])
        return out

    @staticmethod
    def _pad(batch):
        n = max(len(b) for b in batch)
        return torch.tensor([b + [PAD] * (n - len(b)) for b in batch], dtype=torch.long)

    # ---- training -----------------------------------------------------------
    def _epoch_loss(self, chunks, train):
        self.net.train(train)
        total, count = 0.0, 0
        order = self.rng.permutation(len(chunks)) if train else np.arange(len(chunks))
        for i in range(0, len(order), self.batch_size):
            batch = self._pad([chunks[j] for j in order[i:i + self.batch_size]]).to(self.device)
            x, y = batch[:, :-1], batch[:, 1:]
            with torch.set_grad_enabled(train):
                logits = self.net(x)
                loss = self.loss_fn(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
                if train:
                    self.opt.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
                    self.opt.step()
            n = int((y != PAD).sum())
            total += loss.item() * n
            count += n
        return total / max(count, 1)

    def fit(self, seqs):
        torch.manual_seed(self.seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        self.rng = np.random.default_rng(self.seed)
        syscalls = sorted({s for seq in seqs for s in seq})
        self.vocab = {s: i + 2 for i, s in enumerate(syscalls)}

        idx = self.rng.permutation(len(seqs))
        n_hold = max(1, int(len(seqs) * self.holdout))
        hold = [seqs[i] for i in idx[:n_hold]]
        fit = [seqs[i] for i in idx[n_hold:]]
        train_chunks, hold_chunks = self._chunks(fit), self._chunks(hold)

        self.net = _Net(len(self.vocab) + 2, self.emb, self.hidden, self.layers,
                        self.dropout).to(self.device)
        self.opt = torch.optim.Adam(self.net.parameters(), lr=self.lr)
        self.loss_fn = nn.CrossEntropyLoss(ignore_index=PAD)

        best, best_state, bad, start = float("inf"), None, 0, 1
        path = self._ckpt_path(self._run_id(seqs)) if self.checkpoint_dir else None
        if path is not None and path.exists():
            ck = torch.load(path, map_location=self.device, weights_only=False)
            self.vocab, self.history = ck["vocab"], ck["history"]
            best, bad, best_state = ck["best"], ck["bad"], ck["best_state"]
            if ck["done"]:
                print(f"    loaded finished checkpoint {path.name} (epoch {ck['epoch']})", flush=True)
                self.net.load_state_dict(best_state)
                return self
            self.net.load_state_dict(ck["net"])
            self.opt.load_state_dict(ck["opt"])
            self.rng.bit_generator.state = ck["np_rng"]
            torch.set_rng_state(ck["torch_rng"].cpu())          # RNG states must be CPU ByteTensors
            if ck["cuda_rng"] is not None and torch.cuda.is_available():
                torch.cuda.set_rng_state_all([t.cpu() for t in ck["cuda_rng"]])
            start = ck["epoch"] + 1
            print(f"    resuming {path.name} from epoch {start}", flush=True)

        for epoch in range(start, self.max_epochs + 1):
            tr = self._epoch_loss(train_chunks, train=True)
            va = self._epoch_loss(hold_chunks, train=False)
            self.history.append({"epoch": epoch, "train_nll": tr, "holdout_nll": va})
            print(f"    epoch {epoch:>2}  train_nll={tr:.4f}  holdout_nll={va:.4f}", flush=True)
            if va < best - 1e-4:
                best, bad = va, 0
                best_state = {k: v.detach().clone() for k, v in self.net.state_dict().items()}
            else:
                bad += 1
            stop = bad >= self.patience or epoch == self.max_epochs
            if path is not None:
                self._save(path, epoch, best, best_state, bad, done=stop)
            if stop:
                break
        self.net.load_state_dict(best_state)
        return self

    # ---- scoring ------------------------------------------------------------
    @torch.no_grad()
    def token_nll(self, seq):
        """Per-token surprise for one trace (first token has no prediction)."""
        self.net.eval()
        ids = self._encode(seq)
        if len(ids) < 2:
            return np.zeros(0)
        x = torch.tensor([ids[:-1]], dtype=torch.long, device=self.device)
        y = torch.tensor(ids[1:], dtype=torch.long, device=self.device)
        logp = torch.log_softmax(self.net(x)[0], dim=-1)
        return (-logp[torch.arange(len(y)), y]).cpu().numpy()

    def _aggregate(self, nll):
        if nll.size == 0:
            return 0.0
        if self.trace_agg == "mean":
            return float(nll.mean())
        if self.trace_agg == "max_window":
            w = min(self.agg_window, nll.size)
            return float(np.convolve(nll, np.ones(w) / w, mode="valid").max())
        raise ValueError(self.trace_agg)

    def score_one(self, seq):
        return self._aggregate(self.token_nll(seq))

    @torch.no_grad()
    def score(self, seqs, batch_size=64):
        """Batched scoring: traces sorted by length, right-padded. Padding at the
        end cannot affect earlier predictions of a left-to-right LSTM."""
        self.net.eval()
        enc = [self._encode(s) for s in seqs]
        out = np.zeros(len(seqs), dtype=float)
        order = [i for i in sorted(range(len(enc)), key=lambda i: len(enc[i])) if len(enc[i]) >= 2]
        for b in range(0, len(order), batch_size):
            idxs = order[b:b + batch_size]
            x = self._pad([enc[i] for i in idxs]).to(self.device)
            inp, tgt = x[:, :-1], x[:, 1:]
            logp = torch.log_softmax(self.net(inp), dim=-1)
            nll = (-logp.gather(2, tgt.unsqueeze(-1)).squeeze(-1)).cpu().numpy()
            mask = (tgt != PAD).cpu().numpy()
            for row, i in enumerate(idxs):
                out[i] = self._aggregate(nll[row][mask[row]])
        return out
