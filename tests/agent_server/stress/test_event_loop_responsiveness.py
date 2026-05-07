"""Cross-cutting canary: /health stays responsive under each background load.

Why this exists:
    Most agent-server bugs that cause user-visible "the server hangs" symptoms
    boil down to sync I/O on the asyncio thread. Each individual suite checks
    this in its specific scenario. This canary checks it under a representative
    mix of loads in one place — cheap to add, catches the regression class we
    forgot to test specifically.

Loads exercised:
    - Long bash command (sleep + final marker) — exercises bash_service.
    - Busy conversation listing on a seeded store — exercises persistence.

Loads NOT exercised here (covered by their own suites):
    - Slow webhook (test_slow_webhook.py).
    - Slow-loris websocket (test_slow_websocket_consumer.py).
    - High-volume bash output (test_high_volume_bash_output.py).
"""

import asyncio
import statistics
import time

import pytest

from openhands.agent_server.bash_service import BashEventService
from openhands.agent_server.conversation_service import ConversationService
from openhands.agent_server.models import StartConversationRequest
from openhands.sdk import Agent
from openhands.sdk.workspace import LocalWorkspace
from tests.agent_server.stress.budgets import EVENT_LOOP_RESPONSIVENESS
from tests.agent_server.stress.scripts import placeholder_llm


pytestmark = pytest.mark.stress


async def _measure_health_p95_p99(client, *, samples: int) -> tuple[float, float]:
    latencies: list[float] = []
    for _ in range(samples):
        t0 = time.monotonic()
        resp = await client.get("/health")
        latencies.append(time.monotonic() - t0)
        assert resp.status_code == 200
    quantiles = statistics.quantiles(latencies, n=100)
    # quantiles returns 99 cut-points; index 94 ≈ p95, 98 ≈ p99.
    return quantiles[94], quantiles[98]


def _assert_within_budget(name: str, p95: float, p99: float) -> None:
    assert p95 < EVENT_LOOP_RESPONSIVENESS.health_p95_s, (
        f"under load '{name}', /health p95 = {p95 * 1000:.1f} ms exceeded "
        f"{EVENT_LOOP_RESPONSIVENESS.health_p95_s * 1000:.0f} ms. The event "
        f"loop is being blocked by this load."
    )
    assert p99 < EVENT_LOOP_RESPONSIVENESS.health_p99_s, (
        f"under load '{name}', /health p99 = {p99 * 1000:.1f} ms exceeded "
        f"{EVENT_LOOP_RESPONSIVENESS.health_p99_s * 1000:.0f} ms."
    )


async def test_health_responsive_under_long_bash(
    client,
    bash_service: BashEventService,
):
    """A long bash command must not starve the event loop."""
    samples = EVENT_LOOP_RESPONSIVENESS.health_samples

    # Baseline: no load.
    p95_baseline, p99_baseline = await _measure_health_p95_p99(client, samples=samples)
    _assert_within_budget("baseline", p95_baseline, p99_baseline)

    # Start a 4s bash. Take samples while it runs.
    resp = await client.post(
        "/api/bash/start_bash_command",
        json={"command": "sleep 4; echo done", "timeout": 10},
    )
    assert resp.status_code == 200

    # Sample for ~3s of the bash command's lifetime.
    p95_under_bash, p99_under_bash = await _measure_health_p95_p99(
        client, samples=samples
    )
    _assert_within_budget("long_bash", p95_under_bash, p99_under_bash)


async def test_health_responsive_under_busy_listing(
    conversation_service: ConversationService,
    client,
    tmp_path,
):
    """High-volume conversation listing in parallel must not starve /health."""
    samples = EVENT_LOOP_RESPONSIVENESS.health_samples
    workspace = str(tmp_path / "ws")
    (tmp_path / "ws").mkdir()

    # Seed a modest store.
    seed_n = 100
    seed_sem = asyncio.Semaphore(8)

    async def _seed(i: int):
        async with seed_sem:
            request = StartConversationRequest(
                agent=Agent(llm=placeholder_llm(f"resp-canary-{i}"), tools=[]),
                workspace=LocalWorkspace(working_dir=workspace),
                autotitle=False,
            )
            await conversation_service.start_conversation(request)

    await asyncio.gather(*[_seed(i) for i in range(seed_n)])

    # Drive listing in the background.
    stop = asyncio.Event()

    async def _listing_loop():
        while not stop.is_set():
            await client.get(
                "/api/conversations/search",
                params={"limit": 50, "sort_order": "CREATED_AT_DESC"},
            )

    bg_task = asyncio.create_task(_listing_loop())
    try:
        # Brief warm-up so the listing loop is hot before we measure.
        await asyncio.sleep(0.1)
        p95, p99 = await _measure_health_p95_p99(client, samples=samples)
        _assert_within_budget("busy_listing", p95, p99)
    finally:
        stop.set()
        await bg_task
