import React, { useState } from 'react';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  badge?: number;
}

interface SidebarProps {
  activeView: string;
  onNavigate: (view: string) => void;
  userEmail: string;
  onLogout: () => void;
}

const IconDashboard = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
    <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
  </svg>
);
const IconUsers = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
);
const IconMail = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 7l-10 7L2 7"/>
  </svg>
);
const IconBarChart = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6" y1="20" x2="6" y2="14"/><line x1="2" y1="20" x2="22" y2="20"/>
  </svg>
);
const IconCampaign = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 2 11 13"/><path d="m22 2-7 20-4-9-9-4 20-7z"/>
  </svg>
);
const IconSettings = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14M12 2v2m0 16v2M2 12h2m16 0h2"/>
  </svg>
);
const IconLogout = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
);
const IconChevron = ({ collapsed }: { collapsed: boolean }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    style={{ transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }}>
    <polyline points="15 18 9 12 15 6"/>
  </svg>
);

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard',  label: 'Dashboard',   icon: <IconDashboard /> },
  { id: 'leads',      label: 'Leads',        icon: <IconUsers /> },
  { id: 'campaigns',  label: 'Campaigns',    icon: <IconCampaign /> },
  { id: 'inbox',      label: 'Inbox',        icon: <IconMail /> },
  { id: 'analytics',  label: 'Analytics',    icon: <IconBarChart /> },
];

export const Sidebar: React.FC<SidebarProps> = ({ activeView, onNavigate, userEmail, onLogout }) => {
  const [collapsed, setCollapsed] = useState(false);
  const initials = userEmail ? userEmail.slice(0, 2).toUpperCase() : 'VX';

  return (
    <aside style={{
      width: collapsed ? '72px' : '240px',
      transition: 'width 0.3s cubic-bezier(0.4,0,0.2,1)',
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: 'rgba(9, 14, 28, 0.85)',
      borderRight: '1px solid rgba(148,163,184,0.06)',
      backdropFilter: 'blur(20px)',
      position: 'sticky',
      top: 0,
      flexShrink: 0,
      zIndex: 40,
    }}>
      {/* Logo */}
      <div style={{ padding: '20px 16px 16px', display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between', gap: '10px' }}>
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '10px',
              background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 4px 12px rgba(59,130,246,0.4)',
              fontSize: '14px', fontWeight: 700, color: 'white',
            }}>V</div>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9', lineHeight: 1 }}>VFX Outreach</div>
              <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>CRM Platform</div>
            </div>
          </div>
        )}
        {collapsed && (
          <div style={{
            width: '32px', height: '32px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '14px', fontWeight: 700, color: 'white',
          }}>V</div>
        )}
        <button onClick={() => setCollapsed(!collapsed)} style={{
          background: 'rgba(148,163,184,0.06)', border: '1px solid rgba(148,163,184,0.1)',
          borderRadius: '8px', padding: '4px', color: '#64748b',
          cursor: 'pointer', display: 'flex', alignItems: 'center', transition: 'all 0.2s', flexShrink: 0,
        }}>
          <IconChevron collapsed={collapsed} />
        </button>
      </div>

      <hr style={{ border: 'none', borderTop: '1px solid rgba(148,163,184,0.06)', margin: '0 12px 12px' }} />

      {/* Live indicator */}
      {!collapsed ? (
        <div style={{ padding: '0 16px 12px' }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px',
            background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '10px',
          }}>
            <span className="pulse-dot" />
            <span style={{ fontSize: '11px', color: '#6ee7b7', fontWeight: 500 }}>System Online</span>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', justifyContent: 'center', paddingBottom: '12px' }}>
          <span className="pulse-dot" />
        </div>
      )}

      {/* Nav */}
      <nav style={{ flex: 1, padding: '0 8px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`nav-item ${activeView === item.id ? 'active' : ''}`}
            title={collapsed ? item.label : undefined}
            style={{
              width: '100%',
              border: activeView === item.id ? undefined : '1px solid transparent',
              justifyContent: collapsed ? 'center' : 'flex-start',
            }}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && <span style={{ flex: 1, textAlign: 'left' }}>{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Bottom section */}
      <div style={{ padding: '8px', marginTop: 'auto' }}>
        <hr style={{ border: 'none', borderTop: '1px solid rgba(148,163,184,0.06)', margin: '0 4px 8px' }} />
        <button className="nav-item" title={collapsed ? 'Settings' : undefined} style={{ width: '100%', justifyContent: collapsed ? 'center' : 'flex-start', border: '1px solid transparent' }}>
          <IconSettings />
          {!collapsed && <span>Settings</span>}
        </button>

        <div style={{
          margin: '8px 0 4px', padding: collapsed ? '8px' : '10px 12px',
          background: 'rgba(148,163,184,0.05)', border: '1px solid rgba(148,163,184,0.08)',
          borderRadius: '12px', display: 'flex', alignItems: 'center',
          gap: collapsed ? 0 : '10px', justifyContent: collapsed ? 'center' : 'flex-start',
        }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #6366f1, #a78bfa)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '12px', fontWeight: 700, color: 'white', flexShrink: 0,
          }}>{initials}</div>
          {!collapsed && (
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {userEmail}
              </div>
              <div style={{ fontSize: '10px', color: '#64748b' }}>Admin</div>
            </div>
          )}
          {!collapsed && (
            <button onClick={onLogout} title="Logout" style={{
              background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', display: 'flex', padding: '4px',
            }}>
              <IconLogout />
            </button>
          )}
        </div>
        {collapsed && (
          <button onClick={onLogout} className="nav-item" title="Logout" style={{ width: '100%', justifyContent: 'center', border: '1px solid transparent', color: '#ef4444' }}>
            <IconLogout />
          </button>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
