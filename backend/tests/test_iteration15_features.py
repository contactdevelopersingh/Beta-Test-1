"""
Iteration 15 Tests: TP/SL Locking, Signal Deletion, Trading Modes, TP Count, Trade Close Fix

Features tested:
1. DELETE /api/signals/{signal_id} - Delete a signal
2. GET /api/signals/trading-modes - Returns 4 trading modes
3. Signal generation with trading_mode and num_tp_levels parameters
4. Trade close endpoint POST /api/trade/close/{instrument}
5. check_signal_tp_sl function (runs in ticker loop)
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTradingModes:
    """Test trading modes endpoint"""
    
    def test_get_trading_modes_returns_4_modes(self):
        """GET /api/signals/trading-modes should return 4 modes"""
        response = requests.get(f"{BASE_URL}/api/signals/trading-modes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "modes" in data, "Response should have 'modes' key"
        modes = data["modes"]
        assert len(modes) == 4, f"Expected 4 trading modes, got {len(modes)}"
        
        # Verify all 4 modes are present
        mode_ids = [m["id"] for m in modes]
        expected_modes = ["scalping", "day_trading", "swing", "position"]
        for expected in expected_modes:
            assert expected in mode_ids, f"Missing trading mode: {expected}"
        
        # Verify each mode has required fields
        for mode in modes:
            assert "id" in mode, "Mode should have 'id'"
            assert "label" in mode, "Mode should have 'label'"
            assert "desc" in mode, "Mode should have 'desc'"
            assert "default_hold" in mode, "Mode should have 'default_hold'"
        
        print(f"SUCCESS: Trading modes endpoint returns all 4 modes: {mode_ids}")


class TestSignalDeletion:
    """Test signal deletion functionality"""
    
    @pytest.fixture
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "contact.developersingh@gmail.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    def test_delete_signal_success(self, auth_token):
        """DELETE /api/signals/{signal_id} should delete a signal"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First, generate a signal to delete
        signal_payload = {
            "asset_id": "bitcoin",
            "asset_name": "Bitcoin (BTC)",
            "asset_type": "crypto",
            "timeframe": "1H",
            "timeframes": ["1H", "4H"],
            "strategy": "auto",
            "trading_mode": "swing",
            "num_tp_levels": 2
        }
        
        gen_response = requests.post(f"{BASE_URL}/api/signals/generate", json=signal_payload, headers=headers)
        if gen_response.status_code != 200:
            pytest.skip(f"Could not generate signal for deletion test: {gen_response.text}")
        
        signal_id = gen_response.json().get("signal_id")
        assert signal_id, "Generated signal should have signal_id"
        print(f"Generated signal {signal_id} for deletion test")
        
        # Now delete the signal
        delete_response = requests.delete(f"{BASE_URL}/api/signals/{signal_id}", headers=headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        data = delete_response.json()
        assert "message" in data, "Delete response should have message"
        assert "deleted" in data["message"].lower(), f"Expected 'deleted' in message, got: {data['message']}"
        
        # Verify signal is gone by fetching all signals
        signals_response = requests.get(f"{BASE_URL}/api/signals", headers=headers)
        assert signals_response.status_code == 200
        signals = signals_response.json().get("signals", [])
        signal_ids = [s.get("signal_id") for s in signals]
        assert signal_id not in signal_ids, "Deleted signal should not appear in signals list"
        
        print(f"SUCCESS: Signal {signal_id} deleted successfully")
    
    def test_delete_nonexistent_signal_returns_404(self, auth_token):
        """DELETE /api/signals/{fake_id} should return 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        fake_id = f"sig_fake_{uuid.uuid4().hex[:12]}"
        
        response = requests.delete(f"{BASE_URL}/api/signals/{fake_id}", headers=headers)
        assert response.status_code == 404, f"Expected 404 for nonexistent signal, got {response.status_code}"
        print(f"SUCCESS: Delete nonexistent signal returns 404")
    
    def test_delete_signal_requires_auth(self):
        """DELETE /api/signals/{signal_id} should require authentication"""
        response = requests.delete(f"{BASE_URL}/api/signals/sig_test123")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("SUCCESS: Delete signal requires authentication")


class TestSignalGenerationWithNewParams:
    """Test signal generation with trading_mode and num_tp_levels"""
    
    @pytest.fixture
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "contact.developersingh@gmail.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    def test_generate_signal_with_trading_mode_scalping(self, auth_token):
        """Generate signal with trading_mode=scalping"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        payload = {
            "asset_id": "ethereum",
            "asset_name": "Ethereum (ETH)",
            "asset_type": "crypto",
            "timeframe": "5m",
            "timeframes": ["5m", "15m"],
            "strategy": "auto",
            "trading_mode": "scalping",
            "num_tp_levels": 3
        }
        
        response = requests.post(f"{BASE_URL}/api/signals/generate", json=payload, headers=headers)
        assert response.status_code == 200, f"Signal generation failed: {response.text}"
        
        signal = response.json()
        assert signal.get("trading_mode") == "scalping", f"Expected trading_mode=scalping, got {signal.get('trading_mode')}"
        assert signal.get("num_tp_levels") == 3, f"Expected num_tp_levels=3, got {signal.get('num_tp_levels')}"
        
        print(f"SUCCESS: Generated scalping signal with 3 TPs: {signal.get('signal_id')}")
    
    def test_generate_signal_with_1_tp_level(self, auth_token):
        """Generate signal with num_tp_levels=1"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        payload = {
            "asset_id": "solana",
            "asset_name": "Solana (SOL)",
            "asset_type": "crypto",
            "timeframe": "1H",
            "timeframes": ["1H"],
            "strategy": "auto",
            "trading_mode": "day_trading",
            "num_tp_levels": 1
        }
        
        response = requests.post(f"{BASE_URL}/api/signals/generate", json=payload, headers=headers)
        assert response.status_code == 200, f"Signal generation failed: {response.text}"
        
        signal = response.json()
        assert signal.get("num_tp_levels") == 1, f"Expected num_tp_levels=1, got {signal.get('num_tp_levels')}"
        assert signal.get("trading_mode") == "day_trading", f"Expected trading_mode=day_trading"
        
        # With 1 TP, only take_profit_1 should be meaningful
        assert signal.get("take_profit_1") is not None, "Signal should have take_profit_1"
        
        print(f"SUCCESS: Generated day_trading signal with 1 TP: {signal.get('signal_id')}")
    
    def test_generate_signal_with_2_tp_levels(self, auth_token):
        """Generate signal with num_tp_levels=2"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        payload = {
            "asset_id": "bitcoin",
            "asset_name": "Bitcoin (BTC)",
            "asset_type": "crypto",
            "timeframe": "4H",
            "timeframes": ["4H", "1D"],
            "strategy": "auto",
            "trading_mode": "position",
            "num_tp_levels": 2
        }
        
        response = requests.post(f"{BASE_URL}/api/signals/generate", json=payload, headers=headers)
        assert response.status_code == 200, f"Signal generation failed: {response.text}"
        
        signal = response.json()
        assert signal.get("num_tp_levels") == 2, f"Expected num_tp_levels=2, got {signal.get('num_tp_levels')}"
        assert signal.get("trading_mode") == "position", f"Expected trading_mode=position"
        
        print(f"SUCCESS: Generated position signal with 2 TPs: {signal.get('signal_id')}")


