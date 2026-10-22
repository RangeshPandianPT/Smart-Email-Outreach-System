import React, { useEffect, useState } from 'react';

interface Lead {
  id: number;
  name: string;
  email: string;
  company: string;
  role: string;
  status: string;
  service_needed: string;
  deal_stage: string;
}

interface LeadDetails {
  lead: Lead;
  draft: { subject: string; body: string } | null;
}

interface LeadModalProps {
  leadId: number | null;
  isOpen: boolean;
  onClose: () => void;
  fetchWithAuth: (url: string, options?: RequestInit) => Promise<Response>;
}

const IconClose = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);
const IconMail = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 7L2 7"/>
  </svg>
);
const IconBuilding = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 21V7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14"/>
    <path d="M9 21V11h6v10"/><path d="M3 7h18"/>
  </svg>
);
const IconBriefcase = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
    <line x1="12" y1="12" x2="12" y2="12"/>
  </svg>
);
const IconSend = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 2 11 13"/><path d="m22 2-7 20-4-9-9-4 20-7z"/>
  </svg>
);
const IconCopy = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
  </svg>
);

const STATUS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  Pending:  { bg: 'rgba(245,158,11,0.12)',  text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
  Drafted:  { bg: 'rgba(168,85,247,0.12)',  text: '#d8b4fe', border: 'rgba(168,85,247,0.25)' },
  Sent:     { bg: 'rgba(59,130,246,0.12)',  text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
  Replied:  { bg: 'rgba(16,185,129,0.12)',  text: '#6ee7b7', border: 'rgba(16,185,129,0.25)' },
};

const DEAL_STAGES = ['Prospecting', 'Qualified', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'];

export const LeadModal: React.FC<LeadModalProps> = ({ leadId, isOpen, onClose, fetchWithAuth }) => {
  const [details, setDetails] = useState<LeadDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'email'>('overview');

  useEffect(() => {
    if (!leadId || !isOpen) return;
    setLoading(true);
    setDetails(null);
    setActiveTab('overview');
    fetchWithAuth(`http://localhost:8000/api/leads/${leadId}`)
      .then(r => r.json())
      .then(d => setDetails(d))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [leadId, isOpen]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [onClose]);

  if (!isOpen) return null;

  const statusStyle = details?.lead?.status ? STATUS_COLORS[details.lead.status] ?? {} : {};
  const draftStageIndex = details?.lead?.deal_stage
    ? DEAL_STAGES.findIndex(s => s === details.lead.deal_stage)
    : -1;

  const copyEmail = () => {
    if (details?.draft) {
      navigator.clipboard.writeText(`Subject: ${details.draft.subject}\n\n${details.draft.body}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{
          padding: '24px 28px 20px',
          borderBottom: '1px solid rgba(148,163,184,0.08)',
          display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px',
        }}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
              <div className="skeleton" style={{ height: '28px', width: '55%' }} />
              <div className="skeleton" style={{ height: '16px', width: '40%' }} />
            </div>
          ) : details ? (
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                <div style={{
                  width: '44px', height: '44px', borderRadius: '14px',
                  background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '18px', fontWeight: 700, color: 'white', flexShrink: 0,
                }}>
                  {details.lead.name.charAt(0)}
                </div>
                <div>
                  <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                    {details.lead.name}
                  </h2>
                  <div style={{ fontSize: '13px', color: '#64748b', marginTop: '2px' }}>
                    {details.lead.role} at {details.lead.company}
                  </div>
                </div>
                <span style={{
                  padding: '3px 12px', borderRadius: '999px', fontSize: '12px', fontWeight: 600,
                  background: statusStyle.bg, color: statusStyle.text, border: `1px solid ${statusStyle.border}`,
                }}>
                  {details.lead.status}
                </span>
              </div>
            </div>
          ) : null}
          <button onClick={onClose} style={{
            background: 'rgba(148,163,184,0.08)', border: '1px solid rgba(148,163,184,0.1)',
            borderRadius: '10px', padding: '8px', color: '#64748b', cursor: 'pointer',
            display: 'flex', transition: 'all 0.2s', flexShrink: 0,
          }}>
            <IconClose />
          </button>
        </div>

        {/* Tabs */}
        <div style={{ padding: '0 28px', borderBottom: '1px solid rgba(148,163,184,0.08)', display: 'flex', gap: '0' }}>
          {(['overview', 'email'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: '12px 20px', background: 'none', border: 'none', cursor: 'pointer',
                fontSize: '13px', fontWeight: 600, textTransform: 'capitalize',
                color: activeTab === tab ? '#60a5fa' : '#64748b',
                borderBottom: activeTab === tab ? '2px solid #60a5fa' : '2px solid transparent',
                transition: 'all 0.2s', marginBottom: '-1px',
              }}
            >
              {tab === 'email' ? '📧 Email Draft' : '📋 Overview'}
            </button>
          ))}
        </div>

        {/* Body */}
        <div style={{ padding: '24px 28px' }}>
          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[60, 80, 45, 70].map((w, i) => (
                <div key={i} className="skeleton" style={{ height: '16px', width: `${w}%` }} />
              ))}
            </div>
          ) : !details ? (
            <div style={{ textAlign: 'center', color: '#64748b', padding: '40px 0' }}>
              Failed to load lead details.
            </div>
          ) : activeTab === 'overview' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Info grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                {[
                  { icon: <IconMail />, label: 'Email', value: details.lead.email },
                  { icon: <IconBuilding />, label: 'Company', value: details.lead.company },
                  { icon: <IconBriefcase />, label: 'Role', value: details.lead.role },
                  { icon: <IconSend />, label: 'Service Needed', value: details.lead.service_needed },
                ].map(({ icon, label, value }) => (
                  <div key={label} style={{
                    padding: '14px 16px', background: 'rgba(30,41,59,0.5)',
                    border: '1px solid rgba(148,163,184,0.08)', borderRadius: '12px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#64748b', fontSize: '11px', fontWeight: 600, marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      {icon} {label}
                    </div>
                    <div style={{ fontSize: '13px', color: '#e2e8f0', fontWeight: 500 }}>{value || '—'}</div>
                  </div>
                ))}
              </div>

              {/* Deal stage pipeline */}
              <div style={{ padding: '16px 20px', background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(148,163,184,0.08)', borderRadius: '12px' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '14px' }}>
                  Deal Pipeline
                </div>
                <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                  {DEAL_STAGES.map((stage, idx) => {
                    const isPast = idx <= draftStageIndex;
                    const isActive = idx === draftStageIndex;
                    return (
                      <React.Fragment key={stage}>
                        <div style={{
                          flex: 1, textAlign: 'center', padding: '6px 4px',
                          background: isActive ? 'rgba(59,130,246,0.2)' : isPast ? 'rgba(16,185,129,0.1)' : 'rgba(30,41,59,0.6)',
                          border: `1px solid ${isActive ? 'rgba(59,130,246,0.4)' : isPast ? 'rgba(16,185,129,0.2)' : 'rgba(148,163,184,0.06)'}`,
                          borderRadius: '8px', fontSize: '10px', fontWeight: 600,
                          color: isActive ? '#93c5fd' : isPast ? '#6ee7b7' : '#475569',
                          transition: 'all 0.3s',
                        }}>
                          {stage.split(' ')[0]}
                        </div>
                        {idx < DEAL_STAGES.length - 1 && (
                          <div style={{ width: '8px', height: '1px', background: isPast ? 'rgba(16,185,129,0.4)' : 'rgba(148,163,184,0.1)', flexShrink: 0 }} />
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            /* Email Draft Tab */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {details.draft ? (
                <>
                  <div style={{ padding: '14px 16px', background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(148,163,184,0.08)', borderRadius: '12px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '6px' }}>Subject</div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: '#e2e8f0' }}>{details.draft.subject}</div>
                  </div>
                  <div style={{ padding: '16px', background: 'rgba(30,41,59,0.5)', border: '1px solid rgba(148,163,184,0.08)', borderRadius: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <div style={{ fontSize: '11px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Email Body</div>
                      <button onClick={copyEmail} style={{
                        display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(59,130,246,0.1)',
                        border: '1px solid rgba(59,130,246,0.2)', borderRadius: '8px', padding: '4px 10px',
                        color: copied ? '#6ee7b7' : '#93c5fd', cursor: 'pointer', fontSize: '12px', fontWeight: 600, transition: 'all 0.2s',
                      }}>
                        <IconCopy /> {copied ? 'Copied!' : 'Copy'}
                      </button>
                    </div>
                    <pre style={{
                      whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: '13px',
                      color: '#cbd5e1', lineHeight: 1.7, margin: 0, fontFamily: 'inherit',
                    }}>
                      {details.draft.body}
                    </pre>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <button className="btn-primary" style={{ flex: 1, justifyContent: 'center' }}>
                      <IconSend /> Send Email
                    </button>
                    <button style={{
                      flex: 1, padding: '10px', background: 'rgba(148,163,184,0.06)',
                      border: '1px solid rgba(148,163,184,0.1)', borderRadius: '12px',
                      color: '#94a3b8', cursor: 'pointer', fontWeight: 600, fontSize: '14px', transition: 'all 0.2s',
                    }}>
                      Edit Draft
                    </button>
                  </div>
                </>
              ) : (
                <div style={{
                  textAlign: 'center', padding: '40px 20px',
                  background: 'rgba(30,41,59,0.4)', border: '1px dashed rgba(148,163,184,0.15)', borderRadius: '12px',
                }}>
                  <div style={{ fontSize: '32px', marginBottom: '12px' }}>✍️</div>
                  <div style={{ color: '#94a3b8', fontWeight: 600, marginBottom: '8px' }}>No draft yet</div>
                  <div style={{ color: '#475569', fontSize: '13px', marginBottom: '16px' }}>Generate a personalized email for this lead</div>
                  <button className="btn-primary" style={{ margin: '0 auto' }}>
                    Generate Draft
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LeadModal;
