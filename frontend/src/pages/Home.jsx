import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, FileSearch, Target, Zap } from 'lucide-react';
import './Home.css';

const Home = () => {
  return (
    <div className="home-container animate-fade-in">
      <section className="hero-section">
        <h1 className="hero-title">
          Screen Resumes with <span className="text-gradient">AI Precision</span>
        </h1>
        <p className="hero-subtitle">
          Upload resumes and a job description. Our AI analyzes and ranks candidates in seconds using advanced NLP and cosine similarity.
        </p>
        <Link to="/upload" className="cta-button primary-button">
          Start Screening <ArrowRight size={20} />
        </Link>
      </section>

      <section className="features-section">
        <div className="feature-card glass">
          <div className="feature-icon-wrapper text-gradient">
            <Zap size={32} />
          </div>
          <h3>Lightning Fast</h3>
          <p>Process dozens of resumes in seconds instead of hours. Focus on the best candidates immediately.</p>
        </div>
        <div className="feature-card glass">
          <div className="feature-icon-wrapper text-gradient">
            <Target size={32} />
          </div>
          <h3>High Accuracy</h3>
          <p>Uses TF-IDF vectorization and cosine similarity to find the perfect match for your job description.</p>
        </div>
        <div className="feature-card glass">
          <div className="feature-icon-wrapper text-gradient">
            <FileSearch size={32} />
          </div>
          <h3>Smart Extraction</h3>
          <p>Automatically extracts key technical skills from both PDF and DOCX files for easy review.</p>
        </div>
      </section>
    </div>
  );
};

export default Home;
