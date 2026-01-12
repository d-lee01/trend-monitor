"""Manual integration test for collection trigger.

Usage:
    python -m scripts.test_manual_collection

Environment Variables:
    BACKEND_URL: Backend API URL (default: http://localhost:8000)
    TEST_USERNAME: Username for authentication (default: dave)
    TEST_PASSWORD: Password for authentication (required, no default)
"""
import asyncio
import httpx
import os
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
USERNAME = os.getenv("TEST_USERNAME", "dave")
PASSWORD = os.getenv("TEST_PASSWORD")

if not PASSWORD:
    print("ERROR: TEST_PASSWORD environment variable is required")
    print("Usage: TEST_PASSWORD=changeme123 python -m scripts.test_manual_collection")
    exit(1)


async def main():
    print("=" * 60)
    print("Manual Collection Integration Test")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # Login
        print("\n1. Logging in...")
        try:
            login_response = await client.post(
                f"{BACKEND_URL}/auth/login",
                data={"username": USERNAME, "password": PASSWORD}
            )
            if login_response.status_code != 200:
                print(f"   ❌ Login failed: {login_response.status_code}")
                print(f"   Response: {login_response.text}")
                return

            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("   ✅ Logged in successfully")
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return

        # Trigger collection
        print("\n2. Triggering collection...")
        try:
            collect_response = await client.post(
                f"{BACKEND_URL}/collect",
                headers=headers
            )

            if collect_response.status_code == 202:
                data = collect_response.json()
                collection_id = data["collection_id"]
                print(f"   ✅ Collection started: {collection_id}")
                print(f"   Message: {data['message']}")
            elif collect_response.status_code == 409:
                print("   ⚠️  Collection already in progress")
                # Try to get existing collection status
                print("\n3. Checking existing collection status...")
                # Note: We'd need the collection_id to check status
                return
            else:
                print(f"   ❌ Failed: {collect_response.status_code}")
                print(f"   Response: {collect_response.text}")
                return
        except Exception as e:
            print(f"   ❌ Collection trigger error: {e}")
            return

        # Poll status
        print("\n3. Monitoring collection progress...")
        print("   (Press Ctrl+C to stop monitoring)")
        try:
            while True:
                await asyncio.sleep(30)  # Poll every 30 seconds

                status_response = await client.get(
                    f"{BACKEND_URL}/collections/{collection_id}",
                    headers=headers
                )

                if status_response.status_code != 200:
                    print(f"   ⚠️ Status check failed: {status_response.status_code}")
                    break

                status = status_response.json()

                print(f"   Status: {status['status']} | Duration: {status['duration_minutes']:.1f} min | Trends: {status['trends_found']}")

                if status["status"] in ["completed", "failed"]:
                    break
        except KeyboardInterrupt:
            print("\n   Monitoring stopped by user")
            print(f"   Collection {collection_id} is still running in background")
            return
        except Exception as e:
            print(f"   ❌ Status polling error: {e}")
            return

        # Final results
        print("\n4. Collection Results:")
        print(f"   Status: {status['status']}")
        print(f"   Trends found: {status['trends_found']}")
        print(f"   Duration: {status['duration_minutes']:.1f} minutes")

        if status.get("errors"):
            print(f"\n   Errors encountered:")
            for error in status["errors"]:
                print(f"   - {error}")

        print("\n" + "=" * 60)
        if status["status"] == "completed":
            print("✅ Integration test complete!")
        else:
            print("❌ Collection failed")
        print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
