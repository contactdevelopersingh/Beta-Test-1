import { useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AuthCallback } from './components/AuthCallback';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout } from './components/AppLayout';
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import DashboardPage from './pages/DashboardPage';
import SignalsPage from './pages/SignalsPage';
import MarketsPage from './pages/MarketsPage';
import PortfolioPage from './pages/PortfolioPage';
import AlertsPage from './pages/AlertsPage';
import ChartPage from './pages/ChartPage';
import StrategyPage from './pages/StrategyPage';
import ChatPage from './pages/ChatPage';
import SettingsPage from './pages/SettingsPage';
import JournalPage from './pages/JournalPage';
import AdminPage from './pages/AdminPage';
import PricingPage from './pages/PricingPage';
import LeaderboardPage from './pages/LeaderboardPage';
import TradePage from './pages/TradePage';
import StockAnalysisPage from './pages/StockAnalysisPage';
import ScreenerPage from './pages/ScreenerPage';

function AppRouter() {
  const location = useLocation();

  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  // Check URL fragment for session_id - synchronous detection prevents race conditions
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/signals" element={<SignalsPage />} />
        <Route path="/markets" element={<MarketsPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/chart/:assetType/:assetId" element={<ChartPage />} />
        <Route path="/strategy" element={<StrategyPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/journal" element={<JournalPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/leaderboard" element={<LeaderboardPage />} />
        <Route path="/trade" element={<TradePage />} />
        <Route path="/stock-analysis" element={<StockAnalysisPage />} />
        <Route path="/stock-analysis/:symbol" element={<StockAnalysisPage />} />
        <Route path="/screener" element={<ScreenerPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
