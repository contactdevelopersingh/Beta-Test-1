#!/usr/bin/env python3
"""
Focused test for SignalBeast Pro key improvements:
1. Live Forex data with correct price ranges
2. Live Indian market data with 15+ indices and 25+ stocks
3. Diverse signal generation (not stuck at 78%/B+)
"""

import requests
import json
import time
from datetime import datetime

def test_forex_live_data():
    """Test forex API returns live data with expected price ranges"""
    print("🔍 Testing Forex Live Data...")
    
    try:
        response = requests.get("https://signal-beast-pro.preview.emergentagent.com/api/market/forex", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Forex API failed with status {response.status_code}")
            return False
        
        data = response.json()
        pairs = data.get('pairs', [])
        source = data.get('source', 'unknown')
        
        print(f"✅ Forex API returned {len(pairs)} pairs, source: {source}")
        
        # Check for expected major pairs and their price ranges
        expected_checks = {
            'eurusd': {'min': 1.0, 'max': 1.3, 'name': 'EUR/USD'},
            'gbpusd': {'min': 1.1, 'max': 1.5, 'name': 'GBP/USD'},
            'usdjpy': {'min': 140, 'max': 170, 'name': 'USD/JPY'}
        }
        
        found_pairs = {}
        for pair in pairs:
            pair_id = pair.get('id')
            if pair_id in expected_checks:
                found_pairs[pair_id] = pair
                price = pair.get('price', 0)
                expected = expected_checks[pair_id]
                
                if expected['min'] <= price <= expected['max']:
                    print(f"✅ {expected['name']}: ${price:.4f} (within expected range)")
                else:
                    print(f"⚠️  {expected['name']}: ${price:.4f} (outside expected range {expected['min']}-{expected['max']})")
        
        missing = [expected_checks[p]['name'] for p in expected_checks if p not in found_pairs]
        if missing:
            print(f"❌ Missing expected pairs: {missing}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Forex test failed: {e}")
        return False

def test_indian_market_data():
    """Test Indian market API returns live data with sufficient indices and stocks"""
    print("\n🔍 Testing Indian Market Live Data...")
    
    try:
        response = requests.get("https://signal-beast-pro.preview.emergentagent.com/api/market/indian", timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Indian market API failed with status {response.status_code}")
            return False
        
        data = response.json()
        stocks = data.get('stocks', [])
        source = data.get('source', 'unknown')
        
        # Separate indices and stocks
        indices = [s for s in stocks if s.get('type') == 'index']
        stock_items = [s for s in stocks if s.get('type') == 'stock']
        
        print(f"✅ Indian Market API returned {len(stocks)} total items, source: {source}")
        print(f"   - Indices: {len(indices)}")
        print(f"   - Stocks: {len(stock_items)}")
        
        # Check minimum requirements
        if len(indices) < 15:
            print(f"❌ Expected 15+ indices, got {len(indices)}")
            return False
        
        if len(stock_items) < 25:
            print(f"❌ Expected 25+ stocks, got {len(stock_items)}")
            return False
        
        # Check for key indices
        expected_indices = ['nifty50', 'sensex', 'banknifty', 'niftyit', 'niftypharma', 'niftyauto']
        found_indices = [s['id'] for s in indices]
        
        missing_indices = [idx for idx in expected_indices if idx not in found_indices]
        if missing_indices:
            print(f"❌ Missing key indices: {missing_indices}")
            return False
        
        print(f"✅ Found all key indices: {expected_indices}")
        
        # Check for key stocks
        expected_stocks = ['reliance', 'tcs', 'infy', 'hdfcbank', 'sbin']
        found_stocks = [s['id'] for s in stock_items]
        
        missing_stocks = [stock for stock in expected_stocks if stock not in found_stocks]
        if missing_stocks:
            print(f"❌ Missing key stocks: {missing_stocks}")
            return False
        
        print(f"✅ Found all key stocks: {expected_stocks}")
        
        return True
        
    except Exception as e:
        print(f"❌ Indian market test failed: {e}")
        return False

def test_signal_diversity():
    """Test signal generation for diversity (not stuck at 78%/B+)"""
    print("\n🔍 Testing Signal Generation Diversity...")
    
    # First login to get token
    try:
        login_response = requests.post(
            "https://signal-beast-pro.preview.emergentagent.com/api/auth/login",
            json={"email": "chattest@test.com", "password": "test123"},
            timeout=30
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed with status {login_response.status_code}")
            return False
        
        token = login_response.json().get('token')
        if not token:
            print("❌ No token received from login")
            return False
        
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        # Generate multiple signals to test diversity
        test_assets = [
            {"asset_id": "bitcoin", "asset_name": "Bitcoin (BTC)", "asset_type": "crypto"},
            {"asset_id": "ethereum", "asset_name": "Ethereum (ETH)", "asset_type": "crypto"},
            {"asset_id": "eurusd", "asset_name": "EUR/USD", "asset_type": "forex"},
        ]
        
        generated_signals = []
        
        for asset in test_assets:
            try:
                signal_response = requests.post(
                    "https://signal-beast-pro.preview.emergentagent.com/api/signals/generate",
                    json={
                        "asset_id": asset["asset_id"],
                        "asset_name": asset["asset_name"],
                        "asset_type": asset["asset_type"],
                        "timeframe": "1D"
                    },
                    headers=headers,
                    timeout=30
                )
                
                if signal_response.status_code == 200:
                    signal_data = signal_response.json()
                    confidence = signal_data.get('confidence')
                    grade = signal_data.get('grade')
                    direction = signal_data.get('direction')
                    
                    generated_signals.append({
                        'asset': asset['asset_name'],
                        'confidence': confidence,
                        'grade': grade,
                        'direction': direction
                    })
                    
                    print(f"✅ {asset['asset_name']}: {confidence}% confidence, Grade {grade}, {direction}")
                    
                    # Verify grade matches confidence
                    expected_grade = 'A+' if confidence >= 90 else 'A' if confidence >= 80 else 'B+' if confidence >= 70 else 'B' if confidence >= 60 else 'C'
                    if grade != expected_grade:
                        print(f"⚠️  Grade mismatch: {grade} vs expected {expected_grade} for {confidence}%")
                else:
                    print(f"❌ Signal generation failed for {asset['asset_name']}: {signal_response.status_code}")
                
                # Add delay between requests
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error generating signal for {asset['asset_name']}: {e}")
        
        if len(generated_signals) < 2:
            print("❌ Not enough signals generated for diversity test")
            return False
        
        # Check for diversity
        confidences = [s['confidence'] for s in generated_signals]
        grades = [s['grade'] for s in generated_signals]
        
        # Check if stuck at 78%
        if all(c == 78 for c in confidences):
            print("❌ All signals stuck at 78% confidence - diversity issue!")
            return False
        
        # Check if stuck at B+
        if all(g == 'B+' for g in grades):
            print("❌ All signals stuck at B+ grade - diversity issue!")
            return False
        
        print(f"✅ Signal diversity confirmed:")
        print(f"   - Confidence scores: {confidences}")
        print(f"   - Grades: {grades}")
        
        return True
        
    except Exception as e:
        print(f"❌ Signal diversity test failed: {e}")
        return False

def main():
    """Run focused tests for key improvements"""
    print("🚀 SignalBeast Pro - Testing Key Improvements")
    print("=" * 60)
    
    results = {
        'forex_live_data': test_forex_live_data(),
        'indian_market_data': test_indian_market_data(),
        'signal_diversity': test_signal_diversity()
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All key improvements are working correctly!")
        return True
    else:
        print("⚠️  Some improvements need attention")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)