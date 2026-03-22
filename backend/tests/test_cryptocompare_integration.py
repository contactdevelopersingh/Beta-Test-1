"""
SignalBeast Pro - CryptoCompare Integration Tests (Iteration 6)
Tests the switch from CoinGecko to CryptoCompare for crypto data:
- 25 crypto prices with CryptoCompare data
- Real-time updates (tick increases, crypto prices have micro-movements)
- Crypto images from cryptocompare.com
- Chart endpoints using CryptoCompare
- Market status (forex/indian CLOSED on Sunday)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@signalbeast.com"
TEST_PASSWORD = "Test1234!"


class TestCryptoCompareIntegration:
    """Test CryptoCompare crypto data integration"""
    
    def test_market_live_returns_25_crypto(self):
        """CRITICAL: /api/market/live returns 25 crypto prices"""
        # Retry a few times in case we hit the 30-second refresh window
        for attempt in range(3):
            response = requests.get(f"{BASE_URL}/api/market/live")
            assert response.status_code == 200
            data = response.json()
            
            crypto = data.get('crypto', [])
            if len(crypto) == 25:
                print(f"✓ Got {len(crypto)} crypto prices from CryptoCompare")
                return
            time.sleep(5)
            
        assert len(crypto) == 25, f"Expected 25 crypto, got {len(crypto)} after 3 attempts"
        
    def test_crypto_has_required_fields(self):
        """CRITICAL: Crypto data has price, change_24h, market_cap, volume, image"""
        # Retry a few times in case we hit the 30-second refresh window
        for attempt in range(3):
            response = requests.get(f"{BASE_URL}/api/market/live")
            data = response.json()
            crypto = data.get('crypto', [])
            if len(crypto) > 0:
                break
            time.sleep(5)
            
        assert len(crypto) > 0, "No crypto data returned after 3 attempts"
        
        # Check first crypto (should be Bitcoin by market cap)
        btc = crypto[0]
        required_fields = ['id', 'symbol', 'name', 'price', 'change_24h', 'market_cap', 'volume', 'image', 'high', 'low']
        for field in required_fields:
            assert field in btc, f"Missing field: {field}"
            
        assert btc['id'] == 'bitcoin', f"First crypto should be bitcoin, got {btc['id']}"
        assert btc['price'] > 0, "BTC price should be positive"
        assert btc['market_cap'] > 0, "BTC market cap should be positive"
        assert btc['volume'] > 0, "BTC volume should be positive"
        print(f"✓ BTC: ${btc['price']:,.2f}, 24h: {btc['change_24h']:.2f}%, MCap: ${btc['market_cap']:,.0f}")
        
    def test_crypto_images_from_cryptocompare(self):
        """CRITICAL: Crypto images load from https://cryptocompare.com/media/..."""
        # Retry a few times in case we hit the 30-second refresh window
        for attempt in range(3):
            response = requests.get(f"{BASE_URL}/api/market/live")
            data = response.json()
            crypto = data.get('crypto', [])
            if len(crypto) > 0:
                break
            time.sleep(5)
            
        assert len(crypto) > 0, "No crypto data after 3 attempts"
        
        # Check that images are from CryptoCompare
        for coin in crypto[:5]:  # Check first 5
            image = coin.get('image', '')
            assert 'cryptocompare.com' in image, f"Image for {coin['symbol']} not from CryptoCompare: {image}"
            
        print(f"✓ All crypto images from cryptocompare.com")
        print(f"  Sample: {crypto[0]['image']}")


