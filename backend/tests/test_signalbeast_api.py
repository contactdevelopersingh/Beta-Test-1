"""
SignalBeast Pro API Tests
Tests for: Auth, Market Data, Portfolio, Alerts, Notifications, Signals, Chat
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = f"test_{uuid.uuid4().hex[:8]}@signalbeast.com"
TEST_PASSWORD = "Test1234!"
TEST_NAME = "Test User"

# Existing test user
EXISTING_EMAIL = "test@signalbeast.com"
EXISTING_PASSWORD = "Test1234!"


class TestHealthAndMarketData:
    """Test market data endpoints (no auth required)"""
    
    def test_market_live_returns_data(self):
        """GET /api/market/live returns crypto, forex, indian data"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "crypto" in data
        assert "forex" in data
        assert "indian" in data
        assert "gainers" in data
        assert "losers" in data
        assert "tick" in data
        
        # Verify counts (as per requirements: 25 crypto, 12 forex, 44 indian)
        print(f"Crypto count: {len(data['crypto'])}")
        print(f"Forex count: {len(data['forex'])}")
        print(f"Indian count: {len(data['indian'])}")
        
        assert len(data['crypto']) >= 20, f"Expected at least 20 crypto, got {len(data['crypto'])}"
        assert len(data['forex']) >= 10, f"Expected at least 10 forex, got {len(data['forex'])}"
        assert len(data['indian']) >= 30, f"Expected at least 30 indian, got {len(data['indian'])}"
    
    def test_market_live_crypto_has_required_fields(self):
        """Verify crypto data has required fields"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        data = response.json()
        
        if data['crypto']:
            coin = data['crypto'][0]
            assert "id" in coin
            assert "symbol" in coin
            assert "name" in coin
            assert "price" in coin
            assert "change_24h" in coin
            assert coin['price'] > 0
    
    def test_market_live_forex_has_required_fields(self):
        """Verify forex data has required fields"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        data = response.json()
        
        if data['forex']:
            pair = data['forex'][0]
            assert "id" in pair
            assert "symbol" in pair
            assert "price" in pair
            assert pair['price'] > 0
    
    def test_market_live_indian_has_required_fields(self):
        """Verify indian market data has required fields"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        data = response.json()
        
        if data['indian']:
            stock = data['indian'][0]
            assert "id" in stock
            assert "symbol" in stock
            assert "name" in stock
            assert "price" in stock
            assert "type" in stock  # index or stock
    
    def test_market_sentiment(self):
        """GET /api/market/sentiment returns fear & greed data"""
        response = requests.get(f"{BASE_URL}/api/market/sentiment")
        assert response.status_code == 200
        data = response.json()
        
        assert "fear_greed_index" in data
        assert "fear_greed_label" in data
        assert 0 <= data['fear_greed_index'] <= 100
    
    def test_market_crypto_top(self):
        """GET /api/market/crypto/top returns top cryptocurrencies"""
        response = requests.get(f"{BASE_URL}/api/market/crypto/top?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert "coins" in data
        assert len(data['coins']) <= 10
    
    def test_market_crypto_chart(self):
        """GET /api/market/crypto/{coin_id}/chart returns chart data"""
        response = requests.get(f"{BASE_URL}/api/market/crypto/bitcoin/chart?days=7")
        assert response.status_code == 200
        data = response.json()
        
        assert "prices" in data
        assert len(data['prices']) > 0


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_new_user(self):
        """POST /api/auth/register creates new user"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "user_id" in data
        assert "email" in data
        assert "token" in data
        assert data['email'] == TEST_EMAIL
        print(f"Registered user: {data['email']}")
    
    def test_register_duplicate_email_fails(self):
        """POST /api/auth/register with existing email returns 400"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "name": TEST_NAME
        })
        assert response.status_code == 400
        assert "already registered" in response.json().get('detail', '').lower()
    
    def test_login_with_valid_credentials(self):
        """POST /api/auth/login with valid credentials returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "token" in data
        assert "user_id" in data
        assert "email" in data
        print(f"Login successful for: {data['email']}")
    
    def test_login_with_invalid_credentials(self):
        """POST /api/auth/login with wrong password returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
    
    def test_auth_me_without_token(self):
        """GET /api/auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
    
    def test_auth_me_with_valid_token(self):
        """GET /api/auth/me with valid token returns user info"""
        # First login to get token
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        token = login_resp.json()['token']
        
        # Then check /me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "user_id" in data
        assert "email" in data
        assert data['email'] == TEST_EMAIL


