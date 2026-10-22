import React, { useEffect, useState, useMemo } from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line, Area, AreaChart,
} from 'recharts';

import { Sidebar }        from './components/Sidebar';
import { LeadModal }      from './components/LeadModal';
import { StatsCard }      from './components/StatsCard';
import { CampaignPanel }  from './components/CampaignPanel';
import { ActivityFeed }   from './components/ActivityFeed';

/* ─── Types ────────────────────────────────────────────────────────────── */
interface Lead {
  id: number; name: string; email: string; company: string;
  role: string; status: string; service_needed: string; deal_stage: string;
}
interface Summary {
  total_leads: number; pending_leads: number; drafted_leads: number;
  sent_leads: number; replied_leads: number;
}
interface Analytics {
  total_sent: number; total_replies: number; interested: number;
  conversion_rate: number; avg_response_time_hours: number; insights?: string[];
}

/* ─── Icon helpers ─────────────────────────────────────────────────────── */
const IconUsers    = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>;
const IconSend     = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2 11 13"/><path d="m22 2-7 20-4-9-9-4 20-7z"/></svg>;
const IconReply    = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 17 4 12 9 7"/><path d="M20 18v-2a4 4 0 0 0-4-4H4"/></svg>;
const IconPercent  = () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>;
const IconFilter   = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>;
const IconSearch   = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>;
const IconStar     = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="1"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>;
const IconEye      = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>;

/* ─── Status badge ─────────────────────────────────────────────────────── */
const STATUS_CLASS: Record<string, string> = {
  Pending: 'badge badge-pending', Drafted: 'badge badge-drafted',
  Sent:    'badge badge-sent',    Replied: 'badge badge-replied',
};

