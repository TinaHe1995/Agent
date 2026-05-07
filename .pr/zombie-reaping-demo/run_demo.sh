#!/usr/bin/env bash
set +e
section() { echo; echo "=========================================="; echo "$1"; echo "=========================================="; }

run_one() {
    local img="$1"
    local name="$2"
    local label="$3"
    section "$label"
    sudo docker rm -f "$name" >/dev/null 2>&1
    sudo docker run -d --name "$name" "$img" >/dev/null
    echo "Container started. Sleeping 8s for orphans to exit..."
    sleep 8
    echo
    echo "--- Process tree ---"
    sudo docker exec "$name" ps -ef
    echo
    echo "--- Zombies only (PID PPID STAT COMM) ---"
    sudo docker exec "$name" sh -c "ps -eo pid,ppid,stat,comm | awk '\$3 ~ /Z/' || true"
    echo
    echo "--- Zombie count ---"
    sudo docker exec "$name" sh -c "ps -eo stat | awk '\$1 ~ /Z/' | wc -l"
}

run_one zombie-demo:no-tini   no-tini-demo   "RUN 1: WITHOUT tini (mirrors main today)"
run_one zombie-demo:with-tini with-tini-demo "RUN 2: WITH tini (this PR)"
