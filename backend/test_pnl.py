import asyncio

async def test_it():
    print("Wait! `pnl` is already saved on the document in the DB!!")
    print("If pnl is already saved in the DB, I don't need to recalculate it!")

asyncio.run(test_it())