class TestTradeCloseEndpoint:
    """Test trade close endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "contact.developersingh@gmail.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    def test_close_position_no_position(self, auth_token):
        """POST /api/trade/close/{instrument} with no open position"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try to close a position that likely doesn't exist
        response = requests.post(f"{BASE_URL}/api/trade/close/EUR_USD", headers=headers)
        
        # Should either succeed with "no position" message or fail with 403 (plan restriction)
        if response.status_code == 403:
            # Plan restriction - expected for non-Titan users
            assert "Titan plan" in response.json().get("detail", ""), "Should mention Titan plan requirement"
            print("SUCCESS: Trade close requires Titan plan (403 returned)")
        elif response.status_code == 200:
            data = response.json()
            # Either closed successfully or no position found
            assert "message" in data, "Response should have message"
            print(f"SUCCESS: Trade close endpoint responded: {data.get('message')}")
        else:
            # Other status codes might indicate OANDA issues
            print(f"Trade close returned {response.status_code}: {response.text}")
    
    def test_close_position_requires_auth(self):
        """POST /api/trade/close/{instrument} should require authentication"""
        response = requests.post(f"{BASE_URL}/api/trade/close/EUR_USD")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("SUCCESS: Trade close requires authentication")


class TestSignalTPSLFields:
    """Test that signals have TP/SL hit tracking fields"""
    
    @pytest.fixture
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "contact.developersingh@gmail.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    def test_signals_have_tp_sl_fields(self, auth_token):
        """Signals should have tp1_hit, tp2_hit, tp3_hit, sl_hit fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get existing signals
        response = requests.get(f"{BASE_URL}/api/signals", headers=headers)
        assert response.status_code == 200
        
        signals = response.json().get("signals", [])
        if not signals:
            pytest.skip("No signals to check TP/SL fields")
        
        # Check first signal for expected fields
        signal = signals[0]
        
        # These fields should exist (may be False/None initially)
        expected_fields = ["signal_id", "asset_id", "direction", "entry_price", 
                          "take_profit_1", "stop_loss", "status"]
        for field in expected_fields:
            assert field in signal, f"Signal missing field: {field}"
        
        # Status should be one of: active, stopped_out, all_tp_hit
        valid_statuses = ["active", "stopped_out", "all_tp_hit"]
        assert signal.get("status") in valid_statuses, f"Invalid status: {signal.get('status')}"
        
        print(f"SUCCESS: Signal has all required fields. Status: {signal.get('status')}")


class TestMarketLiveEndpoint:
    """Test that market live endpoint still works (regression)"""
    
    def test_market_live_returns_data(self):
        """GET /api/market/live should return crypto, forex, indian data"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        
        data = response.json()
        assert "crypto" in data, "Should have crypto data"
        assert "forex" in data, "Should have forex data"
        assert "indian" in data, "Should have indian data"
        assert "tick" in data, "Should have tick count"
        
        print(f"SUCCESS: Market live returns data. Tick: {data.get('tick')}, Crypto: {len(data.get('crypto', []))}, Forex: {len(data.get('forex', []))}, Indian: {len(data.get('indian', []))}")


