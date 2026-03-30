"""
Test Suite for SignalBeast Pro - Iteration 8
Tests: Signal Strategies, Multi-TF Signals, Trade Journal, Admin Panel, Pricing Page
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "test@test.com"
TEST_USER_PASSWORD = "test123"
TEST_USER_NAME = "TestUser"

ADMIN_EMAIL = "contact.developersingh@gmail.com"
ADMIN_PASSWORD = "admin123"

class TestSetup:
    """Setup: Register test users"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    def test_register_test_user(self, session):
        """Register test user (may already exist)"""
        response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        # 200 or 400 (already exists) are both acceptable
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"Test user registration: {response.status_code}")
    
    def test_register_admin_user(self, session):
        """Register admin user (may already exist)"""
        response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "name": "Admin User"
        })
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"Admin user registration: {response.status_code}")


class TestSignalStrategies:
    """Test GET /api/signals/strategies returns 10 strategies"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Login failed - cannot test strategies")
        return response.json().get("token")
    
    def test_get_strategies_returns_10(self, auth_token):
        """GET /api/signals/strategies should return 10 strategies"""
        response = requests.get(
            f"{BASE_URL}/api/signals/strategies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "strategies" in data, "Response should have 'strategies' key"
        strategies = data["strategies"]
        assert len(strategies) >= 10, f"Expected at least 10 strategies, got {len(strategies)}"
        
        # Verify strategy structure
        for s in strategies:
            assert "id" in s, "Strategy should have 'id'"
            assert "name" in s, "Strategy should have 'name'"
            assert "description" in s, "Strategy should have 'description'"
        
        # Verify expected strategy IDs
        strategy_ids = [s["id"] for s in strategies]
        expected_ids = ["auto", "ema_crossover", "rsi_divergence", "smc", "vwap", 
                       "macd", "bollinger", "ichimoku", "fibonacci", "price_action"]
        for eid in expected_ids:
            assert eid in strategy_ids, f"Missing strategy: {eid}"
        
        print(f"Strategies returned: {strategy_ids}")


class TestMultiTimeframeSignals:
    """Test POST /api/signals/generate with multi-timeframe params"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Login failed - cannot test signals")
        return response.json().get("token")
    
    def test_generate_multi_tf_signal(self, auth_token):
        """POST /api/signals/generate with multi-TF params returns enhanced signal"""
        payload = {
            "asset_id": "bitcoin",
            "asset_name": "Bitcoin (BTC)",
            "asset_type": "crypto",
            "timeframe": "1H",
            "timeframes": ["15m", "1H", "4H"],
            "strategy": "ema_crossover",
            "profit_target": 5.0
        }
        response = requests.post(
            f"{BASE_URL}/api/signals/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=payload,
            timeout=60  # AI generation can take time
        )
        
        # Check for budget exceeded (acceptable)
        if response.status_code == 429:
            pytest.skip("AI budget exceeded - skipping signal generation test")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify enhanced signal fields
        assert "signal_id" in data, "Signal should have signal_id"
        assert "direction" in data, "Signal should have direction"
        assert data["direction"] in ["BUY", "SELL"], f"Invalid direction: {data['direction']}"
        
        # Multi-TF specific fields
        assert "timeframes_analyzed" in data, "Signal should have timeframes_analyzed"
        assert isinstance(data["timeframes_analyzed"], list), "timeframes_analyzed should be a list"
        
        assert "holding_duration" in data, "Signal should have holding_duration"
        assert "confluence_score" in data, "Signal should have confluence_score"
        assert "take_profit_3" in data or "take_profit_3" in str(data), "Signal should have take_profit_3"
        assert "strategy_used" in data, "Signal should have strategy_used"
        assert "higher_tf_bias" in data, "Signal should have higher_tf_bias"
        assert "invalidation" in data, "Signal should have invalidation"
        
        print(f"Signal generated: {data.get('direction')} with confluence {data.get('confluence_score')}")
        print(f"Timeframes analyzed: {data.get('timeframes_analyzed')}")
        print(f"Holding duration: {data.get('holding_duration')}")


