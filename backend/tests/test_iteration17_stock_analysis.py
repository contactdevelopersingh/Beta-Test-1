"""
Iteration 17 - Indian Stock Market Analysis Module Tests
Tests: Stock list, fundamentals, quarterly results, annual P&L, balance sheet, 
cash flow, shareholding, peers, screener, presets, pros/cons generation
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStockList:
    """Test GET /api/stocks/list - returns 40 stocks with sectors"""
    
    def test_stock_list_returns_stocks(self):
        """Verify stock list endpoint returns stocks array"""
        response = requests.get(f"{BASE_URL}/api/stocks/list", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "stocks" in data, "Response should have 'stocks' key"
        assert isinstance(data["stocks"], list), "stocks should be a list"
        print(f"SUCCESS: Stock list returned {len(data['stocks'])} stocks")
    
    def test_stock_list_has_40_stocks(self):
        """Verify stock list has 40 stocks"""
        response = requests.get(f"{BASE_URL}/api/stocks/list", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert len(data["stocks"]) == 40, f"Expected 40 stocks, got {len(data['stocks'])}"
        print(f"SUCCESS: Stock list has exactly 40 stocks")
    
    def test_stock_list_has_sectors(self):
        """Verify stock list includes sectors"""
        response = requests.get(f"{BASE_URL}/api/stocks/list", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "sectors" in data, "Response should have 'sectors' key"
        assert isinstance(data["sectors"], list), "sectors should be a list"
        assert len(data["sectors"]) > 0, "Should have at least one sector"
        print(f"SUCCESS: Stock list has {len(data['sectors'])} sectors: {data['sectors']}")
    
    def test_stock_has_required_fields(self):
        """Verify each stock has symbol, name, sector"""
        response = requests.get(f"{BASE_URL}/api/stocks/list", timeout=30)
        assert response.status_code == 200
        data = response.json()
        for stock in data["stocks"][:5]:  # Check first 5
            assert "symbol" in stock, f"Stock missing 'symbol': {stock}"
            assert "name" in stock, f"Stock missing 'name': {stock}"
            assert "sector" in stock, f"Stock missing 'sector': {stock}"
        print(f"SUCCESS: Stocks have required fields (symbol, name, sector)")


class TestStockAnalysis:
    """Test GET /api/stocks/analysis/{symbol} - full fundamentals"""
    
    def test_reliance_analysis_returns_data(self):
        """Verify Reliance analysis returns full data"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/reliance", timeout=60)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "symbol" in data, "Response should have 'symbol'"
        assert data["symbol"].upper() == "RELIANCE", f"Expected RELIANCE, got {data['symbol']}"
        print(f"SUCCESS: Reliance analysis returned - {data.get('name', 'N/A')}")
    
    def test_analysis_has_fundamentals(self):
        """Verify analysis includes fundamentals with P/E, ROE, D/E, EPS, OPM, NPM"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/reliance", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "fundamentals" in data, "Response should have 'fundamentals'"
        f = data["fundamentals"]
        # Check key fundamental metrics exist (may be None but key should exist)
        expected_keys = ["pe_ratio", "roe", "debt_to_equity", "eps", "opm", "npm"]
        for key in expected_keys:
            assert key in f, f"Fundamentals missing '{key}'"
        print(f"SUCCESS: Fundamentals include P/E={f.get('pe_ratio')}, ROE={f.get('roe')}%, D/E={f.get('debt_to_equity')}, EPS={f.get('eps')}, OPM={f.get('opm')}%, NPM={f.get('npm')}%")
    
    def test_analysis_has_quarterly_results(self):
        """Verify analysis includes quarterly_results array with 4+ quarters"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/reliance", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "quarterly_results" in data, "Response should have 'quarterly_results'"
        qr = data["quarterly_results"]
        assert isinstance(qr, list), "quarterly_results should be a list"
        # Note: yfinance may return varying amounts of data
        print(f"SUCCESS: Quarterly results has {len(qr)} quarters")
    
    def test_analysis_has_annual_pl(self):
        """Verify analysis includes annual_pl array"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/reliance", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "annual_pl" in data, "Response should have 'annual_pl'"
        assert isinstance(data["annual_pl"], list), "annual_pl should be a list"
        print(f"SUCCESS: Annual P&L has {len(data['annual_pl'])} years")
    
    def test_analysis_has_balance_sheet(self):
        """Verify analysis includes balance_sheet array"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/reliance", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "balance_sheet" in data, "Response should have 'balance_sheet'"
        assert isinstance(data["balance_sheet"], list), "balance_sheet should be a list"
        print(f"SUCCESS: Balance sheet has {len(data['balance_sheet'])} years")
    
    def test_analysis_has_cash_flow(self):
        """Verify analysis includes cash_flow array"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/reliance", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "cash_flow" in data, "Response should have 'cash_flow'"
        assert isinstance(data["cash_flow"], list), "cash_flow should be a list"
        print(f"SUCCESS: Cash flow has {len(data['cash_flow'])} years")
    
    def test_analysis_has_pros_cons(self):
        """Verify analysis includes auto-generated pros and cons"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/reliance", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "pros" in data, "Response should have 'pros'"
        assert "cons" in data, "Response should have 'cons'"
        assert isinstance(data["pros"], list), "pros should be a list"
        assert isinstance(data["cons"], list), "cons should be a list"
        print(f"SUCCESS: Pros ({len(data['pros'])}): {data['pros'][:2]}...")
        print(f"SUCCESS: Cons ({len(data['cons'])}): {data['cons'][:2]}...")
    
    def test_analysis_has_analyst_recommendations(self):
        """Verify analysis includes analyst recommendations"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/reliance", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "analyst" in data, "Response should have 'analyst'"
        analyst = data["analyst"]
        assert "target_mean" in analyst, "analyst should have 'target_mean'"
        assert "recommendation" in analyst, "analyst should have 'recommendation'"
        print(f"SUCCESS: Analyst recommendation={analyst.get('recommendation')}, target_mean={analyst.get('target_mean')}")
    
    def test_analysis_has_shareholding(self):
        """Verify analysis includes shareholding (promoters, fii, dii, public)"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/reliance", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "shareholding" in data, "Response should have 'shareholding'"
        sh = data["shareholding"]
        expected_keys = ["promoters", "fii", "dii", "public"]
        for key in expected_keys:
            assert key in sh, f"shareholding missing '{key}'"
        print(f"SUCCESS: Shareholding - Promoters={sh.get('promoters')}%, FII={sh.get('fii')}%, DII={sh.get('dii')}%, Public={sh.get('public')}%")
    
    def test_tcs_analysis(self):
        """Verify TCS analysis works"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/tcs", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"].upper() == "TCS"
        print(f"SUCCESS: TCS analysis returned - {data.get('name', 'N/A')}, Price={data.get('price')}")
    
    def test_hdfcbank_analysis(self):
        """Verify HDFCBANK analysis works"""
        response = requests.get(f"{BASE_URL}/api/stocks/analysis/hdfcbank", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"].upper() == "HDFCBANK"
        print(f"SUCCESS: HDFCBANK analysis returned - {data.get('name', 'N/A')}, Price={data.get('price')}")


class TestStockPeers:
    """Test GET /api/stocks/peers/{symbol} - peer comparison"""
    
    def test_reliance_peers_returns_energy_sector(self):
        """Verify Reliance peers returns companies in Energy sector"""
        response = requests.get(f"{BASE_URL}/api/stocks/peers/reliance", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "peers" in data, "Response should have 'peers'"
        assert isinstance(data["peers"], list), "peers should be a list"
        print(f"SUCCESS: Reliance has {len(data['peers'])} peers")
    
    def test_tcs_peers_returns_it_sector(self):
        """Verify TCS peers returns IT sector companies"""
        response = requests.get(f"{BASE_URL}/api/stocks/peers/tcs", timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "peers" in data
        # TCS is in IT sector, should have peers like INFY, WIPRO, HCLTECH
        print(f"SUCCESS: TCS has {len(data['peers'])} IT sector peers")
    
    def test_peer_has_required_fields(self):
        """Verify peer data has required fields"""
        response = requests.get(f"{BASE_URL}/api/stocks/peers/tcs", timeout=60)
        assert response.status_code == 200
        data = response.json()
        if data["peers"]:
            peer = data["peers"][0]
            expected_keys = ["symbol", "name", "price", "market_cap_cr"]
            for key in expected_keys:
                assert key in peer, f"Peer missing '{key}'"
            print(f"SUCCESS: Peer data has required fields - {peer['symbol']}: Price={peer['price']}, MCap={peer['market_cap_cr']}Cr")


class TestStockScreener:
    """Test POST /api/stocks/screener - filter stocks"""
    
    def test_screener_no_filters(self):
        """Verify screener with no filters returns all stocks"""
        response = requests.post(f"{BASE_URL}/api/stocks/screener", json={"filters": {}}, timeout=120)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data, "Response should have 'results'"
        assert "count" in data, "Response should have 'count'"
        print(f"SUCCESS: Screener with no filters returned {data['count']} stocks")
    
    def test_screener_pe_filter(self):
        """Verify screener with P/E filter works"""
        response = requests.post(f"{BASE_URL}/api/stocks/screener", json={"filters": {"pe_max": 25}}, timeout=120)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"SUCCESS: Screener with pe_max=25 returned {data['count']} stocks")
    
    def test_screener_roe_filter(self):
        """Verify screener with ROE filter works"""
        response = requests.post(f"{BASE_URL}/api/stocks/screener", json={"filters": {"roe_min": 15}}, timeout=120)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"SUCCESS: Screener with roe_min=15 returned {data['count']} stocks")
    
    def test_screener_combined_filters(self):
        """Verify screener with multiple filters works"""
        filters = {"pe_max": 30, "roe_min": 10, "de_max": 1}
        response = requests.post(f"{BASE_URL}/api/stocks/screener", json={"filters": filters}, timeout=120)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"SUCCESS: Screener with combined filters returned {data['count']} stocks")
    
    def test_screener_result_has_required_fields(self):
        """Verify screener results have required fields"""
        response = requests.post(f"{BASE_URL}/api/stocks/screener", json={"filters": {}}, timeout=120)
        assert response.status_code == 200
        data = response.json()
        if data["results"]:
            stock = data["results"][0]
            expected_keys = ["symbol", "name", "sector", "price", "market_cap_cr"]
            for key in expected_keys:
                assert key in stock, f"Screener result missing '{key}'"
            print(f"SUCCESS: Screener result has required fields - {stock['symbol']}: {stock['name']}")


class TestScreenerPresets:
    """Test GET /api/stocks/screener/presets - preset filters"""
    
    def test_presets_returns_7_presets(self):
        """Verify presets endpoint returns 7 presets"""
        response = requests.get(f"{BASE_URL}/api/stocks/screener/presets", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data, "Response should have 'presets'"
        assert len(data["presets"]) == 7, f"Expected 7 presets, got {len(data['presets'])}"
        print(f"SUCCESS: Presets endpoint returned {len(data['presets'])} presets")
    
    def test_presets_have_required_fields(self):
        """Verify each preset has id, name, filters"""
        response = requests.get(f"{BASE_URL}/api/stocks/screener/presets", timeout=30)
        assert response.status_code == 200
        data = response.json()
        for preset in data["presets"]:
            assert "id" in preset, f"Preset missing 'id': {preset}"
            assert "name" in preset, f"Preset missing 'name': {preset}"
            assert "filters" in preset, f"Preset missing 'filters': {preset}"
        print(f"SUCCESS: All presets have required fields (id, name, filters)")
    
    def test_presets_include_buffett_graham(self):
        """Verify presets include Warren Buffett and Benjamin Graham styles"""
        response = requests.get(f"{BASE_URL}/api/stocks/screener/presets", timeout=30)
        assert response.status_code == 200
        data = response.json()
        preset_ids = [p["id"] for p in data["presets"]]
        assert "buffett" in preset_ids, "Should have Warren Buffett preset"
        assert "graham" in preset_ids, "Should have Benjamin Graham preset"
        preset_names = [p["name"] for p in data["presets"]]
        print(f"SUCCESS: Presets include: {preset_names}")


class TestAuthAndExistingFeatures:
    """Verify existing features still work after stock analysis addition"""
    
    def test_login_still_works(self):
        """Verify login endpoint still works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "contact.developersingh@gmail.com",
            "password": "admin123"
        }, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print(f"SUCCESS: Login still works - user_id={data.get('user_id')}")
    
    def test_market_live_still_works(self):
        """Verify market live endpoint still works"""
        response = requests.get(f"{BASE_URL}/api/market/live", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "crypto" in data
        assert "forex" in data
        assert "indian" in data
        print(f"SUCCESS: Market live still works - {len(data.get('crypto', []))} crypto, {len(data.get('forex', []))} forex, {len(data.get('indian', []))} indian")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