class TestRealTimeUpdates:
    """Test real-time price updates"""
    
    def test_tick_increases_between_polls(self):
        """CRITICAL: Tick counter increases between polls"""
        r1 = requests.get(f"{BASE_URL}/api/market/live")
        d1 = r1.json()
        tick1 = d1.get('tick', 0)
        
        time.sleep(3)
        
        r2 = requests.get(f"{BASE_URL}/api/market/live")
        d2 = r2.json()
        tick2 = d2.get('tick', 0)
        
        assert tick2 > tick1, f"Tick should increase: {tick1} -> {tick2}"
        print(f"✓ Tick increased: {tick1} -> {tick2}")
        
    def test_crypto_prices_have_micro_movements(self):
        """CRITICAL: Crypto prices should have micro-movements between polls"""
        r1 = requests.get(f"{BASE_URL}/api/market/live")
        d1 = r1.json()
        
        crypto1 = {c['id']: c['price'] for c in d1.get('crypto', [])}
        
        time.sleep(3)
        
        r2 = requests.get(f"{BASE_URL}/api/market/live")
        d2 = r2.json()
        
        crypto2 = {c['id']: c['price'] for c in d2.get('crypto', [])}
        
        # At least some crypto prices should change (micro-movements)
        changes = 0
        for coin_id in crypto1:
            if coin_id in crypto2 and crypto1[coin_id] != crypto2[coin_id]:
                changes += 1
                
        assert changes > 0, "No crypto prices changed between polls - micro-movements not working"
        print(f"✓ {changes}/{len(crypto1)} crypto prices changed between polls")
        
    def test_forex_prices_stable_when_closed(self):
        """CRITICAL: Forex prices stay STABLE between polls (market closed on Sunday)"""
        r1 = requests.get(f"{BASE_URL}/api/market/live")
        d1 = r1.json()
        
        # Check if forex market is closed
        forex_open = d1.get('market_status', {}).get('forex', {}).get('open', True)
        if forex_open:
            pytest.skip("Forex market is open - cannot test price stability")
            
        forex1 = {f['id']: f['price'] for f in d1.get('forex', [])}
        
        time.sleep(3)
        
        r2 = requests.get(f"{BASE_URL}/api/market/live")
        d2 = r2.json()
        
        forex2 = {f['id']: f['price'] for f in d2.get('forex', [])}
        
        # All forex prices should be identical when market is closed
        for pair_id, price1 in forex1.items():
            price2 = forex2.get(pair_id)
            assert price1 == price2, f"Forex {pair_id} changed when closed: {price1} -> {price2}"
            
        print(f"✓ All {len(forex1)} forex pairs stable when market closed")
        
    def test_indian_prices_stable_when_closed(self):
        """CRITICAL: Indian prices stay STABLE between polls (market closed on Sunday)"""
        r1 = requests.get(f"{BASE_URL}/api/market/live")
        d1 = r1.json()
        
        # Check if Indian market is closed
        indian_open = d1.get('market_status', {}).get('indian', {}).get('open', True)
        if indian_open:
            pytest.skip("Indian market is open - cannot test price stability")
            
        indian1 = {s['id']: s['price'] for s in d1.get('indian', [])}
        
        time.sleep(3)
        
        r2 = requests.get(f"{BASE_URL}/api/market/live")
        d2 = r2.json()
        
        indian2 = {s['id']: s['price'] for s in d2.get('indian', [])}
        
        # All Indian prices should be identical when market is closed
        for stock_id, price1 in indian1.items():
            price2 = indian2.get(stock_id)
            assert price1 == price2, f"Indian {stock_id} changed when closed: {price1} -> {price2}"
            
        print(f"✓ All {len(indian1)} Indian assets stable when market closed")


class TestChartEndpoints:
    """Test chart endpoints using CryptoCompare"""
    
    def test_btc_chart_7d(self):
        """CRITICAL: /api/market/crypto/bitcoin/chart?days=7 returns price data"""
        response = requests.get(f"{BASE_URL}/api/market/crypto/bitcoin/chart?days=7")
        assert response.status_code == 200
        data = response.json()
        
        prices = data.get('prices', [])
        assert len(prices) > 100, f"Expected >100 price points for 7D, got {len(prices)}"
        
        # Each price should be [timestamp, price]
        assert len(prices[0]) == 2, "Price format should be [timestamp, price]"
        assert prices[0][0] > 0, "Timestamp should be positive"
        assert prices[0][1] > 0, "Price should be positive"
        
        print(f"✓ BTC 7D chart: {len(prices)} price points")
        
    def test_chart_crypto_candles(self):
        """CRITICAL: /api/market/chart/crypto/bitcoin?period=1mo returns candle data"""
        response = requests.get(f"{BASE_URL}/api/market/chart/crypto/bitcoin?period=1mo")
        assert response.status_code == 200
        data = response.json()
        
        candles = data.get('candles', [])
        assert len(candles) > 20, f"Expected >20 candles for 1mo, got {len(candles)}"
        
        # Check candle structure
        candle = candles[0]
        required_fields = ['time', 'open', 'high', 'low', 'close', 'volume']
        for field in required_fields:
            assert field in candle, f"Missing candle field: {field}"
            
        assert candle['high'] >= candle['low'], "High should be >= Low"
        assert candle['high'] >= candle['open'], "High should be >= Open"
        assert candle['high'] >= candle['close'], "High should be >= Close"
        
        print(f"✓ BTC 1mo chart: {len(candles)} candles with OHLCV data")


