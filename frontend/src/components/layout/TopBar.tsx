import { Search, Bell, HelpCircle } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const PAGE_TITLES: Record<string, string> = {
  '/':          'Overview',
  '/documents': 'Documents',
  '/queries':   'Queries',
  '/reviews':   'Reviews',
  '/audit':     'Audit Log',
  '/settings':  'Settings',
};

export function TopBar() {
  const location = useLocation();
  // Match longest prefix
  const title = Object.entries(PAGE_TITLES)
    .filter(([path]) => location.pathname === path || (path !== '/' && location.pathname.startsWith(path)))
    .sort(([a], [b]) => b.length - a.length)[0]?.[1] ?? 'ReguLens';

  return (
    <header className="fixed top-0 left-56 right-0 h-12 bg-white border-b border-rl-neutral-200 flex items-center px-5 z-20 gap-4">
      {/* Page title */}
      <h1 className="text-sm font-semibold text-rl-neutral-800 shrink-0">{title}</h1>

      <div className="w-px h-4 bg-rl-neutral-200 shrink-0" />

      {/* Search */}
      <div className="flex-1 max-w-sm relative">
        <Search
          size={13}
          className="absolute left-2.5 top-1/2 -translate-y-1/2 text-rl-neutral-400 pointer-events-none"
        />
        <input
          type="search"
          placeholder="Search queries, documents, evidence…"
          className="w-full pl-8 pr-3 py-1.5 text-xs bg-rl-neutral-50 border border-rl-neutral-200 rounded-rl
                     placeholder:text-rl-neutral-400 text-rl-neutral-700
                     focus:outline-none focus:ring-2 focus:ring-rl-green-500 focus:bg-white
                     transition-colors duration-150"
        />
      </div>

      <div className="flex-1" />

      {/* Actions */}
      <div className="flex items-center gap-1">
        <button className="p-1.5 rounded-rl hover:bg-rl-neutral-100 text-rl-neutral-500 transition-colors relative" title="Notifications">
          <Bell size={15} />
          <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-rl-amber-500 rounded-full" />
        </button>
        <button className="p-1.5 rounded-rl hover:bg-rl-neutral-100 text-rl-neutral-500 transition-colors" title="Help">
          <HelpCircle size={15} />
        </button>
      </div>

      {/* Status pill */}
      <div className="flex items-center gap-1.5 pl-3 border-l border-rl-neutral-200">
        <span className="w-1.5 h-1.5 rounded-full bg-rl-green-500 animate-pulse-subtle" />
        <span className="text-2xs text-rl-neutral-500 font-medium">System ready</span>
      </div>
    </header>
  );
}
