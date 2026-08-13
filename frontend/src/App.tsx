import React, { useEffect, useState, useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

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

interface Summary {
  total_leads: number;
  pending_leads: number;
  drafted_leads: number;
  sent_leads: number;
  replied_leads: number;
}

interface Analytics {
  total_sent: number;
  total_replies: number;
  interested: number;
  conversion_rate: number;
  avg_response_time_hours: number;
  insights?: string[];
}

function App() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/dashboard')
      .then(res => res.json())
      .then(data => {
        setLeads(data.leads || []);
        setSummary(data.summary || null);
        setAnalytics(data.analytics || null);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch dashboard data', err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10 flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
              VFX Outreach Dashboard
            </h1>
            <p className="text-slate-400 mt-2">Manage your CRM, automate emails, and track performance.</p>
          </div>
          <button className="btn-primary">
            + New Campaign
          </button>
        </header>

        {summary && !loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="card p-6 h-64">
              <h3 className="text-lg font-medium text-white mb-4">Lead Status Distribution</h3>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Pending', value: summary.pending_leads },
                      { name: 'Drafted', value: summary.drafted_leads },
                      { name: 'Sent', value: summary.sent_leads },
                      { name: 'Replied', value: summary.replied_leads }
                    ]}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    <Cell fill="#facc15" /> {/* Yellow for Pending */}
                    <Cell fill="#a855f7" /> {/* Purple for Drafted */}
                    <Cell fill="#3b82f6" /> {/* Blue for Sent */}
                    <Cell fill="#10b981" /> {/* Emerald for Replied */}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '0.5rem', color: '#f8fafc' }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            <div className="card p-6 h-64">
              <h3 className="text-lg font-medium text-white mb-4">Engagement Funnel</h3>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { name: 'Total Leads', count: summary.total_leads },
                  { name: 'Sent Emails', count: summary.sent_leads },
                  { name: 'Replies', count: analytics?.total_replies || 0 },
                  { name: 'Interested', count: analytics?.interested || 0 }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                  <YAxis stroke="#94a3b8" tick={{fill: '#94a3b8'}} axisLine={false} tickLine={false} />
                  <Tooltip 
                    cursor={{fill: '#334155'}}
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '0.5rem', color: '#f8fafc' }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-4 mb-8">
          <div className="card p-5">
            <div className="text-slate-400 text-sm">Total Leads</div>
            <div className="text-2xl font-semibold text-white mt-2">{summary?.total_leads ?? 0}</div>
          </div>
          <div className="card p-5">
            <div className="text-slate-400 text-sm">Pending</div>
            <div className="text-2xl font-semibold text-white mt-2">{summary?.pending_leads ?? 0}</div>
          </div>
          <div className="card p-5">
            <div className="text-slate-400 text-sm">Sent</div>
            <div className="text-2xl font-semibold text-white mt-2">{summary?.sent_leads ?? 0}</div>
          </div>
          <div className="card p-5">
            <div className="text-slate-400 text-sm">Replies</div>
            <div className="text-2xl font-semibold text-white mt-2">{analytics?.total_replies ?? 0}</div>
          </div>
        </div>

        <main className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-white">Active Leads</h2>
            <div className="text-sm text-slate-400">Conversion rate: {analytics?.conversion_rate ?? 0}%</div>
          </div>

          {loading ? (
            <div className="text-center py-10 text-slate-400 animate-pulse">Loading dashboard...</div>
          ) : (
            <div className="space-y-4">
              {analytics?.insights?.map((insight) => (
                <div key={insight} className="rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm text-emerald-300">
                  {insight}
                </div>
              ))}

              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-700 text-slate-400">
                      <th className="py-3 font-medium">Lead Details</th>
                      <th className="py-3 font-medium">Email</th>
                      <th className="py-3 font-medium">Service</th>
                      <th className="py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leads.map((lead) => (
                      <tr key={lead.id} className="border-b border-slate-800 hover:bg-slate-800/50 transition-colors">
                        <td className="py-4">
                          <div className="font-semibold text-white">{lead.name}</div>
                          <div className="text-sm text-slate-400">{lead.company} ({lead.role})</div>
                        </td>
                        <td className="py-4">
                          <a href={`mailto:${lead.email}`} className="text-blue-400 hover:underline">{lead.email}</a>
                        </td>
                        <td className="py-4 text-slate-300">{lead.service_needed}</td>
                        <td className="py-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-medium tracking-wide
                            ${lead.status === 'Pending' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30' :
                            lead.status === 'Sent' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                            lead.status === 'Drafted' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                            'bg-slate-700 text-slate-300'}`}>
                            {lead.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {leads.length === 0 && (
                      <tr>
                        <td colSpan={4} className="py-10 text-center text-slate-500">
                          No leads found. Start by importing a CSV.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
