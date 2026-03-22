import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { Bell, Check, CheckCheck } from 'lucide-react';
import { Button } from './ui/button';

export const NotificationBell = () => {
  const { api } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const fetchNotifications = async () => {
    try {
      const [nRes, cRes] = await Promise.all([
        api.get('/notifications'),
        api.get('/notifications/unread-count'),
      ]);
      setNotifications(nRes.data.notifications || []);
      setUnreadCount(cRes.data.count || 0);
    } catch {}
  };

  useEffect(() => {
    fetchNotifications();
    const id = setInterval(fetchNotifications, 10000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const markRead = async (notifId) => {
    try {
      await api.post(`/notifications/${notifId}/read`);
      setNotifications(prev => prev.map(n => n.notif_id === notifId ? { ...n, read: true } : n));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch {}
  };

  const markAllRead = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch {}
  };

  const timeAgo = (iso) => {
    const diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60) return 'now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return `${Math.floor(diff / 86400)}d`;
  };

  return (
    <div className="relative" ref={ref}>
      <Button
        variant="ghost"
        size="icon"
        className="w-9 h-9 text-white/50 hover:text-white relative"
        onClick={() => setOpen(!open)}
        data-testid="notification-bell"
      >
        <Bell className="w-[18px] h-[18px]" />
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-[#FF2E2E] text-[9px] text-white flex items-center justify-center font-data font-bold" data-testid="notification-badge">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 max-h-96 rounded-xl glass-panel border border-white/10 shadow-2xl z-50 overflow-hidden" data-testid="notification-dropdown">
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <span className="text-xs font-semibold text-white">Notifications</span>
            {unreadCount > 0 && (
              <button className="text-[10px] text-[#6366F1] hover:text-[#818CF8] flex items-center gap-1" onClick={markAllRead} data-testid="mark-all-read-btn">
                <CheckCheck className="w-3 h-3" /> Mark all read
              </button>
            )}
          </div>
          <div className="overflow-y-auto max-h-72">
            {notifications.length === 0 ? (
              <div className="py-8 text-center">
                <Bell className="w-6 h-6 text-white/10 mx-auto mb-2" />
                <p className="text-[10px] text-white/30">No notifications yet</p>
              </div>
            ) : (
              notifications.slice(0, 20).map(n => (
                <div
                  key={n.notif_id}
                  className={`px-4 py-3 border-b border-white/5 cursor-pointer hover:bg-white/[0.03] ${!n.read ? 'bg-[#6366F1]/5' : ''}`}
                  onClick={() => !n.read && markRead(n.notif_id)}
                  data-testid={`notification-${n.notif_id}`}
                >
                  <div className="flex items-start gap-2">
                    {!n.read && <div className="w-1.5 h-1.5 rounded-full bg-[#6366F1] mt-1.5 shrink-0" />}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-white font-medium truncate">{n.title}</p>
                      <p className="text-[10px] text-white/50 mt-0.5 line-clamp-2">{n.message}</p>
                      <p className="text-[9px] text-white/20 mt-1 font-data">{timeAgo(n.created_at)}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
