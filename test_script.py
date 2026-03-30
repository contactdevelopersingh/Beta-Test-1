import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run_test():
    import os
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["titan_test_pipeline"]

    # insert a mock document
    await db.trade_journal.delete_many({})
    await db.trade_journal.insert_one({
        "user_id": "u1",
        "status": "closed",
        "exit_price": 105,
        "entry_price": 100,
        "quantity": 10,
        "direction": "BUY",
        "emotion_tag": "happy"
    })

    pipeline = [
        {"$match": {"user_id": "u1"}},
        {"$facet": {
            "general_stats": [
                {"$group": {
                    "_id": None,
                    "total_trades": {"$sum": 1},
                    "closed_trades": {
                        "$sum": {
                            "$cond": [
                                {"$and": [
                                    {"$eq": ["$status", "closed"]},
                                    {"$ne": ["$exit_price", None]},
                                    {"$type": "$exit_price"}
                                ]},
                                1, 0
                            ]
                        }
                    },
                    "wins": {
                        "$sum": {
                            "$cond": [
                                {"$and": [
                                    {"$eq": ["$status", "closed"]},
                                    {"$ne": ["$exit_price", None]},
                                    {"$type": "$exit_price"},
                                    {"$gt": [
                                        {"$cond": [
                                            {"$eq": ["$direction", "BUY"]},
                                            {"$multiply": [{"$subtract": ["$exit_price", {"$ifNull": ["$entry_price", 0]}]}, {"$ifNull": ["$quantity", 0]}]},
                                            {"$multiply": [{"$subtract": [{"$ifNull": ["$entry_price", 0]}, "$exit_price"]}, {"$ifNull": ["$quantity", 0]}]}
                                        ]},
                                        0
                                    ]}
                                ]},
                                1, 0
                            ]
                        }
                    },
                    "losses": {
                        "$sum": {
                            "$cond": [
                                {"$and": [
                                    {"$eq": ["$status", "closed"]},
                                    {"$ne": ["$exit_price", None]},
                                    {"$type": "$exit_price"},
                                    {"$lt": [
                                        {"$cond": [
                                            {"$eq": ["$direction", "BUY"]},
                                            {"$multiply": [{"$subtract": ["$exit_price", {"$ifNull": ["$entry_price", 0]}]}, {"$ifNull": ["$quantity", 0]}]},
                                            {"$multiply": [{"$subtract": [{"$ifNull": ["$entry_price", 0]}, "$exit_price"]}, {"$ifNull": ["$quantity", 0]}]}
                                        ]},
                                        0
                                    ]}
                                ]},
                                1, 0
                            ]
                        }
                    },
                    "total_pnl": {
                        "$sum": {
                            "$cond": [
                                {"$and": [
                                    {"$eq": ["$status", "closed"]},
                                    {"$ne": ["$exit_price", None]},
                                    {"$type": "$exit_price"}
                                ]},
                                {"$cond": [
                                    {"$eq": ["$direction", "BUY"]},
                                    {"$multiply": [{"$subtract": ["$exit_price", {"$ifNull": ["$entry_price", 0]}]}, {"$ifNull": ["$quantity", 0]}]},
                                    {"$multiply": [{"$subtract": [{"$ifNull": ["$entry_price", 0]}, "$exit_price"]}, {"$ifNull": ["$quantity", 0]}]}
                                ]},
                                0
                            ]
                        }
                    }
                }}
            ],
            "emotion_breakdown": [
                {"$group": {
                    "_id": {"$ifNull": ["$emotion_tag", "unknown"]},
                    "count": {"$sum": 1}
                }}
            ]
        }}
    ]

    try:
        res = await db.trade_journal.aggregate(pipeline).to_list(1)
        print("Success!", res)
    except Exception as e:
        print("Error!", e)

asyncio.run(run_test())
