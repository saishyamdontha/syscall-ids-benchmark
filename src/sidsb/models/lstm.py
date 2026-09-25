"""LSTM system-call language model.

Trained on normal traces only to predict the next syscall. A trace's anomaly
score is how surprised the model is by it (negative log-likelihood per token).
Early stopping uses a slice of the TRAINING normals, never calibration or test.
"""
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
                 trace_agg="mean", agg_window=20, seed=42, device="auto"):
        self.emb, self.hidden, self.layers, self.dropout = emb, hidden, layers, dropout
        self.chunk, self.stride, self.batch_size, self.lr = chunk, stride, batch_size, lr
        self.max_epochs, self.patience, self.holdout = max_epochs, patience, holdout
        self.trace_agg, self.agg_window, self.seed = trace_agg, agg_window, seed
        self.device = ("cuda" if torch.cuda.is_available() else "cpu") if device == "auto" else device
        self.name = f"lstm_{trace_agg}_s{seed}"
        self.history = []

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

        best, best_state, bad = float("inf"), None, 0
        for epoch in range(1, self.max_epochs + 1):
            tr = self._epoch_loss(train_chunks, train=True)
            va = self._epoch_loss(hold_chunks, train=False)
            self.history.append({"epoch": epoch, "train_nll": tr, "holdout_nll": va})
            print(f"    epoch {epoch:>2}  train_nll={tr:.4f}  holdout_nll={va:.4f}", flush=True)
            if va < best - 1e-4:
                best, bad = va, 0
                best_state = {k: v.detach().clone() for k, v in self.net.state_dict().items()}
            else:
                bad += 1
                if bad >= self.patience:
                    break
        self.net.load_state_dict(best_state)
        return self

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

    def score_one(self, seq):
        nll = self.token_nll(seq)
        if nll.size == 0:
            return 0.0
        if self.trace_agg == "mean":
            return float(nll.mean())
        if self.trace_agg == "max_window":
            w = min(self.agg_window, nll.size)
            return float(np.convolve(nll, np.ones(w) / w, mode="valid").max())
        raise ValueError(self.trace_agg)

    def score(self, seqs):
        return np.array([self.score_one(s) for s in seqs], dtype=float)
