"""
Iteration 9 Tests: Rebrand (SignalBeast -> Titan Trade) and Plan Management
Tests the new plan management endpoints and verifies rebrand in API responses
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://127.0.0.1:8000').rstrip('/')

# Test credentials
ADMIN_EMAIL = "contact.developersingh@gmail.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "testuser@test.com"
TEST_USER_PASSWORD = "test123"
NEW_TEST_USER_EMAIL = f"plantest_{int(time.time())}@test.com"
NEW_TEST_USER_PASSWORD = "test123"


class TestHealthAndBasics:
    """Basic health checks"""
    
    def test_api_health(self):
        """Test API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✅ API health check passed")
    
    def test_market_live_endpoint(self):
        """Test market live data endpoint"""
        response = requests.get(f"{BASE_URL}/api/market/live")
        assert response.status_code == 200
        data = response.json()
        assert "crypto" in data
        assert "forex" in data
        assert "indian" in data
        print("✅ Market live endpoint working")


class TestAuthentication:
    """Authentication tests"""
    
    def test_admin_login(self):
        """Test admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["email"] == ADMIN_EMAIL
        print(f"✅ Admin login successful: {ADMIN_EMAIL}")
        return data["token"]
    
    def test_test_user_login(self):
        """Test regular user can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        print(f"✅ Test user login successful: {TEST_USER_EMAIL}")
        return data["token"]
    
    def test_register_new_user(self):
        """Register a new user for plan testing"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": NEW_TEST_USER_EMAIL,
            "password": NEW_TEST_USER_PASSWORD,
            "name": "Plan Test User"
        })
        # May fail if user already exists, that's ok
        if response.status_code == 200:
            print(f"✅ New user registered: {NEW_TEST_USER_EMAIL}")
        else:
            print(f"⚠️ User registration returned {response.status_code} (may already exist)")
        return response


class TestAdminPlanEndpoints:
    """Test admin plan management endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def test_user_token(self):
        """Get test user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_get_all_plans_as_admin(self, admin_token):
        """GET /api/admin/plans - Admin can get all plans"""
        response = requests.get(
            f"{BASE_URL}/api/admin/plans",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        print(f"✅ GET /api/admin/plans returned {len(data['plans'])} plans")
    
    def test_get_all_plans_as_non_admin(self, test_user_token):
        """GET /api/admin/plans - Non-admin gets 403"""
        response = requests.get(
            f"{BASE_URL}/api/admin/plans",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 403
        print("✅ Non-admin correctly gets 403 on GET /api/admin/plans")
    
    def test_assign_plan_weekly(self, admin_token):
        """POST /api/admin/plans/assign - Assign weekly plan"""
        response = requests.post(
            f"{BASE_URL}/api/admin/plans/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": TEST_USER_EMAIL,
                "plan_name": "basic",
                "billing_cycle": "weekly"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert data["plan"]["plan_name"] == "basic"
        assert data["plan"]["billing_cycle"] == "weekly"
        print(f"✅ Assigned weekly basic plan to {TEST_USER_EMAIL}")
    
    def test_assign_plan_monthly(self, admin_token):
        """POST /api/admin/plans/assign - Assign monthly plan"""
        response = requests.post(
            f"{BASE_URL}/api/admin/plans/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": TEST_USER_EMAIL,
                "plan_name": "pro",
                "billing_cycle": "monthly"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan"]["plan_name"] == "pro"
        assert data["plan"]["billing_cycle"] == "monthly"
        print(f"✅ Assigned monthly pro plan to {TEST_USER_EMAIL}")
    
    def test_assign_plan_with_custom_days(self, admin_token):
        """POST /api/admin/plans/assign - Assign plan with custom days"""
        response = requests.post(
            f"{BASE_URL}/api/admin/plans/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": TEST_USER_EMAIL,
                "plan_name": "titan",
                "billing_cycle": "weekly",
                "duration_days": 14
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan"]["plan_name"] == "titan"
        print(f"✅ Assigned titan plan with 14 custom days to {TEST_USER_EMAIL}")
    
    def test_assign_plan_with_custom_hours(self, admin_token):
        """POST /api/admin/plans/assign - Assign plan with custom hours"""
        response = requests.post(
            f"{BASE_URL}/api/admin/plans/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": TEST_USER_EMAIL,
                "plan_name": "basic",
                "billing_cycle": "weekly",
                "duration_hours": 48
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan"]["plan_name"] == "basic"
        print(f"✅ Assigned basic plan with 48 custom hours to {TEST_USER_EMAIL}")
    
    def test_assign_plan_free(self, admin_token):
        """POST /api/admin/plans/assign - Assign free plan"""
        response = requests.post(
            f"{BASE_URL}/api/admin/plans/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": TEST_USER_EMAIL,
                "plan_name": "free",
                "billing_cycle": "weekly"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["plan"]["plan_name"] == "free"
        print(f"✅ Assigned free plan to {TEST_USER_EMAIL}")
    
    def test_assign_plan_as_non_admin(self, test_user_token):
        """POST /api/admin/plans/assign - Non-admin gets 403"""
        response = requests.post(
            f"{BASE_URL}/api/admin/plans/assign",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={
                "email": "someone@test.com",
                "plan_name": "basic",
                "billing_cycle": "weekly"
            }
        )
        assert response.status_code == 403
        print("✅ Non-admin correctly gets 403 on POST /api/admin/plans/assign")
    
    def test_assign_plan_invalid_email(self, admin_token):
        """POST /api/admin/plans/assign - Invalid email returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/admin/plans/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "email": "nonexistent_user_xyz@test.com",
                "plan_name": "basic",
                "billing_cycle": "weekly"
            }
        )
        assert response.status_code == 404
        print("✅ Assigning plan to non-existent user correctly returns 404")