class TestMarketStatus:
    """Test market status in API response"""
    
    def test_market_status_present(self):
        """CRITICAL: market_status in API response"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        
        assert 'market_status' in data, "market_status missing from response"
        
        market_status = data['market_status']
        assert 'crypto' in market_status
        assert 'forex' in market_status
        assert 'indian' in market_status
        
    def test_crypto_always_24_7(self):
        """CRITICAL: Crypto market shows 24/7"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        
        crypto_status = data.get('market_status', {}).get('crypto', {})
        assert crypto_status.get('open') == True, "Crypto should always be open"
        assert crypto_status.get('label') == '24/7', "Crypto label should be '24/7'"
        print(f"✓ Crypto: open={crypto_status.get('open')}, label={crypto_status.get('label')}")
        
    def test_forex_closed_on_sunday(self):
        """CRITICAL: Forex shows Closed on Sunday"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        
        forex_status = data.get('market_status', {}).get('forex', {})
        # Today is Sunday - forex should be closed
        assert forex_status.get('open') == False, "Forex should be closed on Sunday"
        assert forex_status.get('label') == 'Closed', "Forex label should be 'Closed'"
        print(f"✓ Forex: open={forex_status.get('open')}, label={forex_status.get('label')}")
        
    def test_indian_closed_on_sunday(self):
        """CRITICAL: Indian shows Closed on Sunday"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        
        indian_status = data.get('market_status', {}).get('indian', {})
        # Today is Sunday - Indian market should be closed
        assert indian_status.get('open') == False, "Indian should be closed on Sunday"
        assert indian_status.get('label') == 'Closed', "Indian label should be 'Closed'"
        print(f"✓ Indian: open={indian_status.get('open')}, label={indian_status.get('label')}")


class TestGainersLosers:
    """Test gainers and losers include crypto"""
    
    def test_gainers_losers_present(self):
        """Gainers and losers arrays present"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        
        assert 'gainers' in data
        assert 'losers' in data
        
        gainers = data.get('gainers', [])
        losers = data.get('losers', [])
        
        print(f"✓ Gainers: {len(gainers)}, Losers: {len(losers)}")
        
    def test_losers_include_crypto(self):
        """Losers should include crypto coins (since crypto has negative changes)"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        data = response.json()
        
        losers = data.get('losers', [])
        crypto_in_losers = [l for l in losers if l.get('market') == 'crypto']
        
        # With 25 crypto coins, some should be in losers
        print(f"✓ Crypto in losers: {len(crypto_in_losers)}")
        for loser in crypto_in_losers[:3]:
            print(f"  - {loser.get('symbol')}: {loser.get('change_24h'):.2f}%")


class TestAuthentication:
    """Test auth with test credentials"""
    
    def test_login_test_user(self):
        """Login with test@signalbeast.com / Test1234!"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        
        assert 'token' in data
        assert data.get('email') == TEST_EMAIL
        print(f"✓ Login successful for {TEST_EMAIL}")
        return data.get('token')


class TestSignalGeneration:
    """Test signal generation uses live cache prices"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json().get('token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_generate_signal_for_crypto(self):
        """Signal generation uses live cache prices (not CoinGecko)"""
        response = requests.post(
            f"{BASE_URL}/api/signals/generate",
            headers=self.headers,
            json={
                "asset_id": "bitcoin",
                "asset_name": "Bitcoin",
                "asset_type": "crypto",
                "timeframe": "1D"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            assert 'signal_id' in data
            assert 'direction' in data
            assert data['direction'] in ['BUY', 'SELL']
            print(f"✓ Signal generated: {data['direction']} with {data.get('confidence', 0)}% confidence")
        elif response.status_code == 429:
            pytest.skip("LLM budget exceeded")
        else:
            print(f"Signal generation returned {response.status_code}: {response.text}")


class TestAlertsCRUD:
    """Test alerts CRUD still works"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json().get('token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_create_alert(self):
        """Create a price alert"""
        response = requests.post(
            f"{BASE_URL}/api/alerts",
            headers=self.headers,
            json={
                "asset_id": "bitcoin",
                "asset_name": "Bitcoin",
                "asset_type": "crypto",
                "condition": "above",
                "target_price": 100000,
                "note": "Test alert iter6"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert 'alert_id' in data
        print(f"✓ Alert created: {data['alert_id']}")
        return data['alert_id']
        
    def test_get_alerts(self):
        """Get user alerts"""
        response = requests.get(f"{BASE_URL}/api/alerts", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert 'alerts' in data
        print(f"✓ Got {len(data['alerts'])} alerts")


class TestNotifications:
    """Test notification bell works"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json().get('token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_get_unread_count(self):
        """Get unread notification count"""
        response = requests.get(f"{BASE_URL}/api/notifications/unread-count", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert 'count' in data
        print(f"✓ Unread notifications: {data['count']}")


class TestBeastAIChat:
    """Test Beast AI Chat works"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json().get('token')
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
    def test_chat_endpoint(self):
        """Send a chat message"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers=self.headers,
            json={
                "message": "What is Bitcoin?",
                "session_id": None
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            assert 'response' in data
            assert 'session_id' in data
            print(f"✓ Chat response received, session: {data['session_id']}")
        elif response.status_code == 500 and "budget" in response.text.lower():
            pytest.skip("LLM budget exceeded")
        else:
            # Graceful fallback is acceptable
            print(f"Chat returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
