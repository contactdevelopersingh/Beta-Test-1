"""
Iteration 14 Tests: Bug Fixes for Login/Signup and Market Data Speed
Tests:
1. Login with valid credentials (contact.developersingh@gmail.com / admin123)
2. Login with valid credentials (infinityanirudra@gmail.com / admin456)
3. Register new user and immediately login with those credentials
4. 10 rapid logins in sequence don't get rate-limited (30/min limit)
5. Wrong password returns 401 not 429
6. Market data /api/market/live returns all 3 markets (crypto, forex, indian)
7. Market tick count increments rapidly (every ~1 second)
8. Security headers still present
9. Admin endpoints still accessible for both admins
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestLoginWithValidCredentials:
    """Test that valid users can login successfully"""
    
    def test_admin1_login_success(self):
        """Admin 1 (contact.developersingh@gmail.com / admin123) should login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "contact.developersingh@gmail.com",
            "password": "admin123"
        })
        print(f"Admin 1 login response: {response.status_code}")
        assert response.status_code == 200, f"Admin 1 login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert data["email"] == "contact.developersingh@gmail.com"
        print(f"SUCCESS: Admin 1 login works - {data['email']}")
    
    def test_admin2_login_success(self):
        """Admin 2 (infinityanirudra@gmail.com / admin456) should login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "infinityanirudra@gmail.com",
            "password": "admin456"
        })
        print(f"Admin 2 login response: {response.status_code}")
        assert response.status_code == 200, f"Admin 2 login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert data["email"] == "infinityanirudra@gmail.com"
        print(f"SUCCESS: Admin 2 login works - {data['email']}")


class TestRegisterAndLogin:
    """Test that new users can register and immediately login"""
    
    def test_register_new_user_and_login(self):
        """Register a new user and immediately login with those credentials"""
        # Generate unique email
        unique_id = uuid.uuid4().hex[:8]
        test_email = f"test_newuser_{unique_id}@example.com"
        test_password = "testpass123"
        test_name = "Test New User"
        
        # Register
        reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": test_password,
            "name": test_name
        })
        print(f"Register response: {reg_response.status_code}")
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        reg_data = reg_response.json()
        assert "token" in reg_data, "No token in registration response"
        assert reg_data["email"] == test_email, f"Email mismatch: expected {test_email}, got {reg_data.get('email')}"
        print(f"Registration SUCCESS: {test_email}")
        
        # Immediately login with the same credentials
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        print(f"Login response after registration: {login_response.status_code}")
        assert login_response.status_code == 200, f"Login after registration failed: {login_response.text}"
        login_data = login_response.json()
        assert "token" in login_data, "No token in login response"
        assert login_data["email"] == test_email, f"Email mismatch on login"
        print(f"SUCCESS: New user can register and immediately login - {test_email}")


class TestRateLimitingRelaxed:
    """Test that rate limiting is relaxed to 30/min"""
    
    def test_10_rapid_logins_not_rate_limited(self):
        """10 rapid logins in sequence should NOT get rate-limited (30/min limit)"""
        successful_logins = 0
        rate_limited = False
        
        for i in range(10):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "contact.developersingh@gmail.com",
                "password": "admin123"
            })
            print(f"Login attempt {i+1}: {response.status_code}")
            
            if response.status_code == 200:
                successful_logins += 1
            elif response.status_code == 429:
                rate_limited = True
                print(f"RATE LIMITED on attempt {i+1}")
                break
            else:
                print(f"Unexpected status {response.status_code}: {response.text}")
        
        assert not rate_limited, f"Got rate limited after {successful_logins} logins - rate limit should be 30/min"
        assert successful_logins == 10, f"Only {successful_logins}/10 logins succeeded"
        print(f"SUCCESS: All 10 rapid logins succeeded without rate limiting")
    
    def test_wrong_password_returns_401_not_429(self):
        """Wrong password should return 401 (Invalid credentials) not 429 (rate limited)"""
        # Use a unique email to avoid brute-force lockout from previous tests
        unique_email = f"wrongpw_test_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": unique_email,
            "password": "wrongpassword"
        })
        print(f"Wrong password response: {response.status_code}")
        assert response.status_code == 401, f"Expected 401 for wrong password, got {response.status_code}: {response.text}"
        print(f"SUCCESS: Wrong password correctly returns 401 (not 429)")


class TestBruteForceProtectionRelaxed:
    """Test that brute-force threshold is now 15 attempts"""
    
    def test_brute_force_threshold_is_15(self):
        """Should be able to make 14 failed attempts before getting locked out"""
        unique_email = f"bruteforce_test_{uuid.uuid4().hex[:8]}@example.com"
        
        # Make 14 failed login attempts - should all return 401
        for i in range(14):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": unique_email,
                "password": "wrongpassword"
            })
            print(f"Failed attempt {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                pytest.fail(f"Got 429 on attempt {i+1} - brute force threshold should be 15")
            
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print(f"SUCCESS: 14 failed attempts all returned 401 (brute-force threshold is 15)")


class TestMarketDataLive:
    """Test that market data endpoint returns all 3 markets"""
    
    def test_market_live_returns_all_markets(self):
        """Market data /api/market/live should return crypto, forex, and indian markets"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        print(f"Market live response: {response.status_code}")
        assert response.status_code == 200, f"Market live failed: {response.text}"
        
        data = response.json()
        
        # Check crypto
        assert "crypto" in data, "Missing 'crypto' in response"
        crypto_count = len(data.get("crypto", []))
        print(f"Crypto assets: {crypto_count}")
        
        # Check forex
        assert "forex" in data, "Missing 'forex' in response"
        forex_count = len(data.get("forex", []))
        print(f"Forex pairs: {forex_count}")
        
        # Check indian
        assert "indian" in data, "Missing 'indian' in response"
        indian_count = len(data.get("indian", []))
        print(f"Indian assets: {indian_count}")
        
        # Check tick count
        assert "tick" in data, "Missing 'tick' in response"
        print(f"Tick count: {data.get('tick')}")
        
        # Check initialized
        assert "initialized" in data, "Missing 'initialized' in response"
        print(f"Initialized: {data.get('initialized')}")
        
        # Check market_status
        assert "market_status" in data, "Missing 'market_status' in response"
        market_status = data.get("market_status", {})
        print(f"Market status: {market_status}")
        
        print(f"SUCCESS: Market live returns all 3 markets - crypto({crypto_count}), forex({forex_count}), indian({indian_count})")
    
    def test_market_tick_increments_rapidly(self):
        """Market tick count should increment rapidly (every ~1 second)"""
        # Get first tick
        response1 = requests.get(f"{BASE_URL}/api/market/live")
        assert response1.status_code == 200
        tick1 = response1.json().get("tick", 0)
        print(f"First tick: {tick1}")
        
        # Wait 3 seconds
        time.sleep(3)
        
        # Get second tick
        response2 = requests.get(f"{BASE_URL}/api/market/live")
        assert response2.status_code == 200
        tick2 = response2.json().get("tick", 0)
        print(f"Second tick after 3s: {tick2}")
        
        # Tick should have incremented by at least 2 (since we waited 3 seconds and tick updates every ~1 second)
        tick_diff = tick2 - tick1
        print(f"Tick difference: {tick_diff}")
        
        assert tick_diff >= 2, f"Tick only incremented by {tick_diff} in 3 seconds - expected at least 2"
        print(f"SUCCESS: Market tick increments rapidly - {tick_diff} ticks in 3 seconds")


