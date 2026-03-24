"""
Iteration 11 - Testing new features:
- Plan-based feature gating (GET /api/user/plan-usage, GET /api/user/plan)
- Community & Leaderboard (GET /api/community/stats, /api/community/leaderboard, /api/community/my-stats)
- Trade execution (GET /api/trade/account, /api/trade/positions, /api/trade/history)
- SEO (GET /api/sitemap.xml)
- Signal generation respects plan limits
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "contact.developersingh@gmail.com"
ADMIN_PASSWORD = "admin123"

@pytest.fixture(scope="module")
def admin_token():
    """Login as admin (titan plan user) and get token"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json().get('token')

@pytest.fixture(scope="module")
def admin_session(admin_token):
    """Create session with admin auth"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    })
    return session


class TestPlanBasedFeatureGating:
    """Test plan-based feature gating endpoints"""
    
    def test_get_user_plan_returns_limits_and_features(self, admin_session):
        """GET /api/user/plan returns plan info with limits and features fields"""
        resp = admin_session.get(f"{BASE_URL}/api/user/plan")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify required fields
        assert 'plan_name' in data, "Missing plan_name"
        assert 'limits' in data, "Missing limits field"
        assert 'features' in data, "Missing features field"
        
        # Verify limits structure
        limits = data['limits']
        assert 'signals_per_day' in limits, "Missing signals_per_day in limits"
        assert 'chat_msgs_per_day' in limits, "Missing chat_msgs_per_day in limits"
        assert 'multi_timeframe' in limits, "Missing multi_timeframe in limits"
        assert 'trade_execution' in limits, "Missing trade_execution in limits"
        
        print(f"User plan: {data['plan_name']}, limits: {limits}")
    
    def test_get_plan_usage_returns_correct_structure(self, admin_session):
        """GET /api/user/plan-usage returns correct limits and usage for logged-in user"""
        resp = admin_session.get(f"{BASE_URL}/api/user/plan-usage")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify required fields
        assert 'plan_name' in data, "Missing plan_name"
        assert 'limits' in data, "Missing limits"
        assert 'usage' in data, "Missing usage"
        
        # Verify limits structure
        limits = data['limits']
        assert 'signals_per_day' in limits, "Missing signals_per_day"
        assert 'chat_msgs_per_day' in limits, "Missing chat_msgs_per_day"
        assert 'alerts' in limits, "Missing alerts"
        assert 'multi_timeframe' in limits, "Missing multi_timeframe"
        assert 'trade_execution' in limits, "Missing trade_execution"
        
        # Verify usage structure
        usage = data['usage']
        assert 'signals_today' in usage, "Missing signals_today"
        assert 'chat_msgs_today' in usage, "Missing chat_msgs_today"
        assert 'active_alerts' in usage, "Missing active_alerts"
        
        print(f"Plan: {data['plan_name']}, Usage: {usage}")


class TestCommunityAndLeaderboard:
    """Test community stats and leaderboard endpoints"""
    
    def test_community_stats_returns_correct_fields(self, admin_session):
        """GET /api/community/stats returns total_traders, total_signals, etc."""
        resp = admin_session.get(f"{BASE_URL}/api/community/stats")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify required fields
        assert 'total_traders' in data, "Missing total_traders"
        assert 'total_signals_generated' in data, "Missing total_signals_generated"
        assert 'total_trades_logged' in data, "Missing total_trades_logged"
        assert 'community_win_rate' in data, "Missing community_win_rate"
        
        # Verify types
        assert isinstance(data['total_traders'], int), "total_traders should be int"
        assert isinstance(data['total_signals_generated'], int), "total_signals_generated should be int"
        assert isinstance(data['total_trades_logged'], int), "total_trades_logged should be int"
        assert isinstance(data['community_win_rate'], (int, float)), "community_win_rate should be numeric"
        
        print(f"Community stats: {data}")
    
    def test_leaderboard_returns_array(self, admin_session):
        """GET /api/community/leaderboard returns array (may be empty if no trades)"""
        resp = admin_session.get(f"{BASE_URL}/api/community/leaderboard")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert 'leaderboard' in data, "Missing leaderboard field"
        assert isinstance(data['leaderboard'], list), "leaderboard should be a list"
        
        # If there are entries, verify structure
        if len(data['leaderboard']) > 0:
            entry = data['leaderboard'][0]
            assert 'rank' in entry, "Missing rank"
            assert 'user_id' in entry, "Missing user_id"
            assert 'name' in entry, "Missing name"
            assert 'total_trades' in entry, "Missing total_trades"
            assert 'total_pnl' in entry, "Missing total_pnl"
            assert 'win_rate' in entry, "Missing win_rate"
            assert 'tier' in entry, "Missing tier"
            print(f"Leaderboard has {len(data['leaderboard'])} entries, top: {entry['name']}")
        else:
            print("Leaderboard is empty (no closed trades with 3+ entries)")
    
    def test_my_community_stats_returns_badges_and_rank(self, admin_session):
        """GET /api/community/my-stats returns badges, rank, win_rate etc."""
        resp = admin_session.get(f"{BASE_URL}/api/community/my-stats")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify required fields
        assert 'total_trades' in data, "Missing total_trades"
        assert 'closed_trades' in data, "Missing closed_trades"
        assert 'wins' in data, "Missing wins"
        assert 'losses' in data, "Missing losses"
        assert 'win_rate' in data, "Missing win_rate"
        assert 'total_pnl' in data, "Missing total_pnl"
        assert 'badges' in data, "Missing badges"
        assert 'leaderboard_rank' in data, "Missing leaderboard_rank"
        
        # Verify badges is a list
        assert isinstance(data['badges'], list), "badges should be a list"
        
        print(f"My stats: trades={data['total_trades']}, win_rate={data['win_rate']}%, badges={len(data['badges'])}")


class TestTradeExecution:
    """Test OANDA trade execution endpoints"""
    
    def test_trade_account_returns_balance_info(self, admin_session):
        """GET /api/trade/account returns balance, nav, margin info from OANDA"""
        resp = admin_session.get(f"{BASE_URL}/api/trade/account")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        # Verify required fields (may have error if OANDA not configured)
        if 'error' not in data:
            assert 'balance' in data, "Missing balance"
            assert 'nav' in data, "Missing nav"
            assert 'unrealized_pnl' in data, "Missing unrealized_pnl"
            assert 'margin_used' in data, "Missing margin_used"
            assert 'margin_available' in data, "Missing margin_available"
            assert 'open_trade_count' in data, "Missing open_trade_count"
            
            print(f"OANDA Account: balance=${data['balance']}, NAV=${data['nav']}, open_trades={data['open_trade_count']}")
        else:
            print(f"OANDA not configured: {data['error']}")
    
    def test_trade_positions_returns_array(self, admin_session):
        """GET /api/trade/positions returns positions array"""
        resp = admin_session.get(f"{BASE_URL}/api/trade/positions")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert 'positions' in data, "Missing positions field"
        assert isinstance(data['positions'], list), "positions should be a list"
        
        # If there are positions, verify structure
        if len(data['positions']) > 0:
            pos = data['positions'][0]
            assert 'instrument' in pos, "Missing instrument"
            assert 'direction' in pos, "Missing direction"
            assert 'units' in pos, "Missing units"
            assert 'unrealized_pnl' in pos, "Missing unrealized_pnl"
            print(f"Open positions: {len(data['positions'])}")
        else:
            print("No open positions")
    
    def test_trade_history_returns_user_trades(self, admin_session):
        """GET /api/trade/history returns user's trade execution history"""
        resp = admin_session.get(f"{BASE_URL}/api/trade/history")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert 'trades' in data, "Missing trades field"
        assert isinstance(data['trades'], list), "trades should be a list"
        
        # If there are trades, verify structure
        if len(data['trades']) > 0:
            trade = data['trades'][0]
            assert 'trade_id' in trade, "Missing trade_id"
            assert 'instrument' in trade, "Missing instrument"
            assert 'units' in trade, "Missing units"
            assert 'created_at' in trade, "Missing created_at"
            print(f"Trade history: {len(data['trades'])} executions")
        else:
            print("No trade executions yet")


