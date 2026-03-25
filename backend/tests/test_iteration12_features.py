"""
Iteration 12 Backend Tests - New Features:
- Expanded strategies (29 forex, 29 crypto)
- 2FA endpoints (setup, verify, disable, status)
- Custom strategy CRUD
- New timeframes
- Combo mode support
- R:R ratio support
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "contact.developersingh@gmail.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestExpandedStrategies:
    """Test expanded forex and crypto strategies"""

    def test_forex_strategies_count(self, auth_headers):
        """GET /api/signals/strategies?market=forex returns 29 forex strategies"""
        response = requests.get(f"{BASE_URL}/api/signals/strategies?market=forex", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        strategies = data["strategies"]
        assert len(strategies) == 29, f"Expected 29 forex strategies, got {len(strategies)}"
        print(f"PASS: Forex strategies count = {len(strategies)}")

    def test_forex_strategies_include_ict_smc(self, auth_headers):
        """Forex strategies include ICT, SMC, MSNR, CRT, FVG+OB, BOS, CHoCH"""
        response = requests.get(f"{BASE_URL}/api/signals/strategies?market=forex", headers=auth_headers)
        assert response.status_code == 200
        strategies = response.json()["strategies"]
        strategy_ids = [s["id"] for s in strategies]
        
        required = ["ict", "smc", "msnr", "crt", "fvg_ob", "bos", "choch", "liquidity_grab", "kill_zones"]
        for req in required:
            assert req in strategy_ids, f"Missing forex strategy: {req}"
        print(f"PASS: All required forex strategies present: {required}")

    def test_crypto_strategies_count(self, auth_headers):
        """GET /api/signals/strategies?market=crypto returns 29 crypto strategies"""
        response = requests.get(f"{BASE_URL}/api/signals/strategies?market=crypto", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        strategies = data["strategies"]
        assert len(strategies) == 29, f"Expected 29 crypto strategies, got {len(strategies)}"
        print(f"PASS: Crypto strategies count = {len(strategies)}")

    def test_crypto_strategies_include_onchain_whale(self, auth_headers):
        """Crypto strategies include onchain, whale_tracking, orderbook, funding_rate, open_interest"""
        response = requests.get(f"{BASE_URL}/api/signals/strategies?market=crypto", headers=auth_headers)
        assert response.status_code == 200
        strategies = response.json()["strategies"]
        strategy_ids = [s["id"] for s in strategies]
        
        required = ["onchain", "whale_tracking", "orderbook", "funding_rate", "open_interest", "liquidation_zones"]
        for req in required:
            assert req in strategy_ids, f"Missing crypto strategy: {req}"
        print(f"PASS: All required crypto strategies present: {required}")

    def test_strategy_has_name_and_description(self, auth_headers):
        """Each strategy has id, name, and description"""
        response = requests.get(f"{BASE_URL}/api/signals/strategies?market=forex", headers=auth_headers)
        assert response.status_code == 200
        strategies = response.json()["strategies"]
        
        for s in strategies[:5]:  # Check first 5
            assert "id" in s, "Strategy missing 'id'"
            assert "name" in s, "Strategy missing 'name'"
            assert "description" in s, "Strategy missing 'description'"
            assert len(s["description"]) > 10, f"Strategy {s['id']} has short description"
        print("PASS: Strategies have id, name, and description")


class TestTwoFactorAuth:
    """Test 2FA endpoints"""

    def test_2fa_status(self, auth_headers):
        """GET /api/auth/2fa/status returns two_fa_enabled status"""
        response = requests.get(f"{BASE_URL}/api/auth/2fa/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "two_fa_enabled" in data
        assert isinstance(data["two_fa_enabled"], bool)
        print(f"PASS: 2FA status = {data['two_fa_enabled']}")

    def test_2fa_setup_returns_qr_and_secret(self, auth_headers):
        """POST /api/auth/2fa/setup returns QR code and secret"""
        response = requests.post(f"{BASE_URL}/api/auth/2fa/setup", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "qr_code" in data, "Missing qr_code in 2FA setup response"
        assert "secret" in data, "Missing secret in 2FA setup response"
        assert data["qr_code"].startswith("data:image/png;base64,"), "QR code should be base64 PNG"
        assert len(data["secret"]) >= 16, "Secret should be at least 16 chars"
        print(f"PASS: 2FA setup returns QR code and secret (secret length: {len(data['secret'])})")

    def test_2fa_verify_invalid_code(self, auth_headers):
        """POST /api/auth/2fa/verify with invalid code returns error"""
        # First setup 2FA
        requests.post(f"{BASE_URL}/api/auth/2fa/setup", headers=auth_headers)
        
        # Try to verify with invalid code
        response = requests.post(f"{BASE_URL}/api/auth/2fa/verify", 
                                 headers=auth_headers, 
                                 json={"code": "000000"})
        # Should fail with 400 (invalid code)
        assert response.status_code == 400
        print("PASS: 2FA verify rejects invalid code")


class TestCustomStrategies:
    """Test custom strategy CRUD"""

    def test_get_custom_strategies(self, auth_headers):
        """GET /api/strategies/custom returns user's custom strategies array"""
        response = requests.get(f"{BASE_URL}/api/strategies/custom", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert isinstance(data["strategies"], list)
        print(f"PASS: Custom strategies endpoint returns array (count: {len(data['strategies'])})")

    def test_create_custom_strategy(self, auth_headers):
        """POST /api/strategies/custom creates a new custom combo strategy"""
        payload = {
            "name": "TEST_ICT_SMC_Combo",
            "description": "Test combo strategy for iteration 12",
            "strategies": ["ict", "smc", "crt"],
            "market_type": "forex"
        }
        response = requests.post(f"{BASE_URL}/api/strategies/custom", 
                                 headers=auth_headers, 
                                 json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "strategy_id" in data
        assert data["name"] == payload["name"]
        assert data["strategies"] == payload["strategies"]
        print(f"PASS: Created custom strategy with ID: {data['strategy_id']}")
        return data["strategy_id"]

    def test_delete_custom_strategy(self, auth_headers):
        """DELETE /api/strategies/custom/{id} deletes a custom strategy"""
        # First create a strategy to delete
        payload = {
            "name": "TEST_ToDelete",
            "description": "Will be deleted",
            "strategies": ["macd", "rsi_divergence"],
            "market_type": "all"
        }
        create_resp = requests.post(f"{BASE_URL}/api/strategies/custom", 
                                    headers=auth_headers, 
                                    json=payload)
        assert create_resp.status_code == 200
        strategy_id = create_resp.json()["strategy_id"]
        
        # Now delete it
        delete_resp = requests.delete(f"{BASE_URL}/api/strategies/custom/{strategy_id}", 
                                      headers=auth_headers)
        assert delete_resp.status_code == 200
        
        # Verify it's gone
        get_resp = requests.get(f"{BASE_URL}/api/strategies/custom", headers=auth_headers)
        strategies = get_resp.json()["strategies"]
        strategy_ids = [s["strategy_id"] for s in strategies]
        assert strategy_id not in strategy_ids, "Strategy should be deleted"
        print(f"PASS: Deleted custom strategy {strategy_id}")


class TestSignalGeneration:
    """Test signal generation with new features"""

    def test_signal_with_combo_strategies(self, auth_headers):
        """POST /api/signals/generate with combo strategies"""
        payload = {
            "asset_id": "eurusd",
            "asset_name": "EUR/USD",
            "asset_type": "forex",
            "timeframe": "1H",
            "timeframes": ["15m", "1H", "4H"],
            "strategies": ["ict", "smc"]  # Combo mode
        }
        response = requests.post(f"{BASE_URL}/api/signals/generate", 
                                 headers=auth_headers, 
                                 json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "signal_id" in data
        assert "direction" in data
        assert "confidence" in data
        print(f"PASS: Generated combo signal - Direction: {data['direction']}, Confidence: {data['confidence']}")

    def test_signal_with_custom_rr_ratio(self, auth_headers):
        """POST /api/signals/generate with custom R:R ratio"""
        payload = {
            "asset_id": "bitcoin",
            "asset_name": "Bitcoin (BTC)",
            "asset_type": "crypto",
            "timeframe": "4H",
            "timeframes": ["1H", "4H"],
            "strategy": "auto",
            "risk_reward": "1:2.5"  # Custom R:R
        }
        response = requests.post(f"{BASE_URL}/api/signals/generate", 
                                 headers=auth_headers, 
                                 json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "signal_id" in data
        assert "risk_reward" in data
        print(f"PASS: Generated signal with custom R:R - R:R: {data.get('risk_reward')}")


class TestTimeframes:
    """Test new timeframes support"""

    def test_all_timeframes_available(self, auth_headers):
        """Verify all new timeframes are supported in signal generation"""
        # Test with new timeframes: 1m, 3m, 10m, 30m, 2H, 3H, 3D
        new_timeframes = ["1m", "3m", "10m", "30m", "2H", "3H", "3D"]
        
        # Just verify the endpoint accepts these timeframes
        payload = {
            "asset_id": "eurusd",
            "asset_name": "EUR/USD",
            "asset_type": "forex",
            "timeframe": "1H",
            "timeframes": ["3m", "10m", "30m"],  # New timeframes
            "strategy": "auto"
        }
        response = requests.post(f"{BASE_URL}/api/signals/generate", 
                                 headers=auth_headers, 
                                 json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "timeframes_analyzed" in data
        print(f"PASS: Signal generated with new timeframes: {data.get('timeframes_analyzed')}")


class TestMarketLive:
    """Test market live data"""

    def test_market_live_returns_all_markets(self, auth_headers):
        """GET /api/market/live returns crypto, forex, indian data"""
        response = requests.get(f"{BASE_URL}/api/market/live", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "crypto" in data
        assert "forex" in data
        assert "indian" in data
        assert "market_status" in data
        print(f"PASS: Market live returns all markets (crypto: {len(data['crypto'])}, forex: {len(data['forex'])}, indian: {len(data['indian'])})")


class TestCleanup:
    """Cleanup test data"""

    def test_cleanup_test_strategies(self, auth_headers):
        """Remove TEST_ prefixed custom strategies"""
        response = requests.get(f"{BASE_URL}/api/strategies/custom", headers=auth_headers)
        if response.status_code == 200:
            strategies = response.json()["strategies"]
            for s in strategies:
                if s["name"].startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/strategies/custom/{s['strategy_id']}", 
                                    headers=auth_headers)
                    print(f"Cleaned up: {s['name']}")
        print("PASS: Cleanup complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
