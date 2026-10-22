import React, { useEffect, useRef, useState } from 'react';

interface ActivityEvent {
  id: number;
  type: 'email_sent' | 'reply_received' | 'lead_added' | 'draft_created' | 'campaign_started' | 'interested';
  title: string;
  subtitle: string;
  timestamp: string;
  isNew?: boolean;
}

const MOCK_EVENTS: ActivityEvent[] = [
  { id: 1,  type: 'reply_received',   title: 'Reply from Marcus Chen',       subtitle: 'Interested in VFX pipeline work',   timestamp: '2 min ago',   isNew: true },
  { id: 2,  type: 'email_sent',       title: 'Email sent to Priya Sharma',   subtitle: 'Q4 Outreach Campaign',              timestamp: '8 min ago',   isNew: true },
  { id: 3,  type: 'interested',       title: 'Hot lead: Studio Nexus',        subtitle: 'Responded positively to outreach',  timestamp: '15 min ago',  isNew: true },
  { id: 4,  type: 'lead_added',       title: '3 new leads imported',          subtitle: 'From animation_studios.csv',        timestamp: '1 hr ago' },
  { id: 5,  type: 'draft_created',    title: 'Draft created for Yumi Tanaka', subtitle: 'AI-generated personalized email',   timestamp: '2 hr ago' },
  { id: 6,  type: 'campaign_started', title: 'Campaign launched',             subtitle: 'VFX Studios Q4 Outreach (80 leads)', timestamp: '3 hr ago' },
  { id: 7,  type: 'email_sent',       title: 'Batch: 12 emails sent',         subtitle: 'Post-Production Houses Wave 2',     timestamp: '5 hr ago' },
  { id: 8,  type: 'reply_received',   title: 'Reply from Jake Morrison',      subtitle: 'Requested a callback',             timestamp: '6 hr ago' },
];

const EVENT_CONFIG: Record<ActivityEvent['type'], { icon: string; bg: string; color: string }> = {
  email_sent:       { icon: '📤', bg: 'rgba(59,130,246,0.12)',   color: '#60a5fa' },
  reply_received:   { icon: '📨', bg: 'rgba(16,185,129,0.12)',   color: '#34d399' },
  lead_added:       { icon: '👤', bg: 'rgba(168,85,247,0.12)',   color: '#c084fc' },
  draft_created:    { icon: '✍️', bg: 'rgba(245,158,11,0.12)',   color: '#fbbf24' },
  campaign_started: { icon: '🚀', bg: 'rgba(99,102,241,0.12)',   color: '#a5b4fc' },
  interested:       { icon: '🔥', bg: 'rgba(239,68,68,0.12)',    color: '#f87171' },
};

interface ActivityFeedProps {
  maxVisible?: number;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ maxVisible = 8 }) => {
  const [events, setEvents] = useState<ActivityEvent[]>(MOCK_EVENTS.slice(0, maxVisible));
  const [showAll, setShowAll] = useState(false);
  const [liveCount, setLiveCount] = useState(0);
  const intervalRef = useRef<number | null>(null);

  // Simulate a new live event arriving every 30 seconds
  useEffect(() => {
    intervalRef.current = window.setInterval(() => {
      setLiveCount(n => n + 1);
    }, 30000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  const visible = showAll ? events : events.slice(0, 5);
  const newCount = events.filter(e => e.isNew).length;

  return (
    <div className="card" style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>Activity Feed</h3>
          {newCount > 0 && (
            <div style={{ fontSize: '12px', color: '#34d399', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span className="pulse-dot" />
              {newCount} new event{newCount > 1 ? 's' : ''}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {liveCount > 0 && (
            <span style={{
              padding: '2px 8px', borderRadius: '999px', fontSize: '10px', fontWeight: 700,
              background: 'rgba(16,185,129,0.15)', color: '#34d399', border: '1px solid rgba(16,185,129,0.25)',
            }}>
              +{liveCount} LIVE
            </span>
          )}
          <button
            onClick={() => setEvents(prev => prev.map(e => ({ ...e, isNew: false })))}
            style={{
              background: 'none', border: 'none', color: '#475569', cursor: 'pointer',
              fontSize: '11px', fontWeight: 600, padding: '4px 8px', borderRadius: '8px',
              transition: 'all 0.2s',
            }}
          >
            Mark all read
          </button>
        </div>
      </div>

      {/* Events */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {visible.map((event, idx) => {
          const cfg = EVENT_CONFIG[event.type];
          return (
            <div
              key={event.id}
              className="activity-item"
              style={{
                background: event.isNew ? 'rgba(59,130,246,0.03)' : 'transparent',
                borderRadius: '8px',
                paddingLeft: event.isNew ? '8px' : '0',
                marginLeft: event.isNew ? '-8px' : '0',
                marginRight: event.isNew ? '-8px' : '0',
                animationDelay: `${idx * 40}ms`,
              }}
            >
              {/* Icon */}
              <div style={{
                width: '34px', height: '34px', borderRadius: '10px',
                background: cfg.bg, display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '15px', flexShrink: 0,
              }}>
                {cfg.icon}
              </div>

              {/* Content */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>{event.title}</span>
                  {event.isNew && (
                    <span style={{
                      fontSize: '9px', fontWeight: 700, padding: '1px 5px', borderRadius: '4px',
                      background: 'rgba(59,130,246,0.2)', color: '#93c5fd', letterSpacing: '0.05em',
                    }}>NEW</span>
                  )}
                </div>
                <div style={{ fontSize: '12px', color: '#475569', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {event.subtitle}
                </div>
              </div>

              {/* Timestamp */}
              <div style={{ fontSize: '11px', color: '#334155', fontWeight: 500, flexShrink: 0, alignSelf: 'flex-start', paddingTop: '2px' }}>
                {event.timestamp}
              </div>
            </div>
          );
        })}
      </div>

      {/* Show more */}
      {events.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          style={{
            width: '100%', padding: '8px', background: 'rgba(148,163,184,0.05)',
            border: '1px solid rgba(148,163,184,0.08)', borderRadius: '10px',
            color: '#64748b', cursor: 'pointer', fontSize: '13px', fontWeight: 600,
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => { (e.target as HTMLButtonElement).style.color = '#94a3b8'; }}
          onMouseLeave={e => { (e.target as HTMLButtonElement).style.color = '#64748b'; }}
        >
          {showAll ? '↑ Show less' : `↓ Show ${events.length - 5} more`}
        </button>
      )}
    </div>
  );
};

export default ActivityFeed;
