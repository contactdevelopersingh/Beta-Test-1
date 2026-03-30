class MockDB:
    class user_plans:
        async def delete_many(self, *args, **kwargs):
            pass
        async def insert_many(self, *args, **kwargs):
            pass
        async def find(self, *args, **kwargs):
            class Cursor:
                def sort(self, *args, **kwargs):
                    return self
                async def to_list(self, *args, **kwargs):
                    from datetime import datetime, timezone, timedelta
                    now = datetime.now(timezone.utc)
                    expired_time = (now - timedelta(days=1)).isoformat()
                    return [{"user_id": f"user_{i}", "status": "active", "expires_at": expired_time} for i in range(500)]
            return Cursor()
        async def update_one(self, *args, **kwargs):
            pass

db = MockDB()
