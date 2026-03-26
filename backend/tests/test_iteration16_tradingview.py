"""
Iteration 16 - TradingView API Integration Tests
Tests for TradingView Node.js service and signal generation with TV data
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://titan-ai-staging.preview.emergentagent.com').rstrip('/')
TV_SERVICE_URL = "http://127.0.0.1:8099"

# Test credentials
TEST_EMAIL = "contact.developersingh@gmail.com"
TEST_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API calls"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestTradingViewServiceHealth:
    """TradingView Node.js service health tests"""
    
    def test_tv_service_health(self, api_client):
        """Test TradingView service health endpoint"""
        response = api_client.get(f"{TV_SERVICE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("service") == "tv-service"
        assert data.get("symbols") > 0
        print(f"TV Service healthy: {data.get('symbols')} symbols mapped")


class TestTradingViewTechnicalAnalysis:
    """TradingView Technical Analysis endpoint tests"""
    
    def test_tv_ta_bitcoin_crypto(self, api_client):
        """Test TradingView TA for Bitcoin (crypto)"""
        response = api_client.get(f"{TV_SERVICE_URL}/ta/bitcoin")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "symbol" in data
        assert data["symbol"] == "BINANCE:BTCUSDT"
        assert data["asset_id"] == "bitcoin"
        assert "timeframes" in data
        assert "summary" in data
        
        # Verify timeframes have required fields
        timeframes = data["timeframes"]
        assert len(timeframes) > 0
        for tf_name, tf_data in timeframes.items():
            assert "oscillators" in tf_data
            assert "moving_averages" in tf_data
            assert "overall" in tf_data
            assert "value" in tf_data["overall"]
            assert "label" in tf_data["overall"]
        
        # Verify summary
        summary = data["summary"]
        assert "bias" in summary
        assert summary["bias"] in ["Bullish", "Bearish", "Neutral"]
        assert "bull_timeframes" in summary
        assert "bear_timeframes" in summary
        assert "confluence" in summary
        assert "label" in summary
        print(f"Bitcoin TV Analysis: {summary['label']}")
    
    def test_tv_ta_eurusd_forex(self, api_client):
        """Test TradingView TA for EUR/USD (forex)"""
        response = api_client.get(f"{TV_SERVICE_URL}/ta/eurusd")
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "FX:EURUSD"
        assert data["asset_id"] == "eurusd"
        assert "timeframes" in data
        assert "summary" in data
        
        # Verify key timeframes exist
        timeframes = data["timeframes"]
        key_tfs = ["15m", "1H", "4H", "1D"]
        for tf in key_tfs:
            assert tf in timeframes, f"Missing timeframe: {tf}"
        
        summary = data["summary"]
        assert summary["bias"] in ["Bullish", "Bearish", "Neutral"]
        print(f"EUR/USD TV Analysis: {summary['label']}")
    
    def test_tv_ta_reliance_indian(self, api_client):
        """Test TradingView TA for Reliance (Indian stock)"""
        response = api_client.get(f"{TV_SERVICE_URL}/ta/reliance")
        assert response.status_code == 200
        data = response.json()
        
        assert data["symbol"] == "NSE:RELIANCE"
        assert data["asset_id"] == "reliance"
        assert "timeframes" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert summary["bias"] in ["Bullish", "Bearish", "Neutral"]
        print(f"Reliance TV Analysis: {summary['label']}")
    
    def test_tv_ta_unknown_asset(self, api_client):
        """Test TradingView TA for unknown asset returns error"""
        response = api_client.get(f"{TV_SERVICE_URL}/ta/unknown_asset_xyz")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data
        assert data["error"] == "Unknown asset"
    
    def test_tv_ta_rating_values(self, api_client):
        """Test TradingView rating values are within expected range"""
        response = api_client.get(f"{TV_SERVICE_URL}/ta/ethereum")
        assert response.status_code == 200
        data = response.json()
        
        for tf_name, tf_data in data.get("timeframes", {}).items():
            overall_value = tf_data["overall"]["value"]
            # TradingView ratings are typically between -1 and 1
            assert -2 <= overall_value <= 2, f"Rating out of range: {overall_value}"
            
            # Verify label matches value
            label = tf_data["overall"]["label"]
            if overall_value >= 0.5:
                assert label == "Strong Buy"
            elif overall_value >= 0.1:
                assert label == "Buy"
            elif overall_value > -0.1:
                assert label == "Neutral"
            elif overall_value > -0.5:
                assert label == "Sell"
            else:
                assert label == "Strong Sell"


class TestSignalGenerationWithTradingView:
    """Signal generation tests with TradingView data integration"""
    
    def test_signal_generation_crypto_with_tv(self, authenticated_client):
        """Test signal generation for crypto includes TradingView data"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/signals/generate",
            json={
                "asset_id": "ethereum",
                "asset_name": "Ethereum",
                "asset_type": "crypto",
                "timeframe": "4H",
                "strategy": "auto",
                "trading_mode": "swing",
                "num_tp_levels": 3
            }
        )
        assert response.status_code == 200
        signal = response.json()
        
        # Verify required fields
        assert "signal_id" in signal
        assert "direction" in signal
        assert signal["direction"] in ["BUY", "SELL"]
        assert "entry_price" in signal
        assert "stop_loss" in signal
        assert "take_profit_1" in signal
        
        # Verify TradingView-related fields
        assert "technical_summary" in signal
        assert len(signal["technical_summary"]) > 0
        assert "risk_level" in signal
        assert signal["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
        
        # Verify confluence factors mention TradingView
        assert "confluence_factors" in signal
        
        print(f"Crypto Signal: {signal['direction']} with risk_level={signal['risk_level']}")
        print(f"Technical Summary: {signal['technical_summary']}")
    
    def test_signal_generation_forex_with_tv(self, authenticated_client):
        """Test signal generation for forex includes TradingView data"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/signals/generate",
            json={
                "asset_id": "gbpusd",
                "asset_name": "GBP/USD",
                "asset_type": "forex",
                "timeframe": "1H",
                "strategy": "smc",
                "trading_mode": "day_trading",
                "num_tp_levels": 2
            }
        )
        assert response.status_code == 200
        signal = response.json()
        
        assert "technical_summary" in signal
        assert "risk_level" in signal
        assert signal["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
        
        print(f"Forex Signal: {signal['direction']} with risk_level={signal['risk_level']}")
    
    def test_signal_generation_indian_with_tv(self, authenticated_client):
        """Test signal generation for Indian stock includes TradingView data"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/signals/generate",
            json={
                "asset_id": "tcs",
                "asset_name": "TCS",
                "asset_type": "indian",
                "timeframe": "1D",
                "strategy": "auto",
                "trading_mode": "position",
                "num_tp_levels": 3
            }
        )
        assert response.status_code == 200
        signal = response.json()
        
        assert "technical_summary" in signal
        assert "risk_level" in signal
        
        print(f"Indian Signal: {signal['direction']} with risk_level={signal['risk_level']}")
    
    def test_signal_has_all_required_fields(self, authenticated_client):
        """Test generated signal has all required fields including new TV fields"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/signals/generate",
            json={
                "asset_id": "bitcoin",
                "asset_name": "Bitcoin",
                "asset_type": "crypto",
                "timeframe": "1D",
                "strategy": "auto",
                "trading_mode": "swing",
                "num_tp_levels": 3
            }
        )
        assert response.status_code == 200
        signal = response.json()
        
        # Core signal fields
        required_fields = [
            "signal_id", "user_id", "asset_id", "asset_name", "asset_type",
            "direction", "confidence", "grade", "entry_price",
            "take_profit_1", "stop_loss", "risk_reward",
            "timeframes_analyzed", "primary_timeframe", "strategy_used",
            "holding_duration", "confluence_score", "confluence_factors",
            "analysis", "trade_logic", "trade_reason", "key_levels",
            "market_condition", "higher_tf_bias", "invalidation",
            "trading_mode", "num_tp_levels", "status", "created_at"
        ]
        
        # New TradingView-related fields
        tv_fields = ["technical_summary", "risk_level"]
        
        for field in required_fields + tv_fields:
            assert field in signal, f"Missing field: {field}"
        
        print(f"Signal has all {len(required_fields) + len(tv_fields)} required fields")


class TestExistingFeaturesStillWork:
    """Verify existing features still work after TradingView integration"""
    
    def test_login_works(self, api_client):
        """Test login still works"""
        response = api_client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user_id" in data
    
    def test_market_live_works(self, api_client):
        """Test live market data still works"""
        response = api_client.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        data = response.json()
        assert "crypto" in data
        assert "forex" in data
        assert "indian" in data
        assert len(data["crypto"]) > 0
    
    def test_signals_list_works(self, authenticated_client):
        """Test signals list still works"""
        response = authenticated_client.get(f"{BASE_URL}/api/signals")
        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
    
    def test_trading_modes_works(self, api_client):
        """Test trading modes endpoint still works"""
        response = api_client.get(f"{BASE_URL}/api/signals/trading-modes")
        assert response.status_code == 200
        data = response.json()
        assert "modes" in data
        assert len(data["modes"]) == 4
    
    def test_strategies_works(self, api_client):
        """Test strategies endpoint still works"""
        response = api_client.get(f"{BASE_URL}/api/signals/strategies?market=crypto")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert len(data["strategies"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
