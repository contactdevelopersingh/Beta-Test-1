import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, AreaSeries, CandlestickSeries, HistogramSeries } from 'lightweight-charts';

export const TradingChart = ({ data, symbol, height = 350, showVolume = true }) => {
  const containerRef = useRef(null);
  const [chartType, setChartType] = useState('area');

  useEffect(() => {
    if (!containerRef.current || !data || data.length === 0) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: 'rgba(255,255,255,0.4)',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 10,
      },
      localization: {
        locale: 'en-US',
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.03)' },
        horzLines: { color: 'rgba(255,255,255,0.03)' },
      },
      crosshair: {
        mode: 0,
        vertLine: { color: 'rgba(99,102,241,0.3)', labelBackgroundColor: '#6366F1' },
        horzLine: { color: 'rgba(99,102,241,0.3)', labelBackgroundColor: '#6366F1' },
      },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.05)',
        scaleMargins: { top: 0.1, bottom: showVolume ? 0.25 : 0.1 },
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.05)',
        timeVisible: true,
        secondsVisible: false,
      },
      width: containerRef.current.clientWidth,
      height: height,
      handleScroll: { vertTouchDrag: false },
    });

    if (chartType === 'candlestick' && data[0]?.open !== undefined) {
      const mainSeries = chart.addSeries(CandlestickSeries, {
        upColor: '#00FF94',
        downColor: '#FF2E2E',
        borderUpColor: '#00FF94',
        borderDownColor: '#FF2E2E',
        wickUpColor: '#00FF94',
        wickDownColor: '#FF2E2E',
      });
      mainSeries.setData(data);
    } else {
      const mainSeries = chart.addSeries(AreaSeries, {
        lineColor: '#6366F1',
        topColor: 'rgba(99,102,241,0.3)',
        bottomColor: 'rgba(99,102,241,0.01)',
        lineWidth: 2,
      });
      const areaData = data.map(d => ({
        time: d.time,
        value: d.close || d.value || d.price || 0,
      }));
      mainSeries.setData(areaData);
    }

    if (showVolume && data[0]?.volume !== undefined) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        color: 'rgba(99,102,241,0.2)',
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      });
      volumeSeries.priceScale().applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });
      volumeSeries.setData(data.map(d => ({
        time: d.time,
        value: d.volume || 0,
        color: (d.close || 0) >= (d.open || 0) ? 'rgba(0,255,148,0.15)' : 'rgba(255,46,46,0.15)',
      })));
    }

    chart.timeScale().fitContent();

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, chartType, height, showVolume]);

  return (
    <div data-testid="trading-chart">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[10px] text-white/40 uppercase tracking-wider">{symbol}</span>
        <div className="flex gap-1">
          {['area', 'candlestick'].map(t => (
            <button
              key={t}
              onClick={() => setChartType(t)}
              className={`px-2 py-0.5 rounded text-[10px] font-medium ${chartType === t ? 'bg-[#6366F1] text-white' : 'bg-white/5 text-white/40 hover:text-white/60'}`}
              data-testid={`chart-type-${t}`}
            >
              {t === 'area' ? 'Line' : 'Candles'}
            </button>
          ))}
        </div>
      </div>
      <div ref={containerRef} className="rounded-lg overflow-hidden" />
    </div>
  );
};
