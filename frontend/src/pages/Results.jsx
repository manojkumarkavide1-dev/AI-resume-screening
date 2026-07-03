import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Download, Award, FileText, CheckCircle2, Trash2 } from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import './Results.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const Results = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    try {
      const response = await axios.get('/api/results');
      setCandidates(response.data);
    } catch (error) {
      console.error('Failed to fetch results', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadCSV = () => {
    if (candidates.length === 0) return;
    
    const headers = ['Rank', 'Name', 'Filename', 'Match Score (%)', 'Skills'];
    const csvContent = [
      headers.join(','),
      ...candidates.map((c, i) => 
        `${i + 1},"${c.name}","${c.filename}",${c.match_score},"${c.skills.join(', ')}"`
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'screening_results.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const clearResults = async () => {
    if (window.confirm('Are you sure you want to delete all screening results? This cannot be undone.')) {
      try {
        await axios.delete('/api/results');
        setCandidates([]);
      } catch (error) {
        console.error('Failed to clear results', error);
        alert('Failed to clear results.');
      }
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner-large"></div>
        <p>Loading results...</p>
      </div>
    );
  }

  const chartData = {
    labels: candidates.slice(0, 10).map(c => c.name), // Top 10
    datasets: [
      {
        label: 'Match Score (%)',
        data: candidates.slice(0, 10).map(c => c.match_score),
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: 'var(--text-primary)'
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: { color: 'var(--text-secondary)' },
        grid: { color: 'var(--border)' }
      },
      x: {
        ticks: { color: 'var(--text-secondary)' },
        grid: { display: false }
      }
    }
  };

  return (
    <div className="results-container animate-fade-in">
      <div className="results-header">
        <h2>Screening Results</h2>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button onClick={clearResults} className="secondary-button" style={{ color: 'var(--danger)', borderColor: 'var(--danger)' }} disabled={candidates.length === 0}>
            <Trash2 size={18} /> Clear Data
          </button>
          <button onClick={downloadCSV} className="secondary-button" disabled={candidates.length === 0}>
            <Download size={18} /> Export CSV
          </button>
        </div>
      </div>

      {candidates.length > 0 && (
        <div className="chart-container glass">
          <h3>Top Candidates Match Distribution</h3>
          <div className="chart-wrapper">
            <Bar data={chartData} options={chartOptions} />
          </div>
        </div>
      )}

      <div className="candidates-list">
        {candidates.length === 0 ? (
          <div className="empty-state glass">
            <FileText size={48} className="empty-icon" />
            <h3>No results found</h3>
            <p>Upload some resumes to see the analysis here.</p>
          </div>
        ) : (
          candidates.map((candidate, index) => (
            <div key={candidate.id} className="candidate-card glass">
              <div className="candidate-rank">
                #{index + 1}
              </div>
              <div className="candidate-info">
                <h3>{candidate.name}</h3>
                <p className="filename"><FileText size={14} /> {candidate.filename}</p>
                <div className="skills-container">
                  {candidate.skills.slice(0, 5).map((skill, i) => (
                    <span key={i} className="skill-badge">{skill}</span>
                  ))}
                  {candidate.skills.length > 5 && (
                    <span className="skill-badge overflow">+{candidate.skills.length - 5}</span>
                  )}
                </div>
              </div>
              <div className="candidate-score">
                <div className="score-circle">
                  <svg viewBox="0 0 36 36" className="circular-chart">
                    <path className="circle-bg"
                      d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path className="circle"
                      strokeDasharray={`${candidate.match_score}, 100`}
                      d="M18 2.0845
                        a 15.9155 15.9155 0 0 1 0 31.831
                        a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className="percentage">{candidate.match_score}%</div>
                </div>
                {index === 0 && <span className="top-match-badge"><Award size={14} /> Top Match</span>}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Results;
