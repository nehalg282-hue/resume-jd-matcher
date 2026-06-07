import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const ScoreCircle = ({ score, label, size = 140 }) => {
  const color = score >= 70 ? '#38a169' : score >= 40 ? '#d69e2e' : '#e53e3e';
  const radius = size === 140 ? 54 : 38;
  const strokeWidth = size === 140 ? 12 : 8;
  const fontSize = size === 140 ? 26 : 16;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const cx = size / 2;
  const cy = size / 2;

  return (
    <div className="score-circle-wrapper">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={cx} cy={cy} r={radius} fill="none" stroke="#e2e8f0" strokeWidth={strokeWidth} />
        <circle
          cx={cx} cy={cy} r={radius}
          fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="middle"
          fontSize={fontSize} fontWeight="700" fill={color}>
          {score}%
        </text>
      </svg>
      {label && <div className="score-circle-label" style={{ color }}>{label}</div>}
    </div>
  );
};

const KeywordBadge = ({ word, type }) => (
  <span className={`keyword-badge ${type}`}>{word}</span>
);

const SectionBar = ({ label, value }) => {
  const color = value >= 70 ? '#38a169' : value >= 40 ? '#d69e2e' : '#e53e3e';
  return (
    <div className="section-bar">
      <div className="section-bar-header">
        <span className="section-bar-label">{label}</span>
        <span className="section-bar-value" style={{ color }}>{value}%</span>
      </div>
      <div className="section-bar-track">
        <div
          className="section-bar-fill"
          style={{ width: `${value}%`, background: color, transition: 'width 1s ease' }}
        />
      </div>
    </div>
  );
};

