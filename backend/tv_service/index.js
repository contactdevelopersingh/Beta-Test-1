const TradingView = require('@mathieuc/tradingview');
const express = require('express');

const app = express();
const PORT = 8099;

// Map our asset IDs to TradingView symbols
const SYMBOL_MAP = {
  // Crypto
  'bitcoin': 'BINANCE:BTCUSDT', 'ethereum': 'BINANCE:ETHUSDT', 'solana': 'BINANCE:SOLUSDT',
  'binancecoin': 'BINANCE:BNBUSDT', 'ripple': 'BINANCE:XRPUSDT', 'cardano': 'BINANCE:ADAUSDT',
  'dogecoin': 'BINANCE:DOGEUSDT', 'polkadot': 'BINANCE:DOTUSDT', 'avalanche-2': 'BINANCE:AVAXUSDT',
  'chainlink': 'BINANCE:LINKUSDT', 'litecoin': 'BINANCE:LTCUSDT', 'cosmos': 'BINANCE:ATOMUSDT',
  'uniswap': 'BINANCE:UNIUSDT', 'near': 'BINANCE:NEARUSDT', 'aptos': 'BINANCE:APTUSDT',
  'filecoin': 'BINANCE:FILUSDT', 'stellar': 'BINANCE:XLMUSDT', 'tron': 'BINANCE:TRXUSDT',
  'injective-protocol': 'BINANCE:INJUSDT', 'shiba-inu': 'BINANCE:SHIBUSDT',
  'matic-network': 'BINANCE:POLUSDT',
  // Forex
  'eurusd': 'FX:EURUSD', 'gbpusd': 'FX:GBPUSD', 'usdjpy': 'FX:USDJPY',
  'audusd': 'FX:AUDUSD', 'usdchf': 'FX:USDCHF', 'usdcad': 'FX:USDCAD',
  'nzdusd': 'FX:NZDUSD', 'xauusd': 'TVC:GOLD', 'xagusd': 'TVC:SILVER',
  'eurgbp': 'FX:EURGBP', 'eurjpy': 'FX:EURJPY', 'gbpjpy': 'FX:GBPJPY',
  'audjpy': 'FX:AUDJPY', 'cadjpy': 'FX:CADJPY', 'gbpchf': 'FX:GBPCHF',
  'euraud': 'FX:EURAUD', 'eurchf': 'FX:EURCHF', 'gbpaud': 'FX:GBPAUD',
  'gbpnzd': 'FX:GBPNZD', 'audnzd': 'FX:AUDNZD',
  // Indian
  'nifty50': 'NSE:NIFTY', 'sensex': 'BSE:SENSEX', 'banknifty': 'NSE:BANKNIFTY',
  'reliance': 'NSE:RELIANCE', 'tcs': 'NSE:TCS', 'infy': 'NSE:INFY',
  'hdfcbank': 'NSE:HDFCBANK', 'icicibank': 'NSE:ICICIBANK', 'sbin': 'NSE:SBIN',
  'itc': 'NSE:ITC', 'bhartiartl': 'NSE:BHARTIARTL', 'bajfinance': 'NSE:BAJFINANCE',
  'adanient': 'NSE:ADANIENT', 'axisbank': 'NSE:AXISBANK', 'maruti': 'NSE:MARUTI',
};

function ratingToLabel(val) {
  if (val >= 0.5) return 'Strong Buy';
  if (val >= 0.1) return 'Buy';
  if (val > -0.1) return 'Neutral';
  if (val > -0.5) return 'Sell';
  return 'Strong Sell';
}

// In-memory cache (TTL: 30 seconds)
const cache = {};
const CACHE_TTL = 30000;

// Get TradingView Technical Analysis across all timeframes
app.get('/ta/:assetId', async (req, res) => {
  const { assetId } = req.params;
  const tvSymbol = SYMBOL_MAP[assetId];
  if (!tvSymbol) return res.json({ error: 'Unknown asset', data: null });

  // Check cache
  const cached = cache[assetId];
  if (cached && Date.now() - cached.time < CACHE_TTL) {
    return res.json(cached.data);
  }

  try {
    const ta = await TradingView.getTA(tvSymbol);
    if (!ta) return res.json({ error: 'No data from TradingView', data: null });

    // Parse into readable format
    const timeframes = {};
    for (const [tf, vals] of Object.entries(ta)) {
      const tfLabel = { '1': '1m', '5': '5m', '15': '15m', '60': '1H', '240': '4H', '1D': '1D', '1W': '1W', '1M': '1M' }[tf] || tf;
      timeframes[tfLabel] = {
        oscillators: { value: vals.Other, label: ratingToLabel(vals.Other) },
        moving_averages: { value: vals.MA, label: ratingToLabel(vals.MA) },
        overall: { value: vals.All, label: ratingToLabel(vals.All) },
      };
    }

    // Compute summary across key timeframes
    const keyTFs = ['15m', '1H', '4H', '1D'];
    let bullCount = 0, bearCount = 0;
    for (const tf of keyTFs) {
      if (timeframes[tf]) {
        const v = timeframes[tf].overall.value;
        if (v > 0.1) bullCount++;
        else if (v < -0.1) bearCount++;
      }
    }
    const tvBias = bullCount > bearCount ? 'Bullish' : bearCount > bullCount ? 'Bearish' : 'Neutral';
    const tvConfluence = Math.max(bullCount, bearCount);

    const result = {
      symbol: tvSymbol,
      asset_id: assetId,
      timeframes,
      summary: {
        bias: tvBias,
        bull_timeframes: bullCount,
        bear_timeframes: bearCount,
        confluence: tvConfluence,
        label: `TradingView: ${tvBias} (${bullCount} bull / ${bearCount} bear across ${keyTFs.join(', ')})`
      }
    };

    cache[assetId] = { data: result, time: Date.now() };
    res.json(result);
  } catch (e) {
    console.error(`TA error for ${assetId}:`, e.message);
    res.json({ error: e.message, data: null });
  }
});

// Batch TA for multiple assets
app.get('/ta-batch', async (req, res) => {
  const ids = (req.query.ids || '').split(',').filter(Boolean);
  if (!ids.length) return res.json({ error: 'No ids', results: {} });

  const results = {};
  await Promise.allSettled(ids.map(async (id) => {
    const tvSymbol = SYMBOL_MAP[id];
    if (!tvSymbol) return;
    try {
      const ta = await TradingView.getTA(tvSymbol);
      if (ta) results[id] = ta;
    } catch (e) {}
  }));
  res.json({ results });
});

app.get('/health', (req, res) => res.json({ status: 'ok', service: 'tv-service', symbols: Object.keys(SYMBOL_MAP).length }));

app.listen(PORT, '127.0.0.1', () => {
  console.log(`TradingView Service running on port ${PORT} | ${Object.keys(SYMBOL_MAP).length} symbols mapped`);
});
