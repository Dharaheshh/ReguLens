import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, FileText, Search, ClipboardCheck,
  Activity, Settings, Microscope, ChevronRight,
} from 'lucide-react';

interface NavItem {
  to: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
}

const WORKSPACE_NAV: NavItem[] = [
  { to: '/',          icon: LayoutDashboard, label: 'Overview'  },
  { to: '/documents', icon: FileText,        label: 'Documents' },
  { to: '/queries',   icon: Search,          label: 'Queries'   },
  { to: '/reviews',   icon: ClipboardCheck,  label: 'Reviews'   },
];

const SYSTEM_NAV: NavItem[] = [
  { to: '/audit',    icon: Activity, label: 'Audit Log' },
  { to: '/settings', icon: Settings, label: 'Settings'  },
];

function NavGroup({ label, items }: { label: string; items: NavItem[] }) {
  const location = useLocation();

  return (
    <div className="mb-5">
      <p className="rl-label px-3 mb-1.5">{label}</p>
      <ul className="space-y-0.5">
        {items.map(({ to, icon: Icon, label: itemLabel }) => {
          // Exact match for home, startsWith for others
          const isActive = to === '/'
            ? location.pathname === '/'
            : location.pathname.startsWith(to);

          return (
            <li key={to}>
              <NavLink
                to={to}
                className={`
                  flex items-center gap-2.5 px-3 py-2 rounded-rl text-sm
                  transition-colors duration-100 select-none group
                  ${isActive
                    ? 'bg-rl-green-50 text-rl-green-800 font-medium'
                    : 'text-rl-neutral-600 hover:bg-rl-neutral-100 hover:text-rl-neutral-900'
                  }
                `}
              >
                <Icon
                  size={15}
                  className={isActive ? 'text-rl-green-700' : 'text-rl-neutral-400 group-hover:text-rl-neutral-600'}
                />
                <span className="flex-1">{itemLabel}</span>
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-rl-green-600 shrink-0" />
                )}
              </NavLink>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="fixed left-0 top-0 h-full w-56 bg-white border-r border-rl-neutral-200 flex flex-col z-30">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-rl-neutral-100">
        <div className="w-7 h-7 rounded-rl bg-rl-green-700 flex items-center justify-center shrink-0">
          <Microscope size={14} className="text-white" />
        </div>
        <div>
          <span className="text-sm font-bold text-rl-neutral-900 tracking-tight">ReguLens</span>
          <p className="text-2xs text-rl-neutral-400 leading-none mt-0.5">Evidence Workspace</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-4">
        <NavGroup label="Workspace" items={WORKSPACE_NAV} />
        <NavGroup label="System"    items={SYSTEM_NAV} />
      </nav>

      {/* User */}
      <div className="px-3 py-3 border-t border-rl-neutral-100">
        <button className="w-full flex items-center gap-2.5 px-2 py-2 rounded-rl hover:bg-rl-neutral-50 transition-colors group">
          <div className="w-7 h-7 rounded-full bg-rl-green-100 text-rl-green-800 text-xs font-bold flex items-center justify-center shrink-0">
            AR
          </div>
          <div className="flex-1 text-left min-w-0">
            <p className="text-xs font-medium text-rl-neutral-800 truncate">Akshay R.</p>
            <p className="text-2xs text-rl-neutral-400 truncate">Regulatory Specialist</p>
          </div>
          <ChevronRight size={13} className="text-rl-neutral-300 group-hover:text-rl-neutral-500 transition-colors" />
        </button>
      </div>
    </aside>
  );
}
