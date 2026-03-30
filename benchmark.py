import asyncio
import time

class MockCursor:
    def __init__(self, data):
        self.data = data

    async def to_list(self, length):
        return self.data[:length]

class MockCollection:
    def __init__(self, data):
        self.data = data

    def find(self, query, projection):
        # mock finding data and excluding _id
        res = []
        for d in self.data:
            new_d = d.copy()
            if projection and "_id" in projection and projection["_id"] == 0:
                new_d.pop("_id", None)
            res.append(new_d)
        return MockCursor(res)

    def aggregate(self, pipeline):
        # Extremely simplified mock of aggregation
        res = []
        total = 0
        count = 0
        for d in self.data[:100]:  # limit 100
            new_d = d.copy()
            new_d.pop("_id", None)
            res.append(new_d)
            total += d.get('quantity', 0) * d.get('buy_price', 0)
            count += 1

        agg_res = [{
            "_id": None,
            "total_invested": total,
            "holdings_count": count,
            "holdings": res
        }]
        return MockCursor(agg_res)

class MockDB:
    def __init__(self, data):
        self.portfolio = MockCollection(data)

async def benchmark_old(db):
    start = time.perf_counter()
    for _ in range(10000):
        holdings = await db.portfolio.find({"user_id": "test_user"}, {"_id": 0}).to_list(100)
        total_invested = sum(h['quantity'] * h['buy_price'] for h in holdings)
        res = {"total_invested": total_invested, "holdings_count": len(holdings), "holdings": holdings}
    return time.perf_counter() - start

async def benchmark_new(db):
    start = time.perf_counter()
    for _ in range(10000):
        pipeline = [
            {"$match": {"user_id": "test_user"}},
            {"$limit": 100},
            {"$unset": "_id"},
            {"$group": {
                "_id": None,
                "total_invested": {"$sum": {"$multiply": ["$quantity", "$buy_price"]}},
                "holdings_count": {"$sum": 1},
                "holdings": {"$push": "$$ROOT"}
            }}
        ]
        result = await db.portfolio.aggregate(pipeline).to_list(1)
        if not result:
            res = {"total_invested": 0, "holdings_count": 0, "holdings": []}
        else:
            data = result[0]
            res = {
                "total_invested": data.get("total_invested", 0),
                "holdings_count": data.get("holdings_count", 0),
                "holdings": data.get("holdings", [])
            }
    return time.perf_counter() - start

async def main():
    docs = []
    for i in range(100):
        docs.append({
            "_id": f"id_{i}",
            "user_id": "test_user",
            "quantity": 10.5,
            "buy_price": 100.0 + i
        })

    db = MockDB(docs)

    old_time = await benchmark_old(db)
    print(f"Old approach (Python aggregation): {old_time:.4f} seconds")

    new_time = await benchmark_new(db)
    print(f"New approach (MongoDB aggregation mock): {new_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