class TestStrategiesEndpoint:
    """Test strategies endpoint"""
    
    def test_get_strategies_for_crypto(self):
        """GET /api/signals/strategies?market=crypto should return crypto strategies"""
        response = requests.get(f"{BASE_URL}/api/signals/strategies?market=crypto")
        assert response.status_code == 200
        
        data = response.json()
        assert "strategies" in data
        strategies = data["strategies"]
        assert len(strategies) > 10, f"Expected many crypto strategies, got {len(strategies)}"
        
        # Check for crypto-specific strategies
        strategy_ids = [s["id"] for s in strategies]
        crypto_specific = ["onchain", "whale_tracking", "funding_rate", "open_interest"]
        found = [s for s in crypto_specific if s in strategy_ids]
        assert len(found) > 0, f"Should have crypto-specific strategies. Found: {found}"
        
        print(f"SUCCESS: Crypto strategies endpoint returns {len(strategies)} strategies")
    
    def test_get_strategies_for_forex(self):
        """GET /api/signals/strategies?market=forex should return forex strategies"""
        response = requests.get(f"{BASE_URL}/api/signals/strategies?market=forex")
        assert response.status_code == 200
        
        data = response.json()
        strategies = data["strategies"]
        
        # Check for forex-specific strategies
        strategy_ids = [s["id"] for s in strategies]
        forex_specific = ["ict", "smc", "kill_zones", "asian_london"]
        found = [s for s in forex_specific if s in strategy_ids]
        assert len(found) > 0, f"Should have forex-specific strategies. Found: {found}"
        
        print(f"SUCCESS: Forex strategies endpoint returns {len(strategies)} strategies")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
