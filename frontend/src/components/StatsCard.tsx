import React, { useEffect, useRef, useState } from 'react';

interface StatsCardProps {
  label: string;
  value: number | string;
  suffix?: string;
  icon: React.ReactNode;
  trend?: number; // positive = up, negative = down
  trendLabel?: string;
  colorVariant?: 'blue' | 'green' | 'purple' | 'amber' | 'red';
  animateCount?: boolean;
}

const VARIANT_MAP = {
  blue:   { icon: 'rgba(59,130,246,0.15)',  iconText: '#60a5fa',  glow: '0 4px 20px rgba(59,130,246,0.12)',  border: 'rgba(59,130,246,0.15)',  bar: '#3b82f6' },
  green:  { icon: 'rgba(16,185,129,0.15)',  iconText: '#34d399',  glow: '0 4px 20px rgba(16,185,129,0.12)',  border: 'rgba(16,185,129,0.15)',  bar: '#10b981' },
  purple: { icon: 'rgba(168,85,247,0.15)',  iconText: '#c084fc',  glow: '0 4px 20px rgba(168,85,247,0.12)', border: 'rgba(168,85,247,0.15)', bar: '#a855f7' },
  amber:  { icon: 'rgba(245,158,11,0.15)',  iconText: '#fbbf24',  glow: '0 4px 20px rgba(245,158,11,0.12)',  border: 'rgba(245,158,11,0.15)',  bar: '#f59e0b' },
  red:    { icon: 'rgba(239,68,68,0.15)',   iconText: '#f87171',  glow: '0 4px 20px rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.15)',   bar: '#ef4444' },
};

const TrendArrowUp = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="18 15 12 9 6 15"/>
  </svg>
);
const TrendArrowDown = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 12 15 18 9"/>
  </svg>
);

export const StatsCard: React.FC<StatsCardProps> = ({
  label, value, suffix = '', icon,
  trend, trendLabel,
  colorVariant = 'blue',
  animateCount = true,
}) => {
  const variant = VARIANT_MAP[colorVariant];
  const [displayValue, setDisplayValue] = useState(0);
  const numericValue = typeof value === 'number' ? value : parseFloat(String(value)) || 0;
  const animRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (!animateCount || typeof value !== 'number') return;
    const duration = 900;
    const animate = (ts: number) => {
      if (!startRef.current) startRef.current = ts;
      const elapsed = ts - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.round(eased * numericValue));
      if (progress < 1) animRef.current = requestAnimationFrame(animate);
    };
    animRef.current = requestAnimationFrame(animate);
    return () => { if (animRef.current) cancelAnimationFrame(animRef.current); startRef.current = null; };
  }, [numericValue, animateCount, value]);

  const displayedValue = animateCount && typeof value === 'number' ? displayValue : value;
  const isPositiveTrend = trend !== undefined && trend >= 0;

  return (
    <div
      className="card"
      style={{
        padding: '20px 22px',
        boxShadow: variant.glow,
        borderColor: variant.border,
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        position: 'relative',
        overflow: 'hidden',
        cursor: 'default',
      }}
    >
      {/* Subtle background shape */}
      <div style={{
        position: 'absolute', top: '-20px', right: '-20px',
        width: '80px', height: '80px', borderRadius: '50%',
        background: variant.icon, opacity: 0.5,
        pointerEvents: 'none',
      }} />

      {/* Top row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          {label}
        </div>
        <div style={{
          width: '36px', height: '36px', borderRadius: '10px',
          background: variant.icon, color: variant.iconText,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          {icon}
        </div>
      </div>

      {/* Value */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
        <span style={{
          fontSize: '32px', fontWeight: 800, color: '#f1f5f9',
          animation: 'countUp 0.4s ease',
          lineHeight: 1, fontVariantNumeric: 'tabular-nums',
        }}>
          {displayedValue}
        </span>
        {suffix && (
          <span style={{ fontSize: '16px', fontWeight: 600, color: '#64748b' }}>{suffix}</span>
        )}
      </div>

      {/* Trend */}
      {trend !== undefined && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: '4px',
          fontSize: '12px', fontWeight: 600,
          color: isPositiveTrend ? '#34d399' : '#f87171',
        }}>
          {isPositiveTrend ? <TrendArrowUp /> : <TrendArrowDown />}
          <span>{Math.abs(trend)}%</span>
          {trendLabel && <span style={{ color: '#475569', fontWeight: 400 }}>{trendLabel}</span>}
        </div>
      )}

      {/* Bottom accent line */}
      <div style={{ height: '2px', borderRadius: '999px', background: `linear-gradient(90deg, ${variant.bar}, transparent)` }} />
    </div>
  );
};

export default StatsCard;
