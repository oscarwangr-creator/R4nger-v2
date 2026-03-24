from __future__ import annotations

import os
import time
import requests


API_URL = os.getenv("INTEL_API_URL", "http://api:8000")
AGENT_ID = os.getenv("AGENT_ID", "agent-local-1")


def heartbeat() -> None:
    payload = {"agent_id": AGENT_ID, "status": "online"}
    try:
        requests.post(f"{API_URL}/agents/heartbeat", json=payload, timeout=10)
    except Exception:
        pass


def pull_and_run_loop() -> None:
    while True:
        heartbeat()
        try:
            response = requests.post(
                f"{API_URL}/pipeline/run",
                json={"pipeline": "attack_surface_pipeline", "payload": {"input_type": "domain", "value": "example.com"}},
                timeout=120,
            )
            print(response.json())
        except Exception as exc:
            print(f"Agent execution error: {exc}")
        time.sleep(120)


if __name__ == "__main__":
    pull_and_run_loop()
