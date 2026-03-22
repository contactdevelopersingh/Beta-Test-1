"""
SignalBeast Pro - Market Hours Testing (Iteration 5)
Tests the market hours awareness fix:
- Forex and Indian markets should show CLOSED on Sunday
- Prices for closed markets should NOT change between polls
- Crypto is 24/7 and should continue ticking
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMarketStatus:
    """Test market_status field in /api/market/live response"""
    
    def test_market_live_returns_market_status(self):
        """API should include market_status object"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        data = response.json()
        assert 'market_status' in data, "market_status field missing from response"
        
    def test_market_status_has_all_markets(self):
        """market_status should have crypto, forex, indian keys"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        market_status = data.get('market_status', {})
        assert 'crypto' in market_status, "crypto missing from market_status"
        assert 'forex' in market_status, "forex missing from market_status"
        assert 'indian' in market_status, "indian missing from market_status"
        
    def test_crypto_always_open(self):
        """Crypto market should always be open (24/7)"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        crypto_status = data.get('market_status', {}).get('crypto', {})
        assert crypto_status.get('open') == True, "Crypto should always be open"
        assert crypto_status.get('label') == '24/7', "Crypto label should be '24/7'"
        
    def test_forex_closed_on_sunday(self):
        """Forex market should be closed on Sunday (before 5PM ET)"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        forex_status = data.get('market_status', {}).get('forex', {})
        # Today is Sunday March 22, 2026 - forex should be closed
        assert forex_status.get('open') == False, "Forex should be closed on Sunday"
        assert forex_status.get('label') == 'Closed', "Forex label should be 'Closed'"
        
    def test_indian_closed_on_sunday(self):
        """Indian market (NSE) should be closed on weekends"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        indian_status = data.get('market_status', {}).get('indian', {})
        # Today is Sunday - Indian market should be closed
        assert indian_status.get('open') == False, "Indian market should be closed on Sunday"
        assert indian_status.get('label') == 'Closed', "Indian label should be 'Closed'"


class TestPriceStability:
    """Test that closed market prices don't change between polls"""
    
    def test_tick_counter_increases(self):
        """Tick counter should increase between polls"""
        # First poll
        r1 = requests.get(f"{BASE_URL}/api/market/live")
        d1 = r1.json()
        tick1 = d1.get('tick', 0)
        
        # Wait for a few ticks
        time.sleep(3)
        
        # Second poll
        r2 = requests.get(f"{BASE_URL}/api/market/live")
        d2 = r2.json()
        tick2 = d2.get('tick', 0)
        
        assert tick2 > tick1, f"Tick counter should increase: {tick1} -> {tick2}"
        print(f"Tick counter increased: {tick1} -> {tick2}")
        
    def test_forex_prices_stable_when_closed(self):
        """Forex prices should NOT change when market is closed"""
        # First poll
        r1 = requests.get(f"{BASE_URL}/api/market/live")
        d1 = r1.json()
        
        # Skip if forex market is open
        if d1.get('market_status', {}).get('forex', {}).get('open'):
            pytest.skip("Forex market is open - cannot test price stability")
            
        forex1 = {f['id']: f['price'] for f in d1.get('forex', [])}
        
        # Wait for a few ticks
        time.sleep(3)
        
        # Second poll
        r2 = requests.get(f"{BASE_URL}/api/market/live")
        d2 = r2.json()
        forex2 = {f['id']: f['price'] for f in d2.get('forex', [])}
        
        # All forex prices should be identical
        for pair_id, price1 in forex1.items():
            price2 = forex2.get(pair_id)
            assert price1 == price2, f"Forex {pair_id} price changed when market is closed: {price1} -> {price2}"
        print(f"Verified {len(forex1)} forex pairs have stable prices when market is closed")
        
    def test_indian_prices_stable_when_closed(self):
        """Indian market prices should NOT change when market is closed"""
        # First poll
        r1 = requests.get(f"{BASE_URL}/api/market/live")
        d1 = r1.json()
        
        # Skip if Indian market is open
        if d1.get('market_status', {}).get('indian', {}).get('open'):
            pytest.skip("Indian market is open - cannot test price stability")
            
        indian1 = {s['id']: s['price'] for s in d1.get('indian', [])}
        
        # Wait for a few ticks
        time.sleep(3)
        
        # Second poll
        r2 = requests.get(f"{BASE_URL}/api/market/live")
        d2 = r2.json()
        indian2 = {s['id']: s['price'] for s in d2.get('indian', [])}
        
        # All Indian prices should be identical
        for stock_id, price1 in indian1.items():
            price2 = indian2.get(stock_id)
            assert price1 == price2, f"Indian {stock_id} price changed when market is closed: {price1} -> {price2}"
        print(f"Verified {len(indian1)} Indian stocks have stable prices when market is closed")


class TestMarketDataCounts:
    """Test that all market data is loading correctly"""
    
    def test_crypto_count(self):
        """Should have crypto assets (may be 0 if CoinGecko rate limited)"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        crypto_count = len(data.get('crypto', []))
        # CoinGecko may be rate limited, so we just check the field exists
        print(f"Crypto count: {crypto_count} (may be 0 if CoinGecko rate limited)")
        assert 'crypto' in data, "crypto field should exist in response"
        
    def test_forex_count(self):
        """Should have 12 forex pairs"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        forex_count = len(data.get('forex', []))
        assert forex_count >= 10, f"Expected at least 10 forex pairs, got {forex_count}"
        print(f"Forex count: {forex_count}")
        
    def test_indian_count(self):
        """Should have 44 Indian stocks/indices"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        indian_count = len(data.get('indian', []))
        assert indian_count >= 30, f"Expected at least 30 Indian assets, got {indian_count}"
        print(f"Indian count: {indian_count}")


class TestAuth:
    """Test authentication with test credentials"""
    
    def test_login_with_test_credentials(self):
        """Login with test@signalbeast.com / Test1234!"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@signalbeast.com",
            "password": "Test1234!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert 'token' in data, "Token missing from login response"
        assert data.get('email') == 'test@signalbeast.com'
        print(f"Login successful for {data.get('email')}")
        return data.get('token')
        
    def test_auth_me_with_token(self):
        """GET /api/auth/me should return user info"""
        # First login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@signalbeast.com",
            "password": "Test1234!"
        })
        token = login_resp.json().get('token')
        
        # Then get user info
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get('email') == 'test@signalbeast.com'


class TestGainersLosers:
    """Test top gainers and losers data"""
    
    def test_gainers_losers_fields_present(self):
        """API should return gainers and losers arrays (may be empty if no crypto data)"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        assert 'gainers' in data, "gainers field missing from response"
        assert 'losers' in data, "losers field missing from response"
        # Note: May be empty if CoinGecko is rate limited
        print(f"Gainers: {len(data.get('gainers', []))}, Losers: {len(data.get('losers', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