const DebugPanel = ({ debug }) => {
  const [open, setOpen] = useState(false);
  if (!debug) return null;
  return (
    <div className="debug-panel">
      <button className="debug-toggle" onClick={() => setOpen(o => !o)}>
        🔬 Debug Info {open ? '▲' : '▼'}
      </button>
      {open && (
        <div className="debug-content">
          <div className="debug-row">
            <span>Total JD keywords</span><strong>{debug.total_jd_keywords}</strong>
          </div>
          <div className="debug-row">
            <span>Total matched</span><strong>{debug.total_matched}</strong>
          </div>
          <div className="debug-row">
            <span>Sections detected</span>
            <strong>{debug.sections_found?.join(', ') || '—'}</strong>
          </div>
          <div className="debug-keywords">
            <div>
              <p className="debug-kw-title matched-title">Matched ({debug.exact_matched?.length})</p>
              <div className="keywords-list">
                {debug.exact_matched?.map(k => <KeywordBadge key={k} word={k} type="matched" />)}
              </div>
            </div>
            <div>
              <p className="debug-kw-title missing-title">Missing ({debug.exact_missing?.length})</p>
              <div className="keywords-list">
                {debug.exact_missing?.map(k => <KeywordBadge key={k} word={k} type="missing" />)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

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
    if (file) { setResumeFile(file); setResumeText(''); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setResult(null);
    if (inputMode === 'text' && !resumeText.trim()) { setError('Please enter your resume text.'); return; }
    if (inputMode === 'file' && !resumeFile) { setError('Please upload a resume file.'); return; }
    if (!jdText.trim()) { setError('Please enter the job description.'); return; }

    setLoading(true);
    try {
      const formData = new FormData();
      if (inputMode === 'file' && resumeFile) formData.append('resume_file', resumeFile);
      else formData.append('resume_text', resumeText);
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
    setResult(null); setError(''); setResumeText(''); setJdText(''); setResumeFile(null);
  };

  const matchLabel = result
    ? result.match_percentage >= 70 ? 'Strong Match'
      : result.match_percentage >= 40 ? 'Partial Match' : 'Low Match'
    : '';

  const sectionLabels = {
    skills: '🛠 Skills',
    experience: '💼 Experience',
    projects: '🚀 Projects',
    education: '🎓 Education',
    certifications: '📜 Certifications',
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">📄</span>
            <span className="logo-text">Resume<span className="accent">Match</span></span>
          </div>
          <p className="header-subtitle">AI-powered resume & job description matcher with ATS scoring</p>
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
                    <button type="button" className={`toggle-btn ${inputMode === 'text' ? 'active' : ''}`}
                      onClick={() => setInputMode('text')}>Paste Text</button>
                    <button type="button" className={`toggle-btn ${inputMode === 'file' ? 'active' : ''}`}
                      onClick={() => setInputMode('file')}>Upload File</button>
                  </div>
                </div>
                {inputMode === 'text' ? (
                  <textarea className="text-input" placeholder="Paste your resume content here..." value={resumeText}
                    onChange={(e) => setResumeText(e.target.value)} rows={14} />
                ) : (
                  <div className="file-upload-area">
                    <input type="file" id="resume-file" accept=".pdf,.docx,.txt"
                      onChange={handleFileChange} style={{ display: 'none' }} />
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
                <div className="section-header"><h2>Job Description</h2></div>
                <textarea className="text-input" placeholder="Paste the job description here..."
                  value={jdText} onChange={(e) => setJdText(e.target.value)} rows={14} />
              </div>
            </div>

            {error && <div className="error-msg">⚠️ {error}</div>}
            <div className="form-actions">
              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? <><span className="spinner" /> Analyzing...</> : '🔍 Analyze Match'}
              </button>
            </div>
          </form>
        ) : (
          <div className="results-container">
            <div className="results-header">
              <h2>Match Analysis Results</h2>
              <button className="reset-btn" onClick={handleReset}>← New Analysis</button>
            </div>

            {/* Top score row */}
            <div className="scores-row">
              <div className="result-card score-card main-score-card">
                <h3>Overall Match Score</h3>
                <ScoreCircle score={result.match_percentage} />
                <div className="score-verdict" style={{
                  color: result.match_percentage >= 70 ? '#38a169' : result.match_percentage >= 40 ? '#d69e2e' : '#e53e3e'
                }}>{matchLabel}</div>
                <p className="score-description">
                  Blended score: 60% ATS keyword coverage + 40% weighted section analysis
                </p>
              </div>

              <div className="result-card mini-scores-card">
                <h3>Detailed Scores</h3>
                <div className="mini-scores-grid">
                  <div className="mini-score">
                    <ScoreCircle score={result.ats_score} size={96} />
                    <p className="mini-score-label">ATS Score</p>
                  </div>
                  <div className="mini-score">
                    <ScoreCircle score={result.keyword_coverage} size={96} />
                    <p className="mini-score-label">Keyword Coverage</p>
                  </div>
                  <div className="mini-score">
                    <ScoreCircle score={result.experience_match} size={96} />
                    <p className="mini-score-label">Experience Match</p>
                  </div>
                  <div className="mini-score">
                    <ScoreCircle score={result.weighted_score} size={96} />
                    <p className="mini-score-label">Weighted Section</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Section breakdown */}
            <div className="result-card section-card">
              <h3>📊 Section-by-Section Breakdown</h3>
              <p className="section-subtitle">
                Weights: Skills 50% · Experience 25% · Projects 15% · Education 5% · Certifications 5%
              </p>
              <div className="section-bars">
                {Object.entries(sectionLabels).map(([key, label]) => (
                  <SectionBar
                    key={key}
                    label={label}
                    value={result.section_scores?.[key] ?? 0}
                  />
                ))}
              </div>
            </div>

            {/* Keyword rows */}
            <div className="keywords-row">
              <div className="result-card keywords-card">
                <h3>✅ Matched Keywords</h3>
                <p className="keywords-count">
                  {result.matched_keywords.length} of {result.debug?.total_jd_keywords} JD keywords matched
                </p>
                <div className="keywords-list">
                  {result.matched_keywords.length > 0
                    ? result.matched_keywords.map(kw => <KeywordBadge key={kw} word={kw} type="matched" />)
                    : <p className="no-keywords">No common keywords found.</p>}
                </div>
              </div>

              <div className="result-card missing-card">
                <h3>❌ Missing Keywords</h3>
                <p className="keywords-count">
                  {result.missing_keywords.length} JD keywords not found in resume
                </p>
                <div className="keywords-list">
                  {result.missing_keywords.length > 0
                    ? result.missing_keywords.map(kw => <KeywordBadge key={kw} word={kw} type="missing" />)
                    : <p className="no-keywords">All key terms are covered! 🎉</p>}
                </div>
              </div>
            </div>

            {/* Tips */}
            <div className="result-card tips-card">
              <h3>💡 Improvement Tips</h3>
              <ul className="tips-list">
                {result.match_percentage >= 70 && (
                  <li>Great match! Your resume aligns well with this job description.</li>
                )}
                {result.match_percentage < 70 && (
                  <li>Add more keywords from the job description to your resume to improve ATS scoring.</li>
                )}
                {result.missing_keywords.length > 0 && (
                  <li>
                    Consider incorporating: <strong>{result.missing_keywords.slice(0, 6).join(', ')}</strong>
                    {result.missing_keywords.length > 6 ? ` and ${result.missing_keywords.length - 6} more…` : ''}
                  </li>
                )}
                {result.section_scores?.experience < 40 && (
                  <li>Your experience section has low keyword overlap — mirror the JD's language in your job bullets.</li>
                )}
                {result.section_scores?.skills < 50 && (
                  <li>Expand your skills section with technologies mentioned in the job description.</li>
                )}
                <li>Quantify achievements (e.g. "improved performance by 30%") to strengthen your profile.</li>
                <li>Use the exact terminology from the JD — ATS systems match keywords literally.</li>
              </ul>
            </div>

            {/* Debug panel */}
            <DebugPanel debug={result.debug} />
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Resume JD Matcher — ATS scoring · synonym mapping · section-weighted NLP analysis</p>
      </footer>
    </div>
  );
}
