import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { BarChart3, FileText, Home, Menu, X, ChevronLeft, ChevronRight, List } from 'lucide-react';
import AnalysisPage from './pages/AnalysisPage';
import TradeJournalPage from './pages/TradeJournalPage';
import DashboardPage from './pages/DashboardPage';
import WatchlistPage from './pages/WatchlistPage';

function Navigation() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const NavItem = ({ to, icon: Icon, label }: { to: string; icon: any; label: string }) => (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center px-6 py-3 text-gray-700 hover:bg-gray-100 transition-all duration-200 ${
          isActive ? 'bg-gray-100 border-r-4 border-blue-500' : ''
        }`
      }
      onClick={() => setIsMobileMenuOpen(false)}
    >
      <Icon className={`${isSidebarOpen ? 'mr-3' : 'mx-auto'}`} size={20} />
      {isSidebarOpen && <span>{label}</span>}
    </NavLink>
  );

  return (
    <>
      {/* Desktop Sidebar */}
      <div
        className={`hidden md:block bg-white shadow-md transition-all duration-300 ease-in-out ${
          isSidebarOpen ? 'w-64' : 'w-16'
        }`}
      >
        <div className="relative">
          {/* Header with Toggle Button */}
          <div className={`p-6 ${!isSidebarOpen && 'p-4'}`}>
            <div className="flex items-center justify-between">
              {isSidebarOpen && (
                <h1 className="text-xl font-bold">Trading Monitor</h1>
              )}
              <button
                onClick={toggleSidebar}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label={isSidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
              >
                {isSidebarOpen ? (
                  <ChevronLeft size={20} className="text-gray-600" />
                ) : (
                  <ChevronRight size={20} className="text-gray-600" />
                )}
              </button>
            </div>
          </div>

          {/* Navigation */}
          <nav className="mt-6">
            <NavItem to="/" icon={Home} label="Dashboard" />
            <NavItem to="/analysis" icon={BarChart3} label="Analysis" />
            <NavItem to="/trades" icon={FileText} label="Trades" />
            <NavItem to="/watchlist" icon={List} label="Watchlist" />
          </nav>
        </div>
      </div>

      {/* Mobile Menu Button */}
      <button
        onClick={toggleMobileMenu}
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md hover:bg-gray-100 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="Toggle menu"
      >
        {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Mobile Sidebar Overlay */}
      {isMobileMenuOpen && (
        <div
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={toggleMobileMenu}
        />
      )}

      {/* Mobile Sidebar */}
      <div
        className={`md:hidden fixed top-0 left-0 h-full w-64 bg-white shadow-lg z-40 transform transition-transform duration-300 ease-in-out ${
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-6 mt-14">
          <h1 className="text-xl font-bold">Trading Monitor</h1>
        </div>
        <nav className="mt-6">
          <NavItem to="/" icon={Home} label="Dashboard" />
          <NavItem to="/analysis" icon={BarChart3} label="Analysis" />
          <NavItem to="/trades" icon={FileText} label="Trades" />
          <NavItem to="/watchlist" icon={List} label="Watchlist" />
        </nav>
      </div>
    </>
  );
}

function App() {
  return (
    <Router>
      <div className="md:flex md:h-screen bg-gray-100">
        <Navigation />
        {/* Main Content */}
        <div className="flex-1 flex flex-col md:overflow-hidden">
          <main className="p-4 md:p-6 md:flex-1 md:overflow-y-auto transition-all duration-300">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/analysis" element={<AnalysisPage />} />
              <Route path="/trades" element={<TradeJournalPage />} />
              <Route path="/watchlist" element={<WatchlistPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
