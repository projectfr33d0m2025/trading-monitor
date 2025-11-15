import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { BarChart3, FileText, Home, Menu, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import AnalysisPage from './pages/AnalysisPage';
import TradeJournalPage from './pages/TradeJournalPage';
import DashboardPage from './pages/DashboardPage';

function Navigation() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/analysis', icon: BarChart3, label: 'Analysis' },
    { path: '/trades', icon: FileText, label: 'Trades' },
  ];

  // Close mobile menu when route changes
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <nav className="bg-gray-800 text-white">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <h1 className="text-xl font-bold mr-8">Trading Monitor</h1>
            {/* Desktop Navigation */}
            <div className="hidden md:flex space-x-4">
              {navItems.map(({ path, icon: Icon, label }) => (
                <Link
                  key={path}
                  to={path}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    location.pathname === path
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {label}
                </Link>
              ))}
            </div>
          </div>
          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-md text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
            aria-label="Toggle mobile menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>
      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-gray-700">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navItems.map(({ path, icon: Icon, label }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center px-3 py-2 rounded-md text-base font-medium transition-colors ${
                  location.pathname === path
                    ? 'bg-gray-900 text-white'
                    : 'text-gray-300 hover:bg-gray-600 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5 mr-3" />
                {label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/analysis" element={<AnalysisPage />} />
            <Route path="/trades" element={<TradeJournalPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
