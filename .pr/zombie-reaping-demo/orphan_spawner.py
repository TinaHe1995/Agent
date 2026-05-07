"""Mimics two real-world patterns the agent server triggers:

  1. Double-fork daemonization (e.g. chrome_crashpad_handler):
     parent fork()s, child fork()s and exits immediately, grandchild
     is re-parented to PID 1.
  2. Background-job outliving its parent shell (`bash -c 'git ... &'`
     where the launching bash exits before git):
     git is re-parented to PID 1 when bash exits.

When PID 1 doesn't reap, both patterns accumulate <defunct> processes
exactly like the live cloud sandbox in the PR description.
"""

import os
import subprocess
import sys
import time


def double_fork_daemon(lifetime: float) -> None:
    """Re-parents grandchild to PID 1 (chrome_crashpad-style)."""
    pid1 = os.fork()
    if pid1 > 0:
        os.waitpid(pid1, 0)  # reap our direct child (the middle process)
        return
    pid2 = os.fork()
    if pid2 > 0:
        os._exit(0)  # middle process exits → grandchild orphaned to PID 1
    # grandchild: pretend to be a daemon, then exit → ZOMBIE if PID 1 doesn't reap
    try:
        os.execvp("sleep", ["sleep", str(lifetime)])
    except Exception:
        time.sleep(lifetime)
        os._exit(0)


def background_git_then_exit() -> None:
    """Runs `bash -c 'git ... &'` and lets bash exit while git is still running.

    git becomes an orphan re-parented to PID 1 — same pattern that produced
    the [git] <defunct> entries in the live sandbox.
    """
    subprocess.run(
        [
            "bash",
            "-c",
            # Background a quick git invocation, then exit bash immediately.
            "git --version >/dev/null 2>&1 & disown; exit 0",
        ],
        check=False,
    )


print(f"PID 1 in this container is: {os.getpid()} ({sys.argv[0]})", flush=True)

# Spawn 4 chrome_crashpad-like double-fork daemons
for _ in range(4):
    double_fork_daemon(lifetime=2)

# And 4 orphan-git patterns
for _ in range(4):
    background_git_then_exit()

# Sleep so children exit, then idle so we can `docker exec ps` and observe state
time.sleep(4)
print("All children should have exited by now. Idling for inspection...", flush=True)
time.sleep(120)
