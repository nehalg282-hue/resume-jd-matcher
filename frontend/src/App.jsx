import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const ScoreCircle = ({ score }) => {
  const color = score >= 70 ? '#38a169' : score >= 40 ? '#d69e2e' : '#e53e3e';
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="score-circle-wrapper">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="12" />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 70 70)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
        <text x="70" y="70" textAnchor="middle" dominantBaseline="middle" fontSize="26" fontWeight="700" fill={color}>
          {score}%
        </text>
      </svg>
      <div className="score-label" style={{ color }}>
        {score >= 70 ? 'Strong Match' : score >= 40 ? 'Partial Match' : 'Low Match'}
      </div>
    </div>
  );
};

const KeywordBadge = ({ word, type }) => (
  <span className={`keyword-badge ${type}`}>{word}</span>
);

export default function App() {
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeText, setResumeText] = useState('');
  const [jdText, setJdText] = useState('');
  const [inputMode, setInputMode] = useState('text');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setResumeFile(file);
      setResumeText('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);

    if (inputMode === 'text' && !resumeText.trim()) {
      setError('Please enter your resume text.');
      return;
    }
    if (inputMode === 'file' && !resumeFile) {
      setError('Please upload a resume file.');
      return;
    }
    if (!jdText.trim()) {
      setError('Please enter the job description.');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      if (inputMode === 'file' && resumeFile) {
        formData.append('resume_file', resumeFile);
      } else {
        formData.append('resume_text', resumeText);
      }
      formData.append('jd_text', jdText);

      const response = await axios.post('/api/match', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError('');
    setResumeText('');
    setJdText('');
    setResumeFile(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">📄</span>
            <span className="logo-text">Resume<span className="accent">Match</span></span>
          </div>
          <p className="header-subtitle">AI-powered resume & job description matcher</p>
        </div>
      </header>

      <main className="app-main">
        {!result ? (
          <form className="match-form" onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-section">
                <div className="section-header">
                  <h2>Your Resume</h2>
                  <div className="input-toggle">
                    <button
                      type="button"
                      className={`toggle-btn ${inputMode === 'text' ? 'active' : ''}`}
                      onClick={() => setInputMode('text')}
                    >
                      Paste Text
                    </button>
                    <button
                      type="button"
                      className={`toggle-btn ${inputMode === 'file' ? 'active' : ''}`}
                      onClick={() => setInputMode('file')}
                    >
                      Upload File
                    </button>
                  </div>
                </div>

                {inputMode === 'text' ? (
                  <textarea
                    className="text-input"
                    placeholder="Paste your resume content here..."
                    value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)}
                    rows={14}
                  />
                ) : (
                  <div className="file-upload-area">
                    <input
                      type="file"
                      id="resume-file"
                      accept=".pdf,.docx,.txt"
                      onChange={handleFileChange}
                      style={{ display: 'none' }}
                    />
                    <label htmlFor="resume-file" className="file-label">
                      {resumeFile ? (
                        <div className="file-selected">
                          <span className="file-icon">✅</span>
                          <span className="file-name">{resumeFile.name}</span>
                          <span className="file-size">({(resumeFile.size / 1024).toFixed(1)} KB)</span>
                        </div>
                      ) : (
                        <div className="file-placeholder">
                          <span className="upload-icon">⬆️</span>
                          <span>Click to upload PDF, DOCX, or TXT</span>
                          <span className="file-hint">Max 10MB</span>
                        </div>
                      )}
                    </label>
                  </div>
                )}
              </div>

              <div className="form-section">
                <div className="section-header">
                  <h2>Job Description</h2>
                </div>
                <textarea
                  className="text-input"
                  placeholder="Paste the job description here..."
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  rows={14}
                />
              </div>
            </div>

            {error && <div className="error-msg">⚠️ {error}</div>}

            <div className="form-actions">
              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? (
                  <><span className="spinner" /> Analyzing...</>
                ) : (
                  '🔍 Analyze Match'
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="results-container">
            <div className="results-header">
              <h2>Match Analysis Results</h2>
              <button className="reset-btn" onClick={handleReset}>← New Analysis</button>
            </div>

            <div className="results-grid">
              <div className="result-card score-card">
                <h3>Overall Match Score</h3>
                <ScoreCircle score={result.match_percentage} />
                <p className="score-description">
                  Based on TF-IDF cosine similarity between your resume and the job description.
                </p>
              </div>

              <div className="result-card keywords-card">
                <h3>✅ Matched Keywords</h3>
                <p className="keywords-count">{result.matched_keywords.length} keywords found in both</p>
                <div className="keywords-list">
                  {result.matched_keywords.length > 0 ? (
                    result.matched_keywords.map(kw => (
                      <KeywordBadge key={kw} word={kw} type="matched" />
                    ))
                  ) : (
                    <p className="no-keywords">No common keywords found.</p>
                  )}
                </div>
              </div>

              <div className="result-card missing-card">
                <h3>❌ Missing Keywords</h3>
                <p className="keywords-count">{result.missing_keywords.length} keywords from JD not in resume</p>
                <div className="keywords-list">
                  {result.missing_keywords.length > 0 ? (
                    result.missing_keywords.map(kw => (
                      <KeywordBadge key={kw} word={kw} type="missing" />
                    ))
                  ) : (
                    <p className="no-keywords">All key terms are covered!</p>
                  )}
                </div>
              </div>

              <div className="result-card tips-card">
                <h3>💡 Improvement Tips</h3>
                <ul className="tips-list">
                  {result.match_percentage < 70 && (
                    <li>Add more keywords from the job description to your resume.</li>
                  )}
                  {result.missing_keywords.length > 0 && (
                    <li>
                      Consider incorporating: <strong>{result.missing_keywords.slice(0, 5).join(', ')}</strong>
                      {result.missing_keywords.length > 5 ? ` and ${result.missing_keywords.length - 5} more...` : ''}
                    </li>
                  )}
                  {result.match_percentage >= 70 && (
                    <li>Great match! Your resume aligns well with this job description.</li>
                  )}
                  <li>Tailor your experience bullets to mirror the job description language.</li>
                  <li>Quantify achievements where possible to strengthen your profile.</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Resume JD Matcher — NLP-powered matching using TF-IDF & cosine similarity</p>
      </footer>
    </div>
  );
}