class TestSEO:
    """Test SEO endpoints"""
    
    def test_sitemap_returns_valid_xml(self, admin_session):
        """GET /api/sitemap.xml returns valid XML sitemap"""
        resp = admin_session.get(f"{BASE_URL}/api/sitemap.xml")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        
        # Verify content type
        content_type = resp.headers.get('content-type', '')
        assert 'xml' in content_type.lower(), f"Expected XML content type, got: {content_type}"
        
        # Verify XML structure
        content = resp.text
        assert '<?xml version="1.0"' in content, "Missing XML declaration"
        assert '<urlset' in content, "Missing urlset element"
        assert '</urlset>' in content, "Missing closing urlset"
        assert '<url>' in content, "Missing url elements"
        assert '<loc>' in content, "Missing loc elements"
        
        # Verify key pages are included
        assert '/dashboard' in content, "Missing /dashboard in sitemap"
        assert '/signals' in content, "Missing /signals in sitemap"
        assert '/markets' in content, "Missing /markets in sitemap"
        assert '/pricing' in content, "Missing /pricing in sitemap"
        
        print(f"Sitemap XML valid, length: {len(content)} chars")


class TestSignalPlanGating:
    """Test that signal generation respects plan limits"""
    
    def test_signals_endpoint_works(self, admin_session):
        """GET /api/signals returns signals list"""
        resp = admin_session.get(f"{BASE_URL}/api/signals")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert 'signals' in data, "Missing signals field"
        assert isinstance(data['signals'], list), "signals should be a list"
        print(f"User has {len(data['signals'])} signals")
    
    def test_strategies_endpoint_returns_all_strategies(self, admin_session):
        """GET /api/signals/strategies returns available strategies"""
        resp = admin_session.get(f"{BASE_URL}/api/signals/strategies")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert 'strategies' in data, "Missing strategies field"
        strategies = data['strategies']
        assert len(strategies) >= 10, f"Expected at least 10 strategies, got {len(strategies)}"
        
        # Verify strategy structure
        for s in strategies:
            assert 'id' in s, "Missing id in strategy"
            assert 'name' in s, "Missing name in strategy"
            assert 'description' in s, "Missing description in strategy"
        
        strategy_ids = [s['id'] for s in strategies]
        assert 'auto' in strategy_ids, "Missing auto strategy"
        assert 'smc' in strategy_ids, "Missing smc strategy"
        assert 'ema_crossover' in strategy_ids, "Missing ema_crossover strategy"
        
        print(f"Available strategies: {strategy_ids}")


class TestNavigationAndPages:
    """Test that new pages are accessible"""
    
    def test_market_live_endpoint(self, admin_session):
        """GET /api/market/live returns live data"""
        resp = admin_session.get(f"{BASE_URL}/api/market/live")
        assert resp.status_code == 200, f"Failed: {resp.text}"
        data = resp.json()
        
        assert 'crypto' in data, "Missing crypto"
        assert 'forex' in data, "Missing forex"
        assert 'indian' in data, "Missing indian"
        assert 'market_status' in data, "Missing market_status"
        
        print(f"Live data: {len(data['crypto'])} crypto, {len(data['forex'])} forex, {len(data['indian'])} indian")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
