import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Avatar, AvatarFallback } from '../components/ui/avatar';
import { Trophy, Medal, TrendingUp, TrendingDown, Users, Zap, Target, Flame, Star, Crown, Diamond, ChevronUp, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';

const TIER_CONFIG = {
  diamond: { color: '#B9F2FF', bg: 'bg-cyan-500/10', border: 'border-cyan-500/30', icon: Diamond },
  platinum: { color: '#E5E7EB', bg: 'bg-gray-300/10', border: 'border-gray-300/30', icon: Crown },
  gold: { color: '#FFD700', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', icon: Trophy },
  silver: { color: '#C0C0C0', bg: 'bg-gray-400/10', border: 'border-gray-400/30', icon: Medal },
  bronze: { color: '#CD7F32', bg: 'bg-orange-600/10', border: 'border-orange-600/30', icon: Medal },
};

const BADGE_ICONS = {
  trophy: Trophy, flame: Flame, star: Star, zap: Zap, dollar: TrendingUp,
  diamond: Diamond, radar: Target, target: Target,
};

export default function LeaderboardPage() {
  const { api } = useAuth();
  const [leaderboard, setLeaderboard] = useState([]);
  const [communityStats, setCommunityStats] = useState(null);
  const [myStats, setMyStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [lb, cs, ms] = await Promise.all([
          api.get('/community/leaderboard'),
          api.get('/community/stats'),
          api.get('/community/my-stats'),
        ]);
        setLeaderboard(lb.data.leaderboard || []);
        setCommunityStats(cs.data);
        setMyStats(ms.data);
      } catch (e) {
        toast.error('Failed to load leaderboard');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [api]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-[#6366F1] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 page-enter" data-testid="leaderboard-page">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Leaderboard</h1>
        <p className="text-sm text-white/50 mt-1">Top traders ranked by P&L performance</p>
      </div>

      {/* Community Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Traders', value: communityStats?.total_traders || 0, icon: Users },
          { label: 'Signals Generated', value: communityStats?.total_signals_generated || 0, icon: Zap },
          { label: 'Trades Logged', value: communityStats?.total_trades_logged || 0, icon: BarChart3 },
          { label: 'Community Win Rate', value: `${communityStats?.community_win_rate || 0}%`, icon: Target },
        ].map(s => (
          <Card key={s.label} className="bg-[#0A0A0F] border-white/5">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <s.icon className="w-4 h-4 text-[#6366F1]" />
                <span className="text-[11px] text-white/40 uppercase tracking-wider">{s.label}</span>
              </div>
              <p className="text-xl font-bold text-white font-data">{typeof s.value === 'number' ? s.value.toLocaleString() : s.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* My Stats */}
      {myStats && (
        <Card className="bg-[#0A0A0F] border-[#6366F1]/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-white flex items-center gap-2">
              <Star className="w-4 h-4 text-[#6366F1]" />
              Your Stats
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
              <div>
                <p className="text-[11px] text-white/40 uppercase">Rank</p>
                <p className="text-lg font-bold text-white font-data">#{myStats.leaderboard_rank || '-'}</p>
              </div>
              <div>
                <p className="text-[11px] text-white/40 uppercase">Win Rate</p>
                <p className="text-lg font-bold text-white font-data">{myStats.win_rate}%</p>
              </div>
              <div>
                <p className="text-[11px] text-white/40 uppercase">Total P&L</p>
                <p className={`text-lg font-bold font-data ${myStats.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {myStats.total_pnl >= 0 ? '+' : ''}${myStats.total_pnl?.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-white/40 uppercase">Trades</p>
                <p className="text-lg font-bold text-white font-data">{myStats.total_trades}</p>
              </div>
            </div>
            {myStats.badges?.length > 0 && (
              <div>
                <p className="text-[11px] text-white/40 uppercase mb-2">Badges</p>
                <div className="flex flex-wrap gap-2">
                  {myStats.badges.map(b => {
                    const Icon = BADGE_ICONS[b.icon] || Star;
                    return (
                      <Badge key={b.id} variant="outline" className="border-[#6366F1]/30 text-[#6366F1] bg-[#6366F1]/5 gap-1 text-xs py-1 px-2">
                        <Icon className="w-3 h-3" />
                        {b.name}
                      </Badge>
                    );
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Leaderboard Table */}
      <Card className="bg-[#0A0A0F] border-white/5">
        <CardHeader className="pb-3">
          <CardTitle className="text-base text-white flex items-center gap-2">
            <Trophy className="w-4 h-4 text-yellow-500" />
            Top Traders
          </CardTitle>
        </CardHeader>
        <CardContent>
          {leaderboard.length === 0 ? (
            <div className="text-center py-12">
              <Trophy className="w-12 h-12 text-white/10 mx-auto mb-3" />
              <p className="text-white/40 text-sm">No traders on the leaderboard yet</p>
              <p className="text-white/25 text-xs mt-1">Start logging trades in your Journal to appear here</p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Header */}
              <div className="hidden md:grid grid-cols-12 gap-2 px-3 py-2 text-[10px] text-white/30 uppercase tracking-wider">
                <div className="col-span-1">Rank</div>
                <div className="col-span-3">Trader</div>
                <div className="col-span-2">Trades</div>
                <div className="col-span-2">Win Rate</div>
                <div className="col-span-2">Avg P&L</div>
                <div className="col-span-2 text-right">Total P&L</div>
              </div>
              {leaderboard.map((t, i) => {
                const tierCfg = TIER_CONFIG[t.tier] || TIER_CONFIG.bronze;
                const TierIcon = tierCfg.icon;
                return (
                  <div key={t.user_id} className={`grid grid-cols-12 gap-2 items-center px-3 py-3 rounded-lg border ${i < 3 ? tierCfg.bg + ' ' + tierCfg.border : 'bg-white/[0.02] border-white/5'}`} data-testid={`leaderboard-row-${i}`}>
                    <div className="col-span-2 md:col-span-1">
                      {i < 3 ? (
                        <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: `${tierCfg.color}15` }}>
                          <TierIcon className="w-4 h-4" style={{ color: tierCfg.color }} />
                        </div>
                      ) : (
                        <span className="text-sm font-data text-white/50">#{t.rank}</span>
                      )}
                    </div>
                    <div className="col-span-5 md:col-span-3 flex items-center gap-2">
                      <Avatar className="w-7 h-7">
                        <AvatarFallback className="bg-[#6366F1]/20 text-[#6366F1] text-[10px]">{t.avatar}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="text-sm text-white truncate">{t.name}</p>
                        <Badge variant="outline" className="text-[9px] border-white/10 text-white/40 capitalize">{t.tier}</Badge>
                      </div>
                    </div>
                    <div className="col-span-5 md:col-span-2 md:block">
                      <span className="text-sm font-data text-white">{t.total_trades}</span>
                      <span className="text-xs text-white/30 ml-1">({t.wins}W/{t.losses}L)</span>
                    </div>
                    <div className="hidden md:block col-span-2">
                      <span className={`text-sm font-data ${t.win_rate >= 50 ? 'text-emerald-400' : 'text-red-400'}`}>{t.win_rate}%</span>
                    </div>
                    <div className="hidden md:block col-span-2">
                      <span className={`text-sm font-data ${t.avg_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {t.avg_pnl >= 0 ? '+' : ''}${t.avg_pnl.toLocaleString()}
                      </span>
                    </div>
                    <div className="col-span-12 md:col-span-2 text-right">
                      <span className={`text-base font-bold font-data ${t.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {t.total_pnl >= 0 ? '+' : ''}${t.total_pnl.toLocaleString()}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
