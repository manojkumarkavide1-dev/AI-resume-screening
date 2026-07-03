import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sun, Moon, BrainCircuit } from 'lucide-react';
import './Navbar.css';

const Navbar = ({ theme, toggleTheme }) => {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  return (
    <nav className="navbar glass">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          <BrainCircuit className="logo-icon" />
          <span className="text-gradient font-bold">NeuralMatch</span>
        </Link>
        
        <div className="navbar-links">
          <Link to="/" className={`nav-link ${isActive('/')}`}>Home</Link>
          <Link to="/upload" className={`nav-link ${isActive('/upload')}`}>Upload</Link>
          <Link to="/results" className={`nav-link ${isActive('/results')}`}>Dashboard</Link>
        </div>

        <button className="theme-toggle" onClick={toggleTheme} aria-label="Toggle Theme">
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