/* ─── Auth screen ──────────────────────────────────────────────────────── */
const AuthScreen: React.FC<{
  authMode: 'login' | 'signup'; setAuthMode: (m: 'login' | 'signup') => void;
  onSuccess: (token: string) => void;
}> = ({ authMode, setAuthMode, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      const body = new URLSearchParams();
      body.append('username', email); body.append('password', password);
      const endpoint = authMode === 'login' ? '/api/auth/login' : '/api/auth/signup';
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Authentication failed');
      if (authMode === 'login') { onSuccess(data.access_token); }
      else { setAuthMode('login'); setError('Account created! Please login.'); }
    } catch (err: any) { setError(err.message); }
    finally { setLoading(false); }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: '24px', position: 'relative', overflow: 'hidden',
    }}>
      {/* Decorative blobs */}
      <div style={{ position: 'fixed', top: '-200px', left: '-200px', width: '600px', height: '600px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(59,130,246,0.08) 0%, transparent 70%)', pointerEvents: 'none' }} />
      <div style={{ position: 'fixed', bottom: '-150px', right: '-150px', width: '500px', height: '500px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(16,185,129,0.06) 0%, transparent 70%)', pointerEvents: 'none' }} />

      <div style={{ width: '100%', maxWidth: '420px', animation: 'slideUp 0.4s ease' }}>
        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            width: '56px', height: '56px', borderRadius: '18px', margin: '0 auto 16px',
            background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '24px', fontWeight: 800, color: 'white',
            boxShadow: '0 8px 32px rgba(59,130,246,0.4)',
          }}>V</div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, margin: '0 0 6px', color: '#f1f5f9' }}>
            {authMode === 'login' ? 'Welcome back' : 'Get started'}
          </h1>
          <p style={{ color: '#64748b', fontSize: '14px', margin: 0 }}>
            {authMode === 'login' ? 'Sign in to VFX Outreach CRM' : 'Create your account'}
          </p>
        </div>

        <div className="card" style={{ padding: '28px' }}>
          {error && (
            <div style={{
              padding: '10px 14px', borderRadius: '10px', fontSize: '13px',
              background: error.includes('created') ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
              border: `1px solid ${error.includes('created') ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.25)'}`,
              color: error.includes('created') ? '#6ee7b7' : '#fca5a5',
              marginBottom: '20px',
            }}>{error}</div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Email</label>
              <input id="auth-email" type="email" value={email} onChange={e => setEmail(e.target.value)} className="input-field" placeholder="you@studio.com" required />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Password</label>
              <input id="auth-password" type="password" value={password} onChange={e => setPassword(e.target.value)} className="input-field" placeholder="••••••••" required />
            </div>
            <button id="auth-submit" type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: '4px', padding: '12px' }} disabled={loading}>
              {loading ? <span className="spinner" /> : (authMode === 'login' ? 'Sign In' : 'Create Account')}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '13px', color: '#475569' }}>
            {authMode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button onClick={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#60a5fa', fontWeight: 600, fontSize: '13px' }}>
              {authMode === 'login' ? 'Sign Up' : 'Login'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ─── Main App ─────────────────────────────────────────────────────────── */
function App() {
  const [token, setToken]         = useState<string | null>(localStorage.getItem('access_token'));
  const [leads, setLeads]         = useState<Lead[]>([]);
  const [summary, setSummary]     = useState<Summary | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading]     = useState(true);
  const [activeView, setActiveView] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [modalLeadId, setModalLeadId]   = useState<number | null>(null);
  const [authMode, setAuthMode]         = useState<'login' | 'signup'>('login');

  const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    const headers = new Headers(options.headers || {});
    if (token) headers.set('Authorization', `Bearer ${token}`);
    return fetch(url, { ...options, headers });
  };

  const handleLogout = () => { localStorage.removeItem('access_token'); setToken(null); };

  const handleAuthSuccess = (tok: string) => {
    localStorage.setItem('access_token', tok);
    setToken(tok);
  };

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    fetchWithAuth('http://localhost:8000/api/dashboard')
      .then(res => {
        if (res.status === 401) { handleLogout(); throw new Error('Unauthorized'); }
        return res.json();
      })
      .then(data => {
        setLeads(data.leads || []);
        setSummary(data.summary || null);
        setAnalytics(data.analytics || null);
        setLoading(false);
      })
      .catch(err => { console.error(err); setLoading(false); });
  }, [token]);

  /* Filtered leads */
  const filteredLeads = useMemo(() => {
    return leads.filter(l => {
      const matchesSearch = !searchQuery ||
        l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.company.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.email.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'All' || l.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [leads, searchQuery, statusFilter]);

  /* Auth */
  if (!token) {
    return <AuthScreen authMode={authMode} setAuthMode={setAuthMode} onSuccess={handleAuthSuccess} />;
  }

  /* Chart data */
  const pieData = summary ? [
    { name: 'Pending', value: summary.pending_leads },
    { name: 'Drafted', value: summary.drafted_leads },
    { name: 'Sent',    value: summary.sent_leads },
    { name: 'Replied', value: summary.replied_leads },
  ] : [];
  const PIE_COLORS = ['#f59e0b', '#a855f7', '#3b82f6', '#10b981'];

  const funnelData = summary ? [
    { name: 'Leads',      count: summary.total_leads },
    { name: 'Sent',       count: summary.sent_leads },
    { name: 'Replies',    count: analytics?.total_replies || 0 },
    { name: 'Interested', count: analytics?.interested || 0 },
  ] : [];

  const trendData = [
    { day: 'Mon', sent: 8,  replies: 2 },
    { day: 'Tue', sent: 14, replies: 4 },
    { day: 'Wed', sent: 11, replies: 3 },
    { day: 'Thu', sent: 19, replies: 7 },
    { day: 'Fri', sent: 16, replies: 5 },
    { day: 'Sat', sent: 6,  replies: 2 },
    { day: 'Sun', sent: 9,  replies: 3 },
  ];

  const userEmail = 'admin@vfxoutreach.com';

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar
        activeView={activeView}
        onNavigate={setActiveView}
        userEmail={userEmail}
        onLogout={handleLogout}
      />

      {/* Main content */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        {/* Top bar */}
        <div style={{
          padding: '16px 28px', borderBottom: '1px solid rgba(148,163,184,0.06)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px',
          background: 'rgba(9,14,28,0.6)', backdropFilter: 'blur(12px)',
          position: 'sticky', top: 0, zIndex: 30,
        }}>
          <div>
            <h1 style={{ fontSize: '20px', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
              {activeView === 'dashboard'  && '📊 Dashboard'}
              {activeView === 'leads'      && '👥 Leads'}
              {activeView === 'campaigns'  && '🚀 Campaigns'}
              {activeView === 'inbox'      && '📨 Inbox'}
              {activeView === 'analytics'  && '📈 Analytics'}
            </h1>
            <p style={{ fontSize: '12px', color: '#475569', margin: '2px 0 0' }}>
              {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {analytics?.insights && analytics.insights.length > 0 && (
              <div style={{
                padding: '6px 14px', borderRadius: '999px', fontSize: '12px', fontWeight: 600,
                background: 'rgba(16,185,129,0.1)', color: '#34d399', border: '1px solid rgba(16,185,129,0.2)',
                display: 'flex', alignItems: 'center', gap: '5px',
              }}>
                <IconStar /> {analytics.insights[0].substring(0, 40)}…
              </div>
            )}
          </div>
        </div>

        {/* Page content */}
        <div style={{ flex: 1, padding: '28px', display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
          {/* Left / main content */}
          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: '24px' }}>

            {/* ── DASHBOARD VIEW ── */}
            {activeView === 'dashboard' && (
              <>
                {/* Stats row */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                  <StatsCard label="Total Leads"    value={summary?.total_leads     ?? 0} icon={<IconUsers />}   colorVariant="blue"   trend={12} trendLabel="vs last wk" animateCount />
                  <StatsCard label="Emails Sent"    value={summary?.sent_leads      ?? 0} icon={<IconSend />}    colorVariant="purple" trend={8}  trendLabel="vs last wk" animateCount />
                  <StatsCard label="Replies"        value={analytics?.total_replies ?? 0} icon={<IconReply />}   colorVariant="green"  trend={5}  trendLabel="vs last wk" animateCount />
                  <StatsCard label="Conversion"     value={analytics?.conversion_rate ?? 0} suffix="%" icon={<IconPercent />} colorVariant="amber" trend={-2} trendLabel="vs last wk" animateCount />
                </div>

                {/* Charts row */}
                {!loading && (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                    {/* Pie */}
                    <div className="card" style={{ padding: '20px' }}>
                      <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8', margin: '0 0 16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Lead Status</h3>
                      <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                          <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={78} paddingAngle={4} dataKey="value">
                            {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                          </Pie>
                          <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(148,163,184,0.1)', borderRadius: '10px', color: '#f1f5f9' }} />
                        </PieChart>
                      </ResponsiveContainer>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 16px', marginTop: '12px' }}>
                        {pieData.map((d, i) => (
                          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>
                            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: PIE_COLORS[i], flexShrink: 0 }} />
                            <span style={{ color: '#94a3b8' }}>{d.name}</span>
                            <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{d.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Area trend */}
                    <div className="card" style={{ padding: '20px' }}>
                      <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8', margin: '0 0 16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Weekly Trend</h3>
                      <ResponsiveContainer width="100%" height={200}>
                        <AreaChart data={trendData}>
                          <defs>
                            <linearGradient id="gradSent" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                            </linearGradient>
                            <linearGradient id="gradReplies" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                              <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.06)" vertical={false} />
                          <XAxis dataKey="day" stroke="#475569" tick={{ fill: '#475569', fontSize: 11 }} axisLine={false} tickLine={false} />
                          <YAxis stroke="#475569" tick={{ fill: '#475569', fontSize: 11 }} axisLine={false} tickLine={false} />
                          <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(148,163,184,0.1)', borderRadius: '10px', color: '#f1f5f9' }} />
                          <Area type="monotone" dataKey="sent"    stroke="#3b82f6" strokeWidth={2} fill="url(#gradSent)"    dot={false} />
                          <Area type="monotone" dataKey="replies" stroke="#10b981" strokeWidth={2} fill="url(#gradReplies)" dot={false} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Insights */}
                {analytics?.insights && analytics.insights.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {analytics.insights.map((insight, i) => (
                      <div key={i} style={{
                        padding: '12px 16px', borderRadius: '12px',
                        background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
                        fontSize: '13px', color: '#6ee7b7', display: 'flex', alignItems: 'center', gap: '8px',
                      }}>
                        <span>💡</span> {insight}
                      </div>
                    ))}
                  </div>
                )}

                {/* Recent leads preview */}
                <div className="card" style={{ padding: '22px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                    <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>Recent Leads</h3>
                    <button onClick={() => setActiveView('leads')} style={{ background: 'none', border: 'none', color: '#60a5fa', cursor: 'pointer', fontSize: '13px', fontWeight: 600 }}>View all →</button>
                  </div>
                  {loading ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {[1,2,3].map(i => <div key={i} className="skeleton" style={{ height: '48px', borderRadius: '10px' }} />)}
                    </div>
                  ) : (
                    leads.slice(0, 5).map(lead => (
                      <div key={lead.id}
                        onClick={() => setModalLeadId(lead.id)}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 0',
                          borderBottom: '1px solid rgba(148,163,184,0.06)', cursor: 'pointer',
                          transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.paddingLeft = '8px'; }}
                        onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.paddingLeft = '0'; }}
                      >
                        <div style={{
                          width: '36px', height: '36px', borderRadius: '10px', flexShrink: 0,
                          background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '13px', fontWeight: 700, color: 'white',
                        }}>{lead.name.charAt(0)}</div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{lead.name}</div>
                          <div style={{ fontSize: '11px', color: '#475569' }}>{lead.company}</div>
                        </div>
                        <span className={STATUS_CLASS[lead.status] || 'badge'}>{lead.status}</span>
                        <span style={{ color: '#334155', opacity: 0.6 }}><IconEye /></span>
                      </div>
                    ))
                  )}
                </div>
              </>
            )}

            {/* ── LEADS VIEW ── */}
            {activeView === 'leads' && (
              <div className="card" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
                  <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9', margin: 0 }}>
                    All Leads <span style={{ fontSize: '13px', color: '#475569', fontWeight: 400 }}>({filteredLeads.length})</span>
                  </h2>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
                    {/* Search */}
                    <div style={{ position: 'relative' }}>
                      <span style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#475569' }}><IconSearch /></span>
                      <input
                        value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                        className="input-field" placeholder="Search leads…"
                        style={{ paddingLeft: '32px', width: '200px' }}
                      />
                    </div>
                    {/* Status filter */}
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {['All','Pending','Drafted','Sent','Replied'].map(s => (
                        <button key={s} onClick={() => setStatusFilter(s)} style={{
                          padding: '5px 12px', borderRadius: '8px', fontSize: '12px', fontWeight: 600, cursor: 'pointer',
                          background: statusFilter === s ? 'rgba(59,130,246,0.15)' : 'transparent',
                          color: statusFilter === s ? '#93c5fd' : '#64748b',
                          border: `1px solid ${statusFilter === s ? 'rgba(59,130,246,0.3)' : 'transparent'}`,
                          transition: 'all 0.15s',
                        }}>{s}</button>
                      ))}
                    </div>
                  </div>
                </div>

                {loading ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: '60px', borderRadius: '10px' }} />)}
                  </div>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(148,163,184,0.08)' }}>
                          {['Lead', 'Email', 'Service', 'Stage', 'Status', ''].map(h => (
                            <th key={h} style={{ padding: '10px 12px', textAlign: 'left', fontSize: '11px', fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {filteredLeads.map(lead => (
                          <tr key={lead.id}
                            style={{ borderBottom: '1px solid rgba(148,163,184,0.05)', cursor: 'pointer', transition: 'background 0.15s' }}
                            onMouseEnter={e => { (e.currentTarget as HTMLTableRowElement).style.background = 'rgba(148,163,184,0.04)'; }}
                            onMouseLeave={e => { (e.currentTarget as HTMLTableRowElement).style.background = 'transparent'; }}
                          >
                            <td style={{ padding: '12px' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                <div style={{ width: '32px', height: '32px', borderRadius: '10px', background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', fontWeight: 700, color: 'white', flexShrink: 0 }}>
                                  {lead.name.charAt(0)}
                                </div>
                                <div>
                                  <div style={{ fontSize: '13px', fontWeight: 600, color: '#e2e8f0' }}>{lead.name}</div>
                                  <div style={{ fontSize: '11px', color: '#475569' }}>{lead.company}</div>
                                </div>
                              </div>
                            </td>
                            <td style={{ padding: '12px' }}>
                              <a href={`mailto:${lead.email}`} style={{ color: '#60a5fa', fontSize: '12px', textDecoration: 'none' }} onClick={e => e.stopPropagation()}>{lead.email}</a>
                            </td>
                            <td style={{ padding: '12px', fontSize: '13px', color: '#94a3b8' }}>{lead.service_needed}</td>
                            <td style={{ padding: '12px', fontSize: '12px', color: '#64748b' }}>{lead.deal_stage || '—'}</td>
                            <td style={{ padding: '12px' }}>
                              <span className={STATUS_CLASS[lead.status] || 'badge'}>{lead.status}</span>
                            </td>
                            <td style={{ padding: '12px' }}>
                              <button onClick={() => setModalLeadId(lead.id)} style={{ display: 'flex', alignItems: 'center', gap: '4px', background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '8px', padding: '4px 10px', color: '#93c5fd', cursor: 'pointer', fontSize: '12px', fontWeight: 600, transition: 'all 0.15s' }}>
                                <IconEye /> View
                              </button>
                            </td>
                          </tr>
                        ))}
                        {filteredLeads.length === 0 && (
                          <tr><td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: '#475569' }}>No leads match your filters.</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* ── CAMPAIGNS VIEW ── */}
            {activeView === 'campaigns' && <CampaignPanel />}

            {/* ── ANALYTICS VIEW ── */}
            {activeView === 'analytics' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                  <StatsCard label="Total Sent"     value={analytics?.total_sent     ?? 0} icon={<IconSend />}    colorVariant="blue"   animateCount />
                  <StatsCard label="Total Replies"  value={analytics?.total_replies  ?? 0} icon={<IconReply />}   colorVariant="green"  animateCount />
                  <StatsCard label="Interested"     value={analytics?.interested     ?? 0} icon={<IconStar />}    colorVariant="amber"  animateCount />
                  <StatsCard label="Conversion Rate" value={analytics?.conversion_rate ?? 0} suffix="%" icon={<IconPercent />} colorVariant="purple" animateCount />
                </div>
                <div className="card" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8', margin: '0 0 16px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Engagement Funnel</h3>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={funnelData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.06)" vertical={false} />
                      <XAxis dataKey="name" stroke="#475569" tick={{ fill: '#475569', fontSize: 12 }} axisLine={false} tickLine={false} />
                      <YAxis stroke="#475569" tick={{ fill: '#475569', fontSize: 12 }} axisLine={false} tickLine={false} />
                      <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid rgba(148,163,184,0.1)', borderRadius: '10px', color: '#f1f5f9' }} cursor={{ fill: 'rgba(148,163,184,0.05)' }} />
                      <Bar dataKey="count" radius={[6,6,0,0]}>
                        {funnelData.map((_, i) => <Cell key={i} fill={['#3b82f6','#6366f1','#10b981','#f59e0b'][i]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* ── INBOX VIEW ── */}
            {activeView === 'inbox' && (
              <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📨</div>
                <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#f1f5f9', margin: '0 0 8px' }}>Inbox</h2>
                <p style={{ color: '#64748b', margin: 0 }}>Connect your Gmail account to view replies here.</p>
              </div>
            )}
          </div>

          {/* Right sidebar: Activity Feed */}
          <div style={{ width: '300px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <ActivityFeed maxVisible={8} />
          </div>
        </div>
      </div>

      {/* Lead modal */}
      <LeadModal
        leadId={modalLeadId}
        isOpen={modalLeadId !== null}
        onClose={() => setModalLeadId(null)}
        fetchWithAuth={fetchWithAuth}
      />
    </div>
  );
}

export default App;