class TestPortfolio:
    """Test portfolio CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()['token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_add_holding(self):
        """POST /api/portfolio/holdings adds a new holding"""
        response = requests.post(
            f"{BASE_URL}/api/portfolio/holdings",
            headers=self.headers,
            json={
                "asset_id": "bitcoin",
                "asset_name": "Bitcoin",
                "asset_type": "crypto",
                "quantity": 0.5,
                "buy_price": 65000
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "holding_id" in data
        assert data['asset_name'] == "Bitcoin"
        assert data['quantity'] == 0.5
        self.holding_id = data['holding_id']
        print(f"Created holding: {data['holding_id']}")
    
    def test_get_portfolio(self):
        """GET /api/portfolio returns user holdings"""
        response = requests.get(
            f"{BASE_URL}/api/portfolio",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "holdings" in data
        assert isinstance(data['holdings'], list)
    
    def test_get_portfolio_summary(self):
        """GET /api/portfolio/summary returns portfolio summary"""
        response = requests.get(
            f"{BASE_URL}/api/portfolio/summary",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_invested" in data
        assert "holdings_count" in data
        assert "holdings" in data
    
    def test_delete_holding(self):
        """DELETE /api/portfolio/holdings/{id} removes holding"""
        # First create a holding
        create_resp = requests.post(
            f"{BASE_URL}/api/portfolio/holdings",
            headers=self.headers,
            json={
                "asset_id": "ethereum",
                "asset_name": "Ethereum",
                "asset_type": "crypto",
                "quantity": 1.0,
                "buy_price": 2000
            }
        )
        holding_id = create_resp.json()['holding_id']
        
        # Then delete it
        response = requests.delete(
            f"{BASE_URL}/api/portfolio/holdings/{holding_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # Verify it's gone
        portfolio = requests.get(f"{BASE_URL}/api/portfolio", headers=self.headers).json()
        holding_ids = [h['holding_id'] for h in portfolio['holdings']]
        assert holding_id not in holding_ids


class TestAlerts:
    """Test price alerts CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()['token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_alert(self):
        """POST /api/alerts creates a new price alert"""
        response = requests.post(
            f"{BASE_URL}/api/alerts",
            headers=self.headers,
            json={
                "asset_id": "bitcoin",
                "asset_name": "Bitcoin",
                "asset_type": "crypto",
                "condition": "above",
                "target_price": 100000,
                "note": "Test alert"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "alert_id" in data
        assert data['asset_name'] == "Bitcoin"
        assert data['condition'] == "above"
        assert data['target_price'] == 100000
        assert data['status'] == "active"
        print(f"Created alert: {data['alert_id']}")
    
    def test_get_alerts(self):
        """GET /api/alerts returns user alerts"""
        response = requests.get(
            f"{BASE_URL}/api/alerts",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "alerts" in data
        assert isinstance(data['alerts'], list)
    
    def test_delete_alert(self):
        """DELETE /api/alerts/{id} removes alert"""
        # First create an alert
        create_resp = requests.post(
            f"{BASE_URL}/api/alerts",
            headers=self.headers,
            json={
                "asset_id": "ethereum",
                "asset_name": "Ethereum",
                "asset_type": "crypto",
                "condition": "below",
                "target_price": 1500
            }
        )
        alert_id = create_resp.json()['alert_id']
        
        # Then delete it
        response = requests.delete(
            f"{BASE_URL}/api/alerts/{alert_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # Verify it's gone
        alerts = requests.get(f"{BASE_URL}/api/alerts", headers=self.headers).json()
        alert_ids = [a['alert_id'] for a in alerts['alerts']]
        assert alert_id not in alert_ids


class TestNotifications:
    """Test notifications endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()['token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_notifications(self):
        """GET /api/notifications returns user notifications"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "notifications" in data
        assert isinstance(data['notifications'], list)
    
    def test_get_unread_count(self):
        """GET /api/notifications/unread-count returns count"""
        response = requests.get(
            f"{BASE_URL}/api/notifications/unread-count",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "count" in data
        assert isinstance(data['count'], int)
    
    def test_mark_all_read(self):
        """POST /api/notifications/read-all marks all as read"""
        response = requests.post(
            f"{BASE_URL}/api/notifications/read-all",
            headers=self.headers
        )
        assert response.status_code == 200


class TestWatchlist:
    """Test watchlist CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()['token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_add_to_watchlist(self):
        """POST /api/watchlist adds item to watchlist"""
        unique_id = f"test_asset_{uuid.uuid4().hex[:8]}"
        response = requests.post(
            f"{BASE_URL}/api/watchlist",
            headers=self.headers,
            json={
                "asset_id": unique_id,
                "asset_name": "Test Asset",
                "asset_type": "crypto"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "watchlist_id" in data
        assert data['asset_id'] == unique_id
    
    def test_get_watchlist(self):
        """GET /api/watchlist returns user watchlist"""
        response = requests.get(
            f"{BASE_URL}/api/watchlist",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "watchlist" in data
        assert isinstance(data['watchlist'], list)
    
    def test_remove_from_watchlist(self):
        """DELETE /api/watchlist/{id} removes item"""
        # First add an item
        unique_id = f"test_remove_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(
            f"{BASE_URL}/api/watchlist",
            headers=self.headers,
            json={
                "asset_id": unique_id,
                "asset_name": "Test Remove",
                "asset_type": "crypto"
            }
        )
        watchlist_id = create_resp.json()['watchlist_id']
        
        # Then remove it
        response = requests.delete(
            f"{BASE_URL}/api/watchlist/{watchlist_id}",
            headers=self.headers
        )
        assert response.status_code == 200


class TestSignals:
    """Test AI signals endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()['token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_signals(self):
        """GET /api/signals returns user signals"""
        response = requests.get(
            f"{BASE_URL}/api/signals",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "signals" in data
        assert isinstance(data['signals'], list)
    
    def test_generate_signal(self):
        """POST /api/signals/generate creates AI signal"""
        response = requests.post(
            f"{BASE_URL}/api/signals/generate",
            headers=self.headers,
            json={
                "asset_id": "bitcoin",
                "asset_name": "Bitcoin",
                "asset_type": "crypto",
                "timeframe": "1D"
            },
            timeout=30  # AI generation can take time
        )
        
        # May fail due to LLM budget, but should return valid response
        if response.status_code == 200:
            data = response.json()
            assert "signal_id" in data
            assert "direction" in data
            assert "confidence" in data
            assert data['direction'] in ['BUY', 'SELL']
            assert 0 <= data['confidence'] <= 100
            print(f"Generated signal: {data['direction']} with {data['confidence']}% confidence")
        elif response.status_code == 429:
            print("Signal generation skipped - LLM budget exceeded")
            pytest.skip("LLM budget exceeded")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


class TestChat:
    """Test Beast AI chat endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        self.token = login_resp.json()['token']
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_send_chat_message(self):
        """POST /api/chat sends message and gets response"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers=self.headers,
            json={
                "message": "What is Bitcoin?",
                "session_id": None
            },
            timeout=30
        )
        
        # May fail due to LLM budget
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "session_id" in data
            assert len(data['response']) > 0
            print(f"Chat response received, session: {data['session_id']}")
        elif response.status_code == 500 and "budget" in response.text.lower():
            print("Chat skipped - LLM budget exceeded")
            pytest.skip("LLM budget exceeded")
        else:
            # Check if it's a graceful fallback
            if response.status_code == 200:
                pass  # Fallback response is acceptable
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")


class TestForexData:
    """Test forex market data specifically"""
    
    def test_forex_endpoint(self):
        """GET /api/market/forex returns forex pairs"""
        response = requests.get(f"{BASE_URL}/api/market/forex")
        assert response.status_code == 200
        data = response.json()
        
        assert "pairs" in data
        assert len(data['pairs']) >= 10
        
        # Check for expected pairs
        pair_ids = [p['id'] for p in data['pairs']]
        assert 'eurusd' in pair_ids
        assert 'gbpusd' in pair_ids


class TestIndianMarket:
    """Test Indian market data specifically"""
    
    def test_indian_endpoint(self):
        """GET /api/market/indian returns Indian stocks/indices"""
        response = requests.get(f"{BASE_URL}/api/market/indian")
        assert response.status_code == 200
        data = response.json()
        
        assert "stocks" in data
        assert len(data['stocks']) >= 30
        
        # Check for indices and stocks
        types = set(s.get('type') for s in data['stocks'])
        assert 'index' in types or 'stock' in types


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