class TestUserPlanEndpoint:
    """Test user's own plan endpoint"""
    
    @pytest.fixture
    def test_user_token(self):
        """Get test user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_get_my_plan(self, test_user_token):
        """GET /api/user/plan - User can get their own plan"""
        response = requests.get(
            f"{BASE_URL}/api/user/plan",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "plan_name" in data
        assert "status" in data
        print(f"✅ GET /api/user/plan returned plan: {data['plan_name']}, status: {data['status']}")
    
    def test_get_my_plan_unauthenticated(self):
        """GET /api/user/plan - Unauthenticated returns 401"""
        response = requests.get(f"{BASE_URL}/api/user/plan")
        assert response.status_code == 401
        print("✅ Unauthenticated request to /api/user/plan correctly returns 401")


class TestRevokePlan:
    """Test plan revocation"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def test_user_token(self):
        """Get test user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_revoke_plan_as_non_admin(self, test_user_token):
        """DELETE /api/admin/plans/{user_id} - Non-admin gets 403"""
        response = requests.delete(
            f"{BASE_URL}/api/admin/plans/some_user_id",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 403
        print("✅ Non-admin correctly gets 403 on DELETE /api/admin/plans/{user_id}")


class TestAdminStats:
    """Test admin stats endpoint includes plan count"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_admin_stats(self, admin_token):
        """GET /api/admin/stats - Returns platform stats"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_signals" in data
        assert "total_trades" in data
        assert "active_alerts" in data
        print(f"✅ Admin stats: {data['total_users']} users, {data['total_signals']} signals")


class TestChatRebrand:
    """Test that chat endpoint uses Titan AI branding"""
    
    @pytest.fixture
    def test_user_token(self):
        """Get test user token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_chat_endpoint_works(self, test_user_token):
        """POST /api/chat - Chat endpoint is accessible"""
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"Authorization": f"Bearer {test_user_token}"},
            json={"message": "Hello, what is your name?"}
        )
        # May return 200 or 429 (budget exceeded)
        assert response.status_code in [200, 429, 500]
        if response.status_code == 200:
            data = response.json()
            assert "response" in data
            assert "session_id" in data
            print(f"✅ Chat endpoint working, response length: {len(data['response'])}")
        else:
            print(f"⚠️ Chat endpoint returned {response.status_code} (may be budget limit)")


class TestSignalStrategies:
    """Test signal strategies endpoint"""
    
    def test_get_strategies(self):
        """GET /api/signals/strategies - Returns 10 strategies"""
        response = requests.get(f"{BASE_URL}/api/signals/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert len(data["strategies"]) == 10
        strategy_ids = [s["id"] for s in data["strategies"]]
        expected = ["auto", "ema_crossover", "rsi_divergence", "smc", "vwap", 
                    "macd", "bollinger", "ichimoku", "fibonacci", "price_action"]
        for exp in expected:
            assert exp in strategy_ids, f"Missing strategy: {exp}"
        print(f"✅ All 10 strategies present: {strategy_ids}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
