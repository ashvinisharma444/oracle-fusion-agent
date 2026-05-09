'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { clearToken } from '@/lib/auth';

const navItems = [
  { href: '/dashboard', label: 'Overview', icon: '⬡' },
  { href: '/dashboard/diagnostics', label: 'Run Diagnostic', icon: '🔍' },
  { href: '/dashboard/sessions', label: 'Browser Sessions', icon: '🖥' },
  { href: '/dashboard/screenshots', label: 'Screenshots', icon: '📷' },
  { href: '/dashboard/knowledge', label: 'Knowledge Search', icon: '📚' },
  { href: '/dashboard/history', label: 'Report History', icon: '📋' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    clearToken();
    router.push('/login');
  };

  return (
    <aside className="w-64 min-h-screen bg-gray-950 border-r border-gray-800 flex flex-col">
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-red-600/20 border border-red-600/30 flex items-center justify-center text-red-500 font-bold text-sm">OA</div>
          <div>
            <p className="text-white font-semibold text-sm leading-tight">Fusion AI Agent</p>
            <p className="text-gray-500 text-xs">Phase 1 · Read Only</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-0.5">
        <p className="text-gray-600 text-xs font-semibold uppercase tracking-wider px-4 pt-3 pb-1">Diagnostics</p>
        {navItems.map(item => (
          <Link key={item.href} href={item.href}>
            <div className={`sidebar-item ${pathname === item.href ? 'active' : ''}`}>
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </div>
          </Link>
        ))}
      </nav>

      <div className="p-3 border-t border-gray-800">
        <button onClick={handleLogout} className="sidebar-item w-full text-left text-red-400 hover:text-red-300">
          <span>↩</span>
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
