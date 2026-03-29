import re

with open("backend/server.py", "r") as f:
    content = f.read()

new_strategies = """    "elliott_wave": "Elliott Wave Theory: 5-wave impulse for trend, 3-wave ABC for correction. Enter at wave 3 start or wave 4 end.",
    "wyckoff_logic": "Wyckoff Method: Accumulation/Distribution phases. Spring or Upthrust for entry. High volume node confirmation.",
    "gann_angles": "Gann Fan & Angles: Geometric price-time analysis. 1x1 line determines trend. Reversal at key fan lines.",
    "renko_trends": "Renko Bricks: Noise reduction. Trade when brick color changes + MACD confirmation. Ideal for trailing stops.",
    "harmonic_patterns": "Harmonic Patterns: Gartley, Bat, Butterfly, Crab. High probability reversal zones defined by specific Fib ratios.",
    "vsa_volume_spread": "VSA (Volume Spread Analysis): Relationship between volume, range, and closing price to detect Smart Money.",
    "market_profile_tpo": "Market Profile: Time-Price Opportunities. Value Area High/Low fades. Point of Control (POC) mean reversion.",
    "order_flow_imbalance": "Order Flow & Imbalance: Footprint charts, aggressive buyer/seller delta. Delta divergence at key S/R levels.",
    "mean_reversion": "Statistical Mean Reversion: Standard deviation channels, VWAP standard error bands. Fade extreme excursions.",
    "statistical_arbitrage": "Pairs/Statistical Arb: Cointegration of correlated assets. Z-score > 2 fade, Z-score < -2 buy spread.",
"""

content = content.replace('    # === FOREX-SPECIFIC STRATEGIES ===', new_strategies + '\n    # === FOREX-SPECIFIC STRATEGIES ===')

# Update lists
forex_list = re.search(r'FOREX_STRATEGIES = \[(.*?)\]', content).group(1)
crypto_list = re.search(r'CRYPTO_STRATEGIES = \[(.*?)\]', content).group(1)
indian_list = re.search(r'INDIAN_STRATEGIES = \[(.*?)\]', content).group(1)

new_keys = ', "elliott_wave", "wyckoff_logic", "gann_angles", "renko_trends", "harmonic_patterns", "vsa_volume_spread", "market_profile_tpo", "order_flow_imbalance", "mean_reversion", "statistical_arbitrage"'

content = content.replace(f'FOREX_STRATEGIES = [{forex_list}]', f'FOREX_STRATEGIES = [{forex_list}{new_keys}]')
content = content.replace(f'CRYPTO_STRATEGIES = [{crypto_list}]', f'CRYPTO_STRATEGIES = [{crypto_list}{new_keys}]')
content = content.replace(f'INDIAN_STRATEGIES = [{indian_list}]', f'INDIAN_STRATEGIES = [{indian_list}{new_keys}]')

with open("backend/server.py", "w") as f:
    f.write(content)
