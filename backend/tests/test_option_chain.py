import pytest
import math
from backend.services.option_chain import black_scholes_call

class TestBlackScholesCall:
    """Test cases for the black_scholes_call function"""

    def test_black_scholes_call_atm(self):
        """Test At-The-Money (ATM) call option pricing"""
        S = 100.0  # Spot price
        K = 100.0  # Strike price
        T = 1.0    # Time to expiration (years)
        r = 0.05   # Risk-free rate
        sigma = 0.20 # Volatility

        price = black_scholes_call(S, K, T, r, sigma)
        assert price == pytest.approx(10.45058, abs=1e-4)

    def test_black_scholes_call_itm(self):
        """Test In-The-Money (ITM) call option pricing"""
        S = 110.0  # Spot price
        K = 100.0  # Strike price
        T = 1.0    # Time to expiration (years)
        r = 0.05   # Risk-free rate
        sigma = 0.20 # Volatility

        price = black_scholes_call(S, K, T, r, sigma)
        assert price == pytest.approx(17.66295, abs=1e-4)

    def test_black_scholes_call_otm(self):
        """Test Out-of-The-Money (OTM) call option pricing"""
        S = 90.0   # Spot price
        K = 100.0  # Strike price
        T = 1.0    # Time to expiration (years)
        r = 0.05   # Risk-free rate
        sigma = 0.20 # Volatility

        price = black_scholes_call(S, K, T, r, sigma)
        assert price == pytest.approx(5.09122, abs=1e-4)

    def test_black_scholes_call_zero_time(self):
        """Test pricing when time to expiration is zero (or negative)"""
        # ITM
        assert black_scholes_call(110.0, 100.0, 0.0, 0.05, 0.20) == 10.0
        assert black_scholes_call(110.0, 100.0, -0.5, 0.05, 0.20) == 10.0
        # OTM
        assert black_scholes_call(90.0, 100.0, 0.0, 0.05, 0.20) == 0.0
        assert black_scholes_call(90.0, 100.0, -0.5, 0.05, 0.20) == 0.0
        # ATM
        assert black_scholes_call(100.0, 100.0, 0.0, 0.05, 0.20) == 0.0

    def test_black_scholes_call_zero_volatility(self):
        """Test pricing when volatility is zero (or negative)"""
        # ITM
        assert black_scholes_call(110.0, 100.0, 1.0, 0.05, 0.0) == 10.0
        assert black_scholes_call(110.0, 100.0, 1.0, 0.05, -0.1) == 10.0
        # OTM
        assert black_scholes_call(90.0, 100.0, 1.0, 0.05, 0.0) == 0.0
        assert black_scholes_call(90.0, 100.0, 1.0, 0.05, -0.1) == 0.0
        # ATM
        assert black_scholes_call(100.0, 100.0, 1.0, 0.05, 0.0) == 0.0

    def test_black_scholes_call_high_volatility(self):
        """Test pricing with very high volatility"""
        S = 100.0
        K = 100.0
        T = 1.0
        r = 0.05
        sigma = 5.0 # Very high volatility

        price = black_scholes_call(S, K, T, r, sigma)
        # As volatility approaches infinity, call option price approaches S
        assert price > 90.0
        assert price <= 100.0
