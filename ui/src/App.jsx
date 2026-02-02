/**
 * Kita.dev Main App
 * React Router setup with all pages
 */
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Tasks from './pages/Tasks';
import Config from './pages/Config';
import RunTask from './pages/RunTask';
import './App.css';

function Layout({ children }) {
  return (
    <div className="app-layout">
      <nav className="sidebar">
        <div className="sidebar-header">
          <span className="logo">
            ⚡<span className="logo-text"> Kita.dev</span>
          </span>
        </div>
        <ul className="nav-links">
          <li>
            <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
              <span>📊</span>
              <span className="nav-text">Dashboard</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/run" className={({ isActive }) => isActive ? 'active' : ''}>
              <span>🚀</span>
              <span className="nav-text">New Task</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/tasks" className={({ isActive }) => isActive ? 'active' : ''}>
              <span>📋</span>
              <span className="nav-text">Tasks</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/config" className={({ isActive }) => isActive ? 'active' : ''}>
              <span>⚙️</span>
              <span className="nav-text">Config</span>
            </NavLink>
          </li>
        </ul>
        <div className="sidebar-footer">
          <div className="version">v0.1.0</div>
        </div>
      </nav>
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/run" element={<RunTask />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/config" element={<Config />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
