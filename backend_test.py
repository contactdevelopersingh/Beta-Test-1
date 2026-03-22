#!/usr/bin/env python3
"""
SignalBeast Pro Backend API Testing Suite
Tests all endpoints systematically with proper auth handling
"""

import requests
import json
import sys
import time
from datetime import datetime

class SignalBeastAPITester:
    def __init__(self, base_url="https://realtime-signals-9.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        
    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def run_test(self, name, method, endpoint, expected_status, data=None, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
                
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                self.log(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    'test': name,
                    'endpoint': endpoint,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:200]
                })
                return False, {}
                
        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            self.failed_tests.append({
                'test': name,
                'endpoint': endpoint,
                'error': str(e)
            })
            return False, {}
    
    def test_auth_flow(self):
        """Test authentication endpoints"""
        self.log("\n🔐 Testing Authentication Flow...")
        
        # Test registration
        test_email = f"test_{int(time.time())}@signalbeast.com"
        test_password = "TestPass123!"
        test_name = "Test User"
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"email": test_email, "password": test_password, "name": test_name}
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user_id')
            self.log(f"   ✅ Got auth token: {self.token[:20]}...")
        else:
            self.log("   ❌ Failed to get auth token from registration")
            return False
            
        # Test /auth/me with token
        success, user_data = self.run_test(
            "Get Current User",
            "GET", 
            "auth/me",
            200,
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ User data: {user_data.get('name')} ({user_data.get('email')})")
        
        # Test login with same credentials
        success, login_response = self.run_test(
            "User Login",
            "POST",
            "auth/login", 
            200,
            data={"email": test_email, "password": test_password}
        )
        
        return success
    
    def test_market_data(self):
        """Test market data endpoints"""
        self.log("\n📈 Testing Market Data Endpoints...")
        
        # Test crypto data
        self.run_test("Top Crypto", "GET", "market/crypto/top", 200)
        self.run_test("Bitcoin Price", "GET", "market/crypto/bitcoin", 200)
        self.run_test("Bitcoin Chart", "GET", "market/crypto/bitcoin/chart?days=7", 200)
        
        # Test forex data (mocked)
        self.run_test("Forex Data", "GET", "market/forex", 200)
        
        # Test Indian market data (mocked)
        self.run_test("Indian Market Data", "GET", "market/indian", 200)
        
        # Test sentiment data
        self.run_test("Market Sentiment", "GET", "market/sentiment", 200)
    
    def test_signals(self):
        """Test AI signals endpoints"""
        self.log("\n⚡ Testing AI Signals...")
        
        if not self.token:
            self.log("   ⚠️ Skipping signals tests - no auth token")
            return
            
        # Get signals list
        success, signals_data = self.run_test(
            "Get Signals List",
            "GET",
            "signals",
            200,
            auth_required=True
        )
        
        # Generate a signal
        signal_request = {
            "asset_id": "bitcoin",
            "asset_name": "Bitcoin (BTC)",
            "asset_type": "crypto",
            "timeframe": "1D"
        }
        
        success, signal_response = self.run_test(
            "Generate AI Signal",
            "POST",
            "signals/generate",
            200,
            data=signal_request,
            auth_required=True
        )
        
        if success:
            self.log(f"   ✅ Generated signal: {signal_response.get('direction')} {signal_response.get('asset_name')}")
            self.log(f"   ✅ Confidence: {signal_response.get('confidence')}%, Grade: {signal_response.get('grade')}")
    
    def test_portfolio(self):
        """Test portfolio endpoints"""
        self.log("\n💼 Testing Portfolio Management...")
        
        if not self.token:
            self.log("   ⚠️ Skipping portfolio tests - no auth token")
            return
            
        # Get portfolio
        success, portfolio_data = self.run_test(
            "Get Portfolio",
            "GET",
            "portfolio",
            200,
            auth_required=True
        )
        
        # Get portfolio summary
        success, summary_data = self.run_test(
            "Get Portfolio Summary",
            "GET",
            "portfolio/summary",
            200,
            auth_required=True
        )
        
        # Add a holding
        holding_data = {
            "asset_id": "bitcoin",
            "asset_name": "Bitcoin",
            "asset_type": "crypto",
            "quantity": 0.1,
            "buy_price": 45000.0
        }
        
        success, holding_response = self.run_test(
            "Add Portfolio Holding",
            "POST",
            "portfolio/holdings",
            200,
            data=holding_data,
            auth_required=True
        )
        
        holding_id = None
        if success and 'holding_id' in holding_response:
            holding_id = holding_response['holding_id']
            self.log(f"   ✅ Added holding: {holding_id}")
            
            # Delete the holding
            success, _ = self.run_test(
                "Delete Portfolio Holding",
                "DELETE",
                f"portfolio/holdings/{holding_id}",
                200,
                auth_required=True
            )
    
    def test_watchlist(self):
        """Test watchlist endpoints"""
        self.log("\n👁️ Testing Watchlist...")
        
        if not self.token:
            self.log("   ⚠️ Skipping watchlist tests - no auth token")
            return
            
        # Get watchlist
        success, watchlist_data = self.run_test(
            "Get Watchlist",
            "GET",
            "watchlist",
            200,
            auth_required=True
        )
        
        # Add to watchlist
        watchlist_item = {
            "asset_id": "ethereum",
            "asset_name": "Ethereum",
            "asset_type": "crypto"
        }
        
        success, watchlist_response = self.run_test(
            "Add to Watchlist",
            "POST",
            "watchlist",
            200,
            data=watchlist_item,
            auth_required=True
        )
        
        if success and 'watchlist_id' in watchlist_response:
            watchlist_id = watchlist_response['watchlist_id']
            self.log(f"   ✅ Added to watchlist: {watchlist_id}")
            
            # Remove from watchlist
            success, _ = self.run_test(
                "Remove from Watchlist",
                "DELETE",
                f"watchlist/{watchlist_id}",
                200,
                auth_required=True
            )
    
    def test_beast_ai_chat(self):
        """Test Beast AI chat endpoints"""
        self.log("\n🤖 Testing Beast AI Chat...")
        
        if not self.token:
            self.log("   ⚠️ Skipping chat tests - no auth token")
            return
            
        # Send a chat message
        chat_message = {
            "message": "What's the current market sentiment for Bitcoin?",
            "session_id": None
        }
        
        success, chat_response = self.run_test(
            "Send Chat Message",
            "POST",
            "chat",
            200,
            data=chat_message,
            auth_required=True
        )
        
        if success:
            session_id = chat_response.get('session_id')
            self.log(f"   ✅ Chat response received, session: {session_id}")
            self.log(f"   ✅ Response preview: {chat_response.get('response', '')[:100]}...")
            
            # Test chat history
            if session_id:
                success, history_data = self.run_test(
                    "Get Chat History",
                    "GET",
                    f"chat/history?session_id={session_id}",
                    200,
                    auth_required=True
                )
    
    def run_all_tests(self):
        """Run all test suites"""
        self.log("🚀 Starting SignalBeast Pro API Testing Suite")
        self.log(f"   Backend URL: {self.base_url}")
        
        start_time = time.time()
        
        # Test authentication first
        auth_success = self.test_auth_flow()
        
        # Test market data (no auth required)
        self.test_market_data()
        
        # Test authenticated endpoints
        if auth_success:
            self.test_signals()
            self.test_portfolio()
            self.test_watchlist()
            self.test_beast_ai_chat()
        else:
            self.log("⚠️ Skipping authenticated endpoint tests due to auth failure")
        
        # Test logout
        if self.token:
            self.run_test("User Logout", "POST", "auth/logout", 200, auth_required=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print summary
        self.log(f"\n📊 Test Summary:")
        self.log(f"   Total Tests: {self.tests_run}")
        self.log(f"   Passed: {self.tests_passed}")
        self.log(f"   Failed: {len(self.failed_tests)}")
        self.log(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        self.log(f"   Duration: {duration:.2f}s")
        
        if self.failed_tests:
            self.log(f"\n❌ Failed Tests:")
            for test in self.failed_tests:
                error_msg = test.get('error', f"Expected {test.get('expected')}, got {test.get('actual')}")
                self.log(f"   - {test['test']}: {error_msg}")
        
        return len(self.failed_tests) == 0

def main():
    tester = SignalBeastAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())