with open("backend/server.py", "r") as f:
    content = f.read()

search_block = """    elif data.asset_type == "indian":
        live_item = next((i for i in _live['indian'] if i['id'] == data.asset_id), None)
        if live_item:
            market_context = f"Current Price: INR {live_item['price']:,.2f}, 24h Change: {live_item['change_24h']:.2f}%, High: {live_item.get('high', 0)}, Low: {live_item.get('low', 0)}, Volume: {live_item.get('volume', 0):,}"
    if not market_context:"""

replace_block = """    elif data.asset_type == "indian":
        live_item = next((i for i in _live['indian'] if i['id'] == data.asset_id), None)
        if live_item:
            market_context = f"Current Price: INR {live_item['price']:,.2f}, 24h Change: {live_item['change_24h']:.2f}%, High: {live_item.get('high', 0)}, Low: {live_item.get('low', 0)}, Volume: {live_item.get('volume', 0):,}"
        elif data.asset_id.startswith("NSE:") or data.asset_id.startswith("BSE:"):
            # Fetch dynamically using yfinance
            try:
                prefix, sym = data.asset_id.split(":", 1)
                yf_symbol = sym + (".NS" if prefix == "NSE" else ".BO")
                import yfinance as yf
                t = yf.Ticker(yf_symbol)
                info = t.fast_info
                current_price = info.get('last_price', 0)
                if current_price:
                    market_context = f"Current Price: INR {current_price:,.2f}, Volume: {info.get('last_volume', 0):,}"
            except Exception as e:
                logger.error(f"Dynamic yfinance fetch failed for {data.asset_id}: {e}")
    if not market_context:"""

content = content.replace(search_block, replace_block)

with open("backend/server.py", "w") as f:
    f.write(content)
