import requests
import time
import sys

BASE_URL = "http://localhost:8000"


def test_health():
    print(f"Testing {BASE_URL}/docs...")
    try:
        resp = requests.get(f"{BASE_URL}/docs")
        if resp.status_code == 200:
            print("[OK] Server is UP")
        else:
            print(f"[FAIL] Server returned {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        sys.exit(1)


def test_agent_run():
    print("Testing /agent/run...")
    payload = {"task": "Echo hello world", "repo_path": "."}
    try:
        resp = requests.post(f"{BASE_URL}/agent/run", json=payload)
        if resp.status_code == 200:
            job_id = resp.json()["job_id"]
            print(f"[OK] Job submitted. ID: {job_id}")
            return job_id
        else:
            print(f"[FAIL] Failed to submit job: {resp.text}")
            sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Run failed: {e}")
        sys.exit(1)


def wait_for_job(job_id):
    print(f"Polling status for job {job_id}...")
    for _ in range(10):
        resp = requests.get(f"{BASE_URL}/agent/status/{job_id}")
        data = resp.json()
        state = data["state"]
        print(f"State: {state}")

        if state in [
            "COMPLETED",
            "STOPPED_SAFE",
            "STOPPED_ERROR",
            "TESTS_PASSED",
            "TESTS_FAILED",
        ]:
            print("[OK] Job finished execution.")
            return

        time.sleep(1)

    print(
        "⚠️ Timed out waiting for job completion (this is expected for long tasks, but 'Echo' should be fast)."
    )


if __name__ == "__main__":
    test_health()
    jid = test_agent_run()
    wait_for_job(jid)
