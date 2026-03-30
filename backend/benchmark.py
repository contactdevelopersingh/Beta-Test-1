import asyncio
import time
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import sys
sys.path.append("backend")
from server import get_all_plans
import server
from test_mock import db
server.db = db

async def run_benchmark():
    # Insert some active plans that are expired
    await db.user_plans.delete_many({})

    now = datetime.now(timezone.utc)
    expired_time = (now - timedelta(days=1)).isoformat()

    # Insert 1000 expired plans
    plans = []
    for i in range(500):
        plans.append({
            "user_id": f"user_{i}",
            "status": "active",
            "expires_at": expired_time,
            "updated_at": now.isoformat()
        })

    if plans:
        await db.user_plans.insert_many(plans)

    print("Inserted 500 expired active plans")

    # Measure get_all_plans execution time
    start = time.time()
    await get_all_plans()
    end = time.time()

    print(f"Time taken: {end - start:.4f} seconds")

    # Cleanup
    await db.user_plans.delete_many({})

if __name__ == "__main__":
    asyncio.run(run_benchmark())
