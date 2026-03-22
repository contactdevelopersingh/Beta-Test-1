import { useState, useEffect, useRef, useCallback } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const useMarketStream = (enabled = true, interval = 1500) => {
  const [data, setData] = useState({
    crypto: [], forex: [], indian: [],
    gainers: [], losers: [],
    tick: 0, connected: false, initialized: false,
  });
  const [priceChanges, setPriceChanges] = useState({});
  const prevPrices = useRef({});
  const timeoutRef = useRef(null);

  const fetchPrices = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/market/live`);
      if (!res.ok) throw new Error('Failed');
      const json = await res.json();

      const changes = {};
      ['crypto', 'forex', 'indian'].forEach(market => {
        (json[market] || []).forEach(item => {
          const prev = prevPrices.current[item.id];
          if (prev !== undefined && Math.abs(prev - item.price) > 0.0001) {
            changes[item.id] = item.price > prev ? 'up' : 'down';
          }
          prevPrices.current[item.id] = item.price;
        });
      });

      setPriceChanges(changes);
      setData({ ...json, connected: true });

      // Clear flash after animation duration
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setPriceChanges({}), 800);
    } catch {
      setData(prev => ({ ...prev, connected: false }));
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    fetchPrices();
    const id = setInterval(fetchPrices, interval);
    return () => {
      clearInterval(id);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [enabled, fetchPrices, interval]);

  return { ...data, priceChanges };
};
