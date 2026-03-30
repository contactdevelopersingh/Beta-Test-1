import asyncio
import time
from datetime import datetime, timezone

class UserPlans:
    def __init__(self):
        self.update_count = 0

    def find(self, *args, **kwargs):
        class Cursor:
            def sort(self, *args, **kwargs):
                return self
            async def to_list(self, *args, **kwargs):
                now = datetime.now(timezone.utc)
                return [{"user_id": f"user_{i}", "status": "active", "expires_at": "2000-01-01T00:00:00Z"} for i in range(500)]
        return Cursor()

    async def update_one(self, filter, update):
        self.update_count += 1
        await asyncio.sleep(0.001) # Simulate network/DB latency

    async def update_many(self, filter, update):
        self.update_count += 1
        await asyncio.sleep(0.005) # Simulate slightly longer single query latency

class MockDB:
    def __init__(self):
        self.user_plans = UserPlans()

db = MockDB()

async def get_all_plans_original():
    db.user_plans.update_count = 0
    plans = await db.user_plans.find({}, {"_id": 0}).sort("updated_at", -1).to_list(500)
    now = datetime.now(timezone.utc).isoformat()
    for p in plans:
        if p.get('status') == 'active' and p.get('expires_at', '') < now:
            p['status'] = 'expired'
            await db.user_plans.update_one({"user_id": p['user_id']}, {"$set": {"status": "expired"}})
    return {"plans": plans, "updates": db.user_plans.update_count}

async def get_all_plans_optimized():
    db.user_plans.update_count = 0
    plans = await db.user_plans.find({}, {"_id": 0}).sort("updated_at", -1).to_list(500)
    now = datetime.now(timezone.utc).isoformat()

    # Track which users need updating to update them in one go
    expired_user_ids = []

    for p in plans:
        if p.get('status') == 'active' and p.get('expires_at', '') < now:
            p['status'] = 'expired'
            expired_user_ids.append(p['user_id'])

    if expired_user_ids:
        await db.user_plans.update_many(
            {"user_id": {"$in": expired_user_ids}},
            {"$set": {"status": "expired"}}
        )

    return {"plans": plans, "updates": db.user_plans.update_count}

async def run():
    print("Running original...")
    t0 = time.time()
    res1 = await get_all_plans_original()
    t1 = time.time()
    orig_time = t1 - t0

    print("Running optimized...")
    t2 = time.time()
    res2 = await get_all_plans_optimized()
    t3 = time.time()
    opt_time = t3 - t2

    print(f"\nResults (simulating 500 expired plans):")
    print(f"Original: {orig_time:.4f}s ({res1['updates']} queries)")
    print(f"Optimized: {opt_time:.4f}s ({res2['updates']} queries)")
    print(f"Improvement: {orig_time / opt_time:.1f}x faster")

if __name__ == "__main__":
    asyncio.run(run())
