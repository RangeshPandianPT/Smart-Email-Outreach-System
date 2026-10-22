import React, { useState } from 'react';

interface Campaign {
  id: number;
  name: string;
  status: 'Active' | 'Paused' | 'Draft' | 'Completed';
  sent: number;
  target: number;
  replies: number;
  createdAt: string;
}

// Mock campaigns — replace with real API data when ready
const MOCK_CAMPAIGNS: Campaign[] = [
  { id: 1, name: 'VFX Studios Q4 Outreach',     status: 'Active',    sent: 42, target: 80,  replies: 11, createdAt: '2026-10-15' },
  { id: 2, name: 'Post-Production Houses Wave 2', status: 'Active',    sent: 18, target: 50,  replies: 4,  createdAt: '2026-10-18' },
  { id: 3, name: 'Indie Filmmakers Promo',        status: 'Paused',    sent: 30, target: 60,  replies: 7,  createdAt: '2026-10-10' },
  { id: 4, name: 'Animation Studios Cold Email',  status: 'Draft',     sent: 0,  target: 40,  replies: 0,  createdAt: '2026-10-20' },
  { id: 5, name: 'Game Dev Studios Blast',        status: 'Completed', sent: 55, target: 55,  replies: 15, createdAt: '2026-10-01' },
];

const STATUS_MAP = {
  Active:    { color: '#34d399', bg: 'rgba(16,185,129,0.12)',    border: 'rgba(16,185,129,0.25)',   dot: '#10b981' },
  Paused:    { color: '#fbbf24', bg: 'rgba(245,158,11,0.12)',    border: 'rgba(245,158,11,0.25)',   dot: '#f59e0b' },
  Draft:     { color: '#94a3b8', bg: 'rgba(148,163,184,0.1)',    border: 'rgba(148,163,184,0.2)',   dot: '#64748b' },
  Completed: { color: '#60a5fa', bg: 'rgba(59,130,246,0.12)',    border: 'rgba(59,130,246,0.25)',   dot: '#3b82f6' },
};

const IconPlay = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <polygon points="5 3 19 12 5 21 5 3"/>
  </svg>
);
const IconPause = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/>
  </svg>
);
const IconPlus = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);
const IconTrash = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
    <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
  </svg>
);

export const CampaignPanel: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>(MOCK_CAMPAIGNS);
  const [filter, setFilter] = useState<'All' | Campaign['status']>('All');

  const toggleStatus = (id: number) => {
    setCampaigns(prev => prev.map(c => {
      if (c.id !== id) return c;
      return { ...c, status: c.status === 'Active' ? 'Paused' : c.status === 'Paused' ? 'Active' : c.status };
    }));
  };

  const filtered = filter === 'All' ? campaigns : campaigns.filter(c => c.status === filter);
  const FILTERS: Array<'All' | Campaign['status']> = ['All', 'Active', 'Paused', 'Draft', 'Completed'];

  return (
    <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>Campaigns</h2>
          <p style={{ fontSize: '13px', color: '#64748b', margin: '2px 0 0' }}>
            {campaigns.filter(c => c.status === 'Active').length} active · {campaigns.length} total
          </p>
        </div>
        <button className="btn-primary">
          <IconPlus /> New Campaign
        </button>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        {FILTERS.map(f => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              padding: '5px 14px', borderRadius: '999px', fontSize: '12px', fontWeight: 600,
              cursor: 'pointer', border: '1px solid', transition: 'all 0.2s',
              background: filter === f ? 'rgba(59,130,246,0.15)' : 'transparent',
              color: filter === f ? '#93c5fd' : '#64748b',
              borderColor: filter === f ? 'rgba(59,130,246,0.3)' : 'rgba(148,163,184,0.12)',
            }}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Campaign list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', padding: '32px', color: '#475569', fontSize: '14px' }}>
            No campaigns found.
          </div>
        )}
        {filtered.map(campaign => {
          const s = STATUS_MAP[campaign.status];
          const pct = campaign.target > 0 ? Math.min(Math.round((campaign.sent / campaign.target) * 100), 100) : 0;
          const replyRate = campaign.sent > 0 ? Math.round((campaign.replies / campaign.sent) * 100) : 0;

          return (
            <div
              key={campaign.id}
              style={{
                padding: '16px 18px',
                background: 'rgba(30,41,59,0.4)',
                border: '1px solid rgba(148,163,184,0.07)',
                borderRadius: '12px',
                display: 'flex', flexDirection: 'column', gap: '12px',
                transition: 'all 0.2s',
              }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(148,163,184,0.14)'; (e.currentTarget as HTMLDivElement).style.background = 'rgba(30,41,59,0.6)'; }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(148,163,184,0.07)'; (e.currentTarget as HTMLDivElement).style.background = 'rgba(30,41,59,0.4)'; }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '14px', fontWeight: 600, color: '#e2e8f0' }}>{campaign.name}</span>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: '5px',
                      padding: '2px 10px', borderRadius: '999px', fontSize: '11px', fontWeight: 600,
                      background: s.bg, color: s.color, border: `1px solid ${s.border}`,
                    }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: s.dot, flexShrink: 0 }} />
                      {campaign.status}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px' }}>Created {campaign.createdAt}</div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {/* Stats */}
                  <div style={{ display: 'flex', gap: '12px', marginRight: '4px' }}>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '16px', fontWeight: 700, color: '#f1f5f9' }}>{campaign.sent}</div>
                      <div style={{ fontSize: '10px', color: '#475569' }}>Sent</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '16px', fontWeight: 700, color: '#34d399' }}>{campaign.replies}</div>
                      <div style={{ fontSize: '10px', color: '#475569' }}>Replies</div>
                    </div>
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: '16px', fontWeight: 700, color: '#60a5fa' }}>{replyRate}%</div>
                      <div style={{ fontSize: '10px', color: '#475569' }}>Rate</div>
                    </div>
                  </div>

                  {/* Action buttons */}
                  {(campaign.status === 'Active' || campaign.status === 'Paused') && (
                    <button
                      onClick={() => toggleStatus(campaign.id)}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        width: '32px', height: '32px', borderRadius: '10px',
                        background: campaign.status === 'Active' ? 'rgba(245,158,11,0.12)' : 'rgba(16,185,129,0.12)',
                        border: `1px solid ${campaign.status === 'Active' ? 'rgba(245,158,11,0.3)' : 'rgba(16,185,129,0.3)'}`,
                        color: campaign.status === 'Active' ? '#fbbf24' : '#34d399',
                        cursor: 'pointer', transition: 'all 0.2s',
                      }}
                      title={campaign.status === 'Active' ? 'Pause' : 'Resume'}
                    >
                      {campaign.status === 'Active' ? <IconPause /> : <IconPlay />}
                    </button>
                  )}
                  <button
                    onClick={() => setCampaigns(prev => prev.filter(c => c.id !== campaign.id))}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      width: '32px', height: '32px', borderRadius: '10px',
                      background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                      color: '#f87171', cursor: 'pointer', transition: 'all 0.2s',
                    }}
                    title="Delete campaign"
                  >
                    <IconTrash />
                  </button>
                </div>
              </div>

              {/* Progress */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: '#475569' }}>Progress</span>
                  <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>{campaign.sent}/{campaign.target} sent ({pct}%)</span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{
                      width: `${pct}%`,
                      background: campaign.status === 'Completed'
                        ? 'linear-gradient(90deg, #10b981, #34d399)'
                        : 'linear-gradient(90deg, #3b82f6, #6366f1)',
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CampaignPanel;
