import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function AppLayout() {
  return (
    <div className="min-h-screen bg-rl-neutral-50 flex">
      <Sidebar />
      <div className="flex-1 ml-56 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 mt-12 p-6 overflow-x-hidden">
          <div className="max-w-6xl mx-auto w-full">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