class TestTradeJournal:
    """Test Trade Journal CRUD operations"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Login failed - cannot test journal")
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_journal_empty_or_list(self, headers):
        """GET /api/journal returns trades list"""
        response = requests.get(f"{BASE_URL}/api/journal", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "trades" in data, "Response should have 'trades' key"
        assert isinstance(data["trades"], list), "trades should be a list"
        print(f"Journal has {len(data['trades'])} trades")
    
    def test_create_journal_entry(self, headers):
        """POST /api/journal creates a trade journal entry"""
        payload = {
            "asset_id": "bitcoin",
            "asset_name": "Bitcoin (BTC)",
            "asset_type": "crypto",
            "direction": "BUY",
            "entry_price": 68000.0,
            "exit_price": 69500.0,
            "quantity": 0.1,
            "timeframe": "4H",
            "strategy": "EMA Crossover",
            "entry_reasoning": "Golden cross on 4H chart",
            "pre_trade_confidence": 8,
            "emotion_tag": "confident",
            "quality_rating": 4,
            "status": "closed"
        }
        response = requests.post(f"{BASE_URL}/api/journal", headers=headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "trade_id" in data, "Response should have trade_id"
        assert data["asset_name"] == "Bitcoin (BTC)", "Asset name mismatch"
        assert data["direction"] == "BUY", "Direction mismatch"
        assert data["entry_price"] == 68000.0, "Entry price mismatch"
        assert data["emotion_tag"] == "confident", "Emotion tag mismatch"
        assert "pnl" in data, "Response should have pnl"
        
        # Store trade_id for update/delete tests
        TestTradeJournal.created_trade_id = data["trade_id"]
        print(f"Created trade: {data['trade_id']} with P&L: {data.get('pnl')}")
    
    def test_update_journal_entry(self, headers):
        """PUT /api/journal/{trade_id} updates a trade"""
        trade_id = getattr(TestTradeJournal, 'created_trade_id', None)
        if not trade_id:
            pytest.skip("No trade created to update")
        
        payload = {
            "exit_price": 70000.0,
            "post_reflection": "Good trade, followed the plan",
            "lesson_learned": "Patience pays off",
            "quality_rating": 5,
            "status": "closed"
        }
        response = requests.put(f"{BASE_URL}/api/journal/{trade_id}", headers=headers, json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["exit_price"] == 70000.0, "Exit price not updated"
        assert data["post_reflection"] == "Good trade, followed the plan", "Reflection not updated"
        assert data["quality_rating"] == 5, "Quality rating not updated"
        print(f"Updated trade: {trade_id}")
    
    def test_get_journal_stats(self, headers):
        """GET /api/journal/stats returns win_rate, total_pnl, emotion_breakdown"""
        response = requests.get(f"{BASE_URL}/api/journal/stats", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "win_rate" in data, "Stats should have win_rate"
        assert "total_pnl" in data, "Stats should have total_pnl"
        assert "emotion_breakdown" in data, "Stats should have emotion_breakdown"
        assert "total_trades" in data, "Stats should have total_trades"
        assert "wins" in data, "Stats should have wins"
        assert "losses" in data, "Stats should have losses"
        
        print(f"Journal stats: {data['total_trades']} trades, {data['win_rate']}% win rate, ${data['total_pnl']} P&L")
    
    def test_delete_journal_entry(self, headers):
        """DELETE /api/journal/{trade_id} deletes a trade"""
        trade_id = getattr(TestTradeJournal, 'created_trade_id', None)
        if not trade_id:
            pytest.skip("No trade created to delete")
        
        response = requests.delete(f"{BASE_URL}/api/journal/{trade_id}", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "message" in data, "Response should have message"
        print(f"Deleted trade: {trade_id}")
        
        # Verify deletion
        response = requests.get(f"{BASE_URL}/api/journal", headers=headers)
        trades = response.json().get("trades", [])
        trade_ids = [t["trade_id"] for t in trades]
        assert trade_id not in trade_ids, "Trade should be deleted"


class TestAdminPanel:
    """Test Admin Panel endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def user_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("User login failed")
        return response.json().get("token")
    
    def test_admin_stats(self, admin_token):
        """GET /api/admin/stats returns platform stats (requires admin auth)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "total_users" in data, "Stats should have total_users"
        assert "total_signals" in data, "Stats should have total_signals"
        assert "total_trades" in data, "Stats should have total_trades"
        assert "active_alerts" in data, "Stats should have active_alerts"
        assert "system_health" in data, "Stats should have system_health"
        
        print(f"Admin stats: {data['total_users']} users, {data['total_signals']} signals")
    
    def test_admin_users(self, admin_token):
        """GET /api/admin/users returns user list (requires admin auth)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "users" in data, "Response should have users"
        assert isinstance(data["users"], list), "users should be a list"
        assert len(data["users"]) > 0, "Should have at least 1 user"
        
        # Verify user structure (no password exposed)
        for user in data["users"]:
            assert "user_id" in user, "User should have user_id"
            assert "email" in user, "User should have email"
            assert "password" not in user, "Password should not be exposed"
        
        print(f"Admin users: {len(data['users'])} users")
    
    def test_admin_system(self, admin_token):
        """GET /api/admin/system returns data feed status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/system",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "data_feeds" in data, "Response should have data_feeds"
        assert "ticker" in data, "Response should have ticker"
        assert "market_status" in data, "Response should have market_status"
        
        # Verify data feeds
        feeds = data["data_feeds"]
        assert "oanda" in feeds, "Should have oanda feed"
        assert "kraken" in feeds, "Should have kraken feed"
        
        print(f"System: OANDA {feeds['oanda']['status']}, Kraken {feeds['kraken']['status']}")
    
    def test_non_admin_gets_403(self, user_token):
        """Non-admin user gets 403 on admin endpoints"""
        endpoints = ["/api/admin/stats", "/api/admin/users", "/api/admin/system"]
        
        for endpoint in endpoints:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert response.status_code == 403, f"Expected 403 for {endpoint}, got {response.status_code}"
        
        print("Non-admin correctly denied access to all admin endpoints")


class TestHealthAndBasics:
    """Basic health checks"""
    
    def test_api_health(self):
        """API is accessible"""
        response = requests.get(f"{BASE_URL}/api/market/live", timeout=10)
        assert response.status_code == 200, f"API not accessible: {response.status_code}"
        print("API health check passed")
    
    def test_market_live_data(self):
        """Market live data returns crypto, forex, indian"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        data = response.json()
        
        assert "crypto" in data, "Should have crypto"
        assert "forex" in data, "Should have forex"
        assert "indian" in data, "Should have indian"
        
        print(f"Live data: {len(data['crypto'])} crypto, {len(data['forex'])} forex, {len(data['indian'])} indian")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
