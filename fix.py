# The user has explicitly stated:
#   "if pnl is already saved in the DB, I don't need to recalculate it!"
# Wait, let's look at get_community_stats:
#   pipeline = [
#       {"$match": {"status": "closed", "pnl": {"$exists": True, "$gt": 0}}},
#       {"$count": "wins"}
#   ]
# Oh!! PNL is saved as a field in the document: "pnl": pnl
# Wait, look at create_journal_entry:
#     if entry.get('exit_price') and entry['exit_price'] > 0:
#         if entry['direction'] == 'BUY':
#             pnl = round((entry['exit_price'] - entry['entry_price']) * entry['quantity'], 2)
#         else:
#             pnl = round((entry['entry_price'] - entry['exit_price']) * entry['quantity'], 2)
#     doc = { ... "pnl": pnl ... }
#
# Wow, if `pnl` is already stored on the document, why was I doing all the multiplication in the aggregation pipeline?!
# I can just sum the `pnl` directly!!
