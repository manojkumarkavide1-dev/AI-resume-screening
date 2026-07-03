import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { UploadCloud, File as FileIcon, X, Loader2 } from 'lucide-react';
import './Upload.css';

const Upload = () => {
  const [jobDescription, setJobDescription] = useState('');
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      file => file.type === 'application/pdf' || 
              file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
              file.name.endsWith('.pdf') || 
              file.name.endsWith('.docx')
    );
    setFiles(prev => [...prev, ...droppedFiles]);
  };

  const handleFileInput = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(prev => [...prev, ...selectedFiles]);
  };

  const removeFile = (indexToRemove) => {
    setFiles(files.filter((_, index) => index !== indexToRemove));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!jobDescription.trim()) {
      setError('Please enter a job description');
      return;
    }
    
    if (files.length === 0) {
      setError('Please upload at least one resume');
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('job_description', jobDescription);
    files.forEach(file => {
      formData.append('resumes', file);
    });

    try {
      await axios.post('/api/analyze', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      navigate('/results');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'An error occurred during analysis');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="upload-container animate-fade-in">
      <div className="upload-header">
        <h2>New Analysis</h2>
        <p>Upload resumes and provide a job description to find the best match.</p>
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        <div className="form-group">
          <label htmlFor="jobDescription">Job Description</label>
          <textarea
            id="jobDescription"
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the full job description here..."
            className="job-textarea glass"
            rows={6}
          />
        </div>

        <div className="form-group">
          <label>Resumes (PDF or DOCX)</label>
          <div 
            className={`dropzone glass ${isDragging ? 'dragging' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              multiple
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              ref={fileInputRef}
              onChange={handleFileInput}
              style={{ display: 'none' }}
            />
            <div className="dropzone-content">
              <UploadCloud size={48} className="upload-icon" />
              <h3>Drag & drop resumes here</h3>
              <p>or click to browse files</p>
            </div>
          </div>
        </div>

        {files.length > 0 && (
          <div className="file-list">
            <h4>Selected Files ({files.length})</h4>
            <div className="file-grid">
              {files.map((file, index) => (
                <div key={index} className="file-item glass">
                  <FileIcon size={20} className="file-item-icon" />
                  <span className="file-name" title={file.name}>{file.name}</span>
                  <button type="button" onClick={() => removeFile(index)} className="remove-btn">
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && <div className="error-message glass">{error}</div>}

        <button 
          type="submit" 
          className="submit-button primary-button"
          disabled={isUploading || files.length === 0 || !jobDescription.trim()}
        >
          {isUploading ? (
            <>
              <Loader2 className="spinner" size={20} />
              Analyzing Resumes...
            </>
          ) : (
            'Analyze Candidates'
          )}
        </button>
      </form>
    </div>
  );
};

export default Upload;
