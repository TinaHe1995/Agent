# Zombie reaping demo for PR #3043

This is a self-contained reproduction of the zombie-process accumulation
described in #3042, and a head-to-head verification that adding `tini` as the
container's PID 1 fixes it.

## What it does

`orphan_spawner.py` runs as PID 1 in a small container and exercises the two
real-world patterns that produce the zombies seen in the live cloud sandbox:

1. **Double-fork daemonization** — same trick `chrome_crashpad_handler` uses.
   The grandchild is reparented to PID 1.
2. **Background job outliving its bash** — `bash -c 'git --version & disown;
   exit 0'`. When bash exits, `git` is reparented to PID 1.

Two Dockerfiles wrap the same script:

| File                   | ENTRYPOINT (mirrors)                      |
| ---------------------- | ----------------------------------------- |
| `Dockerfile.no-tini`   | `main` today: `["python", "..."]`         |
| `Dockerfile.with-tini` | This PR: `["tini", "--", "python", "..."]` |

## Run it

```bash
docker build -t zombie-demo:no-tini   -f Dockerfile.no-tini   .
docker build -t zombie-demo:with-tini -f Dockerfile.with-tini .
bash run_demo.sh
```

`run_demo.sh` starts each image, waits for the orphans to exit, then prints
`ps -ef` and a zombie count from inside the container.

## Observed result

Without `tini` (mirrors `main`):

```
PID  PPID  STAT  COMM
 56     1  Z     sleep
 58     1  Z     sleep
 60     1  Z     sleep
 62     1  Z     sleep
 64     1  Z     git
 66     1  Z     git
 68     1  Z     git
 70     1  Z     git
zombies: 8
```

With `tini` (this PR):

```
PID  PPID  STAT  COMM
(none)
zombies: 0
```

Both the double-fork daemons *and* the orphaned-git-from-bash path are reaped
by `tini`, with no changes to the bash tool itself.
