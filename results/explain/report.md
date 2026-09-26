3-gram streaming detector, W=200, threshold at 1% of calibration normals ever alarming.
Each alert's evidence = the never-seen 3-grams in its alarm window; their count / W equals the
alarm score exactly. Syscall names: i386 table (ADFA-LD is 32-bit).

## Evidence per attack family (test)

| Family | Alerts / traces | Alerts with a syscall never seen in training | Most frequent evidence (alerts containing it; % of test normal traces containing it anywhere) |
|---|---|---|---|
| Adduser | 13 / 67 | 0 | `clock_gettime > _newselect > _newselect` (6; 0.1%)<br>`_newselect > writev > _newselect` (6; 0.1%)<br>`writev > _newselect > _newselect` (6; 0.2%) |
| Hydra_FTP | 22 / 111 | 0 | `ppoll > socketcall > socketcall` (13; 0.0%)<br>`ppoll > socketcall > alarm` (13; 0.0%)<br>`socketcall > socketcall > ppoll` (13; 0.1%) |
| Hydra_SSH | 19 / 137 | 0 | `_newselect > read > setitimer` (7; 0.1%)<br>`_newselect > clock_gettime > setitimer` (7; 0.1%)<br>`clock_gettime > setitimer > read` (7; 0.1%) |
| Java_Meterpreter | 13 / 88 | 0 | `clock_gettime > _newselect > clock_gettime` (7; 0.2%)<br>`_newselect > read > clock_gettime` (7; 0.2%)<br>`_newselect > setitimer > _newselect` (7; 0.1%) |
| Meterpreter | 7 / 55 | 0 | `_newselect > read > clock_gettime` (7; 0.2%)<br>`rt_sigprocmask > clock_gettime > _newselect` (7; 0.1%)<br>`_newselect > writev > _newselect` (7; 0.1%) |
| Web_Shell | 7 / 80 | 0 | `_newselect > _newselect > clock_gettime` (7; 0.3%)<br>`clock_gettime > read > _newselect` (7; 0.1%)<br>`_newselect > clock_gettime > _newselect` (7; 0.2%) |

## False alarms: 17 of 1750 test normal traces

| Evidence in false alarms | False alarms containing it |
|---|---|
| `_newselect > time > time` | 7 |
| `time > time > _newselect` | 6 |
| `_newselect > time > _newselect` | 6 |

## One example alert per family

**Adduser** - `UAD-Adduser-1-1613.txt` (766 syscalls): alarm after 202 syscalls, 124 of 200 3-grams in the window never seen in training (score 0.620 > threshold 0.547).

- at syscall 1: `[ read setitimer munmap ] clock_gettime _newselect _newselect setitimer`
- at syscall 2: `read [ setitimer munmap clock_gettime ] _newselect _newselect setitimer read`
- at syscall 3: `read setitimer [ munmap clock_gettime _newselect ] _newselect setitimer read rt_sigprocmask`

**Hydra_FTP** - `UAD-Hydra-FTP-1-1613.txt` (211 syscalls): alarm after 202 syscalls, 112 of 200 3-grams in the window never seen in training (score 0.560 > threshold 0.547).

- at syscall 2: `read [ _newselect read setitimer ] clock_gettime _newselect _newselect read`
- at syscall 3: `read _newselect [ read setitimer clock_gettime ] _newselect _newselect read _newselect`
- at syscall 4: `read _newselect read [ setitimer clock_gettime _newselect ] _newselect read _newselect read`

**Hydra_SSH** - `UAD-Hydra-SSH-2-1613.txt` (434 syscalls): alarm after 202 syscalls, 141 of 200 3-grams in the window never seen in training (score 0.705 > threshold 0.547).

- at syscall 2: `read [ mmap2 _newselect _newselect ] _newselect read read clock_gettime`
- at syscall 8: `_newselect _newselect read read [ clock_gettime clock_gettime _newselect ] read setitimer writev _newselect`
- at syscall 9: `_newselect read read clock_gettime [ clock_gettime _newselect read ] setitimer writev _newselect clock_gettime`

**Java_Meterpreter** - `UAD-Java-Meterpreter-1-1613.txt` (330 syscalls): alarm after 202 syscalls, 134 of 200 3-grams in the window never seen in training (score 0.670 > threshold 0.547).

- at syscall 1: `[ _newselect clock_gettime clock_gettime ] setitimer read read writev`
- at syscall 2: `_newselect [ clock_gettime clock_gettime setitimer ] read read writev setitimer`
- at syscall 3: `_newselect clock_gettime [ clock_gettime setitimer read ] read writev setitimer setitimer`

**Meterpreter** - `UAD-Meterpreter-1-1613.txt` (422 syscalls): alarm after 202 syscalls, 148 of 200 3-grams in the window never seen in training (score 0.740 > threshold 0.547).

- at syscall 1: `[ clock_gettime read rt_sigprocmask ] rt_sigprocmask rt_sigprocmask _newselect setitimer`
- at syscall 4: `clock_gettime read rt_sigprocmask [ rt_sigprocmask rt_sigprocmask _newselect ] setitimer rt_sigprocmask sigreturn writev`
- at syscall 5: `clock_gettime read rt_sigprocmask rt_sigprocmask [ rt_sigprocmask _newselect setitimer ] rt_sigprocmask sigreturn writev rt_sigprocmask`

**Web_Shell** - `UAD-WS10-1613.txt` (724 syscalls): alarm after 202 syscalls, 138 of 200 3-grams in the window never seen in training (score 0.690 > threshold 0.547).

- at syscall 1: `[ _newselect _newselect clock_gettime ] writev read clock_gettime read`
- at syscall 2: `_newselect [ _newselect clock_gettime writev ] read clock_gettime read _newselect`
- at syscall 6: `_newselect clock_gettime writev read [ clock_gettime read _newselect ] _newselect writev _newselect clock_gettime`