class TestSecurityHeadersStillPresent:
    """Test that security headers are still present after bug fixes"""
    
    def test_security_headers_present(self):
        """All security headers should still be present"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        headers = response.headers
        
        # Check X-Content-Type-Options
        assert "X-Content-Type-Options" in headers, "Missing X-Content-Type-Options header"
        assert headers["X-Content-Type-Options"] == "nosniff"
        print(f"X-Content-Type-Options: {headers['X-Content-Type-Options']}")
        
        # Check X-Frame-Options
        assert "X-Frame-Options" in headers, "Missing X-Frame-Options header"
        assert headers["X-Frame-Options"] == "DENY"
        print(f"X-Frame-Options: {headers['X-Frame-Options']}")
        
        # Check X-XSS-Protection
        assert "X-XSS-Protection" in headers, "Missing X-XSS-Protection header"
        print(f"X-XSS-Protection: {headers['X-XSS-Protection']}")
        
        # Check Referrer-Policy
        assert "Referrer-Policy" in headers, "Missing Referrer-Policy header"
        print(f"Referrer-Policy: {headers['Referrer-Policy']}")
        
        print("SUCCESS: All security headers still present")


class TestAdminEndpointsStillAccessible:
    """Test that admin endpoints are still accessible for both admins"""
    
    def test_admin1_can_access_admin_stats(self):
        """Admin 1 should still be able to access /api/admin/stats"""
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "contact.developersingh@gmail.com",
            "password": "admin123"
        })
        assert login_resp.status_code == 200, f"Admin 1 login failed: {login_resp.text}"
        token = login_resp.json()["token"]
        
        # Access admin stats
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Admin 1 stats response: {response.status_code}")
        assert response.status_code == 200, f"Admin 1 stats access failed: {response.text}"
        print("SUCCESS: Admin 1 can access admin stats")
    
    def test_admin2_can_access_admin_stats(self):
        """Admin 2 should still be able to access /api/admin/stats"""
        # Login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "infinityanirudra@gmail.com",
            "password": "admin456"
        })
        assert login_resp.status_code == 200, f"Admin 2 login failed: {login_resp.text}"
        token = login_resp.json()["token"]
        
        # Access admin stats
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Admin 2 stats response: {response.status_code}")
        assert response.status_code == 200, f"Admin 2 stats access failed: {response.text}"
        print("SUCCESS: Admin 2 can access admin stats")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
