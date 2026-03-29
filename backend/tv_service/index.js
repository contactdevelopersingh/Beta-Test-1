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
  let tvSymbol = SYMBOL_MAP[assetId];
  if (!tvSymbol) {
    if (assetId.startsWith('NSE:') || assetId.startsWith('BSE:')) {
      tvSymbol = assetId;
    } else {
      return res.json({ error: 'Unknown asset', data: null });
    }
  }

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
    let tvSymbol = SYMBOL_MAP[id];
    if (!tvSymbol && (id.startsWith('NSE:') || id.startsWith('BSE:'))) {
      tvSymbol = id;
    }
    if (!tvSymbol) return;
    try {
      const ta = await TradingView.getTA(tvSymbol);
      if (ta) results[id] = ta;
    } catch (e) {}
  }));
  res.json({ results });
});

app.get('/health', (req, res) => res.json({ status: 'ok', service: 'tv-nse-service', symbols: Object.keys(SYMBOL_MAP).length }));

// ==================== NSE INDIA DATA ====================
const { NseIndia } = require('stock-nse-india');
const nse = new NseIndia();

// Cache
const nseCache = {};
const NSE_TTL = 60000; // 1 min
function getNseCache(key) {
  const c = nseCache[key];
  if (c && Date.now() - c.time < NSE_TTL) return c.data;
  return null;
}
function setNseCache(key, data) { nseCache[key] = { data, time: Date.now() }; }

// All NSE stock symbols
app.get('/nse/stocks', async (req, res) => {
  try {
    const cached = getNseCache('all_stocks');
    if (cached) return res.json(cached);
    const symbols = await nse.getAllStockSymbols();
    const result = { stocks: symbols, count: symbols.length };
    setNseCache('all_stocks', result);
    res.json(result);
  } catch (e) { res.json({ error: e.message, stocks: [] }); }
});

// Equity details
app.get('/nse/equity/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const cached = getNseCache(`eq_${symbol}`);
    if (cached) return res.json(cached);
    const data = await nse.getEquityDetails(symbol.toUpperCase());
    setNseCache(`eq_${symbol}`, data);
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

// Equity Option Chain (LIVE)
app.get('/nse/optionchain/equity/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const cached = getNseCache(`oc_eq_${symbol}`);
    if (cached) return res.json(cached);
    const data = await nse.getEquityOptionChain(symbol.toUpperCase());
    setNseCache(`oc_eq_${symbol}`, data);
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

// Index Option Chain (NIFTY, BANKNIFTY)
app.get('/nse/optionchain/index/:index', async (req, res) => {
  try {
    const { index } = req.params;
    const cached = getNseCache(`oc_idx_${index}`);
    if (cached) return res.json(cached);
    const data = await nse.getIndexOptionChain(index.toUpperCase());
    setNseCache(`oc_idx_${index}`, data);
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

// All market indices
app.get('/nse/indices', async (req, res) => {
  try {
    const cached = getNseCache('indices');
    if (cached) return res.json(cached);
    const data = await nse.getEquityStockIndices('NIFTY 50');
    setNseCache('indices', data);
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

// Gainers & Losers
app.get('/nse/gainers-losers/:index', async (req, res) => {
  try {
    const { index } = req.params;
    const cached = getNseCache(`gl_${index}`);
    if (cached) return res.json(cached);
    const data = await nse.getGainersAndLosersByIndex(index.toUpperCase().replace(/-/g, ' '));
    setNseCache(`gl_${index}`, data);
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

// Most Active
app.get('/nse/most-active', async (req, res) => {
  try {
    const cached = getNseCache('most_active');
    if (cached) return res.json(cached);
    const data = await nse.getMostActiveEquities();
    setNseCache('most_active', data);
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

// Corporate Info
app.get('/nse/corporate/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const data = await nse.getEquityCorporateInfo(symbol.toUpperCase());
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

// Trade Info
app.get('/nse/tradeinfo/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const data = await nse.getEquityTradeInfo(symbol.toUpperCase());
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

// Historical Data
app.get('/nse/historical/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const days = parseInt(req.query.days) || 365;
    const end = new Date();
    const start = new Date(end - days * 86400000);
    const data = await nse.getEquityHistoricalData(symbol.toUpperCase(), { start, end });
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

// Intraday Data
app.get('/nse/intraday/:symbol', async (req, res) => {
  try {
    const { symbol } = req.params;
    const data = await nse.getEquityIntradayData(symbol.toUpperCase());
    res.json(data);
  } catch (e) { res.json({ error: e.message }); }
});

app.listen(PORT, '127.0.0.1', () => {
  console.log(`TradingView + NSE Service running on port ${PORT} | ${Object.keys(SYMBOL_MAP).length} TV symbols`);
});
