"""Verify APScheduler is running and jobs are scheduled correctly."""
import requests
import sys

BACKEND_URL = "http://localhost:8000"  # Or Railway URL


def verify_scheduler():
    """Check scheduler health via /health endpoint.

    Returns:
        bool: True if scheduler is healthy, False otherwise
    """
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        response.raise_for_status()

        health = response.json()

        print("=" * 60)
        print("Scheduler Health Check")
        print("=" * 60)
        print(f"Status: {health.get('status', 'unknown')}")
        print(f"Service: {health.get('service', 'unknown')}")
        print(f"Version: {health.get('version', 'unknown')}")
        print()
        print("Scheduler Info:")

        scheduler = health.get('scheduler', {})
        print(f"  Running: {scheduler.get('running', False)}")
        print(f"  Jobs Count: {scheduler.get('jobs_count', 0)}")

        if 'next_run' in scheduler:
            print(f"  Next Run: {scheduler['next_run']}")
        else:
            print("  Next Run: Not scheduled")

        print("=" * 60)

        is_healthy = (
            scheduler.get('running', False) and
            scheduler.get('jobs_count', 0) > 0
        )

        if is_healthy:
            print("✅ Scheduler is healthy and jobs are scheduled!")
            return True
        else:
            print("❌ Scheduler is NOT running properly!")
            print("\nExpected:")
            print("  - Scheduler should be running")
            print("  - Jobs count should be > 0")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Health check failed: Could not connect to backend")
        print(f"   URL: {BACKEND_URL}/health")
        print("\nIs the backend running? Try:")
        print("  cd backend")
        print("  source venv/bin/activate")
        print("  uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


if __name__ == "__main__":
    success = verify_scheduler()
    sys.exit(0 if success else 1)
