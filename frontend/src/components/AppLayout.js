import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { NotificationBell } from './NotificationBell';
import { LayoutDashboard, Zap, TrendingUp, PieChart, MessageSquare, Settings, LogOut, Menu, X, Activity, Bell, Layers, BookOpen, CreditCard, Trophy, ArrowUpRight } from 'lucide-react';
import { useState } from 'react';
import { Button } from './ui/button';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Sheet, SheetContent, SheetTrigger } from './ui/sheet';
import { Toaster } from './ui/sonner';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/signals', icon: Zap, label: 'Signals' },
  { to: '/markets', icon: TrendingUp, label: 'Markets' },
  { to: '/journal', icon: BookOpen, label: 'Journal' },
  { to: '/portfolio', icon: PieChart, label: 'Portfolio' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/strategy', icon: Layers, label: 'Strategy' },
  { to: '/chat', icon: MessageSquare, label: 'Titan AI' },
  { to: '/trade', icon: ArrowUpRight, label: 'Trade' },
  { to: '/leaderboard', icon: Trophy, label: 'Leaderboard' },
  { to: '/pricing', icon: CreditCard, label: 'Pricing' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

const SidebarContent = ({ onClose }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-5 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#6366F1] flex items-center justify-center neon-glow">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white tracking-tight" style={{ fontFamily: 'Manrope' }}>Titan Trade</h1>
            <span className="text-[10px] uppercase tracking-widest text-[#6366F1] font-semibold">PRO</span>
          </div>
        </div>
      </div>

      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              `sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium ${
                isActive ? 'active bg-[#6366F1]/10 text-[#6366F1]' : 'text-white/60 hover:text-white'
              }`
            }
            data-testid={`nav-${label.toLowerCase().replace(' ', '-')}`}
          >
            <Icon className="w-[18px] h-[18px]" />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 mb-3">
          <Avatar className="w-8 h-8">
            <AvatarFallback className="bg-[#6366F1]/20 text-[#6366F1] text-xs">
              {user?.name?.charAt(0)?.toUpperCase() || 'U'}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-white truncate">{user?.name || 'User'}</p>
            <p className="text-[11px] text-white/40 truncate">{user?.email}</p>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start text-white/50 hover:text-red-400 hover:bg-red-500/10 text-xs"
          onClick={handleLogout}
          data-testid="logout-btn"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </div>
  );
};

export const AppLayout = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen flex" style={{ background: '#050505' }}>
      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-[240px] flex-col border-r border-white/10 bg-[#09090B]/80 backdrop-blur-xl fixed h-screen z-30">
        <SidebarContent onClose={() => {}} />
      </aside>

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 h-14 bg-[#09090B]/90 backdrop-blur-xl border-b border-white/10 flex items-center px-4">
        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="text-white" data-testid="mobile-menu-btn">
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[260px] p-0 bg-[#09090B] border-white/10">
            <SidebarContent onClose={() => setMobileOpen(false)} />
          </SheetContent>
        </Sheet>
        <div className="flex items-center gap-2 ml-3">
          <Activity className="w-5 h-5 text-[#6366F1]" />
          <span className="text-sm font-bold text-white">Titan Trade</span>
        </div>
        <div className="ml-auto">
          <NotificationBell />
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 lg:ml-[240px] pt-14 lg:pt-0 min-h-screen">
        <div className="hidden lg:flex items-center justify-end p-4 pb-0">
          <NotificationBell />
        </div>
        <div className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
      <Toaster position="top-right" theme="dark" />
    </div>
  );
};
