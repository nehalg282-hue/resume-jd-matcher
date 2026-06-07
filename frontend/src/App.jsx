import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

// ── Helpers ────────────────────────────────────────────────────────────────

const scoreColor = (s) =>
  s >= 80 ? '#2f855a' : s >= 70 ? '#38a169' : s >= 50 ? '#d69e2e' : s >= 20 ? '#dd6b20' : '#e53e3e';

const scoreLabel = (s) =>
  s >= 80 ? 'Excellent Match' : s >= 70 ? 'Strong Match' : s >= 50 ? 'Moderate Match' : s >= 20 ? 'Weak Match' : 'Poor Match';

const scoreBg = (s) =>
  s >= 80 ? '#f0fff4' : s >= 70 ? '#e6fffa' : s >= 50 ? '#fffff0' : s >= 20 ? '#fffaf0' : '#fff5f5';

// ── Sub-components ─────────────────────────────────────────────────────────

const ScoreRing = ({ score, size = 148 }) => {
  const r = size * 0.37;
  const stroke = size * 0.085;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(score, 100) / 100) * circ;
  const color = scoreColor(score);
  const cx = size / 2, cy = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="#e2e8f0" strokeWidth={stroke} />
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={stroke}
        strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
        style={{ transition: 'stroke-dashoffset 1.1s cubic-bezier(.4,0,.2,1)' }} />
      <text x={cx} y={cy - 6} textAnchor="middle" dominantBaseline="middle"
        fontSize={size * 0.18} fontWeight="800" fill={color}>{score}%</text>
      <text x={cx} y={cy + size * 0.12} textAnchor="middle" dominantBaseline="middle"
        fontSize={size * 0.085} fontWeight="600" fill="#718096">{scoreLabel(score)}</text>
    </svg>
  );
};

const MiniRing = ({ score, label }) => {
  const size = 88;
  const r = 32, stroke = 7;
  const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(score, 100) / 100) * circ;
  const color = scoreColor(score);
  return (
    <div className="mini-ring-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={44} cy={44} r={r} fill="none" stroke="#e2e8f0" strokeWidth={stroke} />
        <circle cx={44} cy={44} r={r} fill="none" stroke={color} strokeWidth={stroke}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          transform="rotate(-90 44 44)"
          style={{ transition: 'stroke-dashoffset 1.1s cubic-bezier(.4,0,.2,1)' }} />
        <text x={44} y={44} textAnchor="middle" dominantBaseline="middle"
          fontSize="14" fontWeight="700" fill={color}>{score}%</text>
      </svg>
      <p className="mini-ring-label">{label}</p>
    </div>
  );
};

const Bar = ({ label, value, weight }) => {
  const color = scoreColor(value);
  return (
    <div className="bar-row">
      <div className="bar-meta">
        <span className="bar-label">{label}</span>
        <span className="bar-right">
          {weight && <span className="bar-weight">{weight}</span>}
          <span className="bar-value" style={{ color }}>{value}%</span>
        </span>
      </div>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  );
};

const Badge = ({ word, type }) => <span className={`badge badge-${type}`}>{word}</span>;

const ClusterCard = ({ name, data }) => {
  const color = scoreColor(data.coverage);
  const icon = data.coverage >= 70 ? '✅' : data.coverage >= 30 ? '⚠️' : '❌';
  return (
    <div className="cluster-card" style={{ borderLeft: `4px solid ${color}` }}>
      <div className="cluster-header">
        <span className="cluster-icon">{icon}</span>
        <span className="cluster-name">{name}</span>
        <span className="cluster-pct" style={{ color }}>{data.coverage}%</span>
      </div>
      {data.matched_exact?.length > 0 && (
        <div className="cluster-pills">
          {data.matched_exact.map(s => <Badge key={s} word={s} type="matched" />)}
        </div>
      )}
      {data.matched_transfer?.length > 0 && (
        <div className="cluster-pills">
          {data.matched_transfer.map(s => <Badge key={s} word={s} type="partial" />)}
        </div>
      )}
      {data.missing?.length > 0 && (
        <div className="cluster-pills">
          {data.missing.map(s => <Badge key={s} word={s} type="missing" />)}
        </div>
      )}
    </div>
  );
};

const ReasoningPanel = ({ reasoning }) => {
  if (!reasoning) return null;
  return (
    <div className="reasoning-panel">
      <h3>🧠 Recruiter Confidence Reasoning</h3>

      {reasoning.strengths?.length > 0 && (
        <div className="reason-block">
          <p className="reason-title strength-title">💪 Strengths</p>
          <ul className="reason-list">
            {reasoning.strengths.map((s, i) => <li key={i} className="reason-strength">{s}</li>)}
          </ul>
        </div>
      )}

      {reasoning.experience_notes?.length > 0 && (
        <div className="reason-block">
          <p className="reason-title">💼 Experience</p>
          <ul className="reason-list">
            {reasoning.experience_notes.map((n, i) => (
              <li key={i} className={reasoning.experience_found ? 'reason-ok' : 'reason-warn'}>{n}</li>
            ))}
          </ul>
        </div>
      )}

      {reasoning.project_notes?.length > 0 && (
        <div className="reason-block">
          <p className="reason-title">🚀 Projects</p>
          <ul className="reason-list">
            {reasoning.project_notes.map((n, i) => (
              <li key={i} className={reasoning.projects_found ? 'reason-ok' : 'reason-warn'}>{n}</li>
            ))}
          </ul>
        </div>
      )}

      {reasoning.missing_critical?.length > 0 && (
        <div className="reason-block">
          <p className="reason-title missing-title">🚩 Missing Critical Requirements</p>
          <ul className="reason-list">
            {reasoning.missing_critical.map((n, i) => <li key={i} className="reason-missing">{n}</li>)}
          </ul>
        </div>
      )}
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
        <div className="debug-body">
          {[
            ['Total JD keywords', debug.total_jd_keywords],
            ['Exact matched', debug.total_matched],
            ['Partial matched (transferable)', debug.partial_matched],
            ['Effective matched (w/ credit)', debug.effective_matched],
            ['Raw blended score', `${debug.raw_blended}%`],
            ['Sections detected', debug.sections_found?.join(', ')],
          ].map(([k, v]) => (
            <div className="debug-row" key={k}>
              <span>{k}</span><strong>{v}</strong>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Main App ───────────────────────────────────────────────────────────────

export default function App() {
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeText, setResumeText] = useState('');
  const [jdText, setJdText] = useState('');
  const [inputMode, setInputMode] = useState('text');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (f) { setResumeFile(f); setResumeText(''); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setResult(null);
    if (inputMode === 'text' && !resumeText.trim()) { setError('Please enter your resume text.'); return; }
    if (inputMode === 'file' && !resumeFile) { setError('Please upload a resume file.'); return; }
    if (!jdText.trim()) { setError('Please enter the job description.'); return; }

    setLoading(true);
    try {
      const fd = new FormData();
      if (inputMode === 'file') fd.append('resume_file', resumeFile);
      else fd.append('resume_text', resumeText);
      fd.append('jd_text', jdText);
      const res = await axios.post('/api/match', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null); setError(''); setResumeText(''); setJdText(''); setResumeFile(null);
  };

  const sectionMeta = [
    { key: 'skills',          label: '🛠 Skills',          weight: '35%' },
    { key: 'experience',      label: '💼 Experience',       weight: '35%' },
    { key: 'projects',        label: '🚀 Projects',         weight: '20%' },
    { key: 'education',       label: '🎓 Education',        weight: '5%' },
    { key: 'certifications',  label: '📜 Certifications',   weight: '5%' },
  ];

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="logo">📄 Resume<span className="accent">Match</span></div>
          <p className="header-sub">Recruiter-style AI matching · skill clusters · transferable credit</p>
        </div>
      </header>

      <main className="app-main">
        {!result ? (
          <form className="match-form" onSubmit={handleSubmit}>
            <div className="form-grid">
              <div className="form-col">
                <div className="col-head">
                  <h2>Your Resume</h2>
                  <div className="toggle-group">
                    <button type="button" className={`tog ${inputMode === 'text' ? 'active' : ''}`}
                      onClick={() => setInputMode('text')}>Paste Text</button>
                    <button type="button" className={`tog ${inputMode === 'file' ? 'active' : ''}`}
                      onClick={() => setInputMode('file')}>Upload File</button>
                  </div>
                </div>
                {inputMode === 'text'
                  ? <textarea className="text-input" rows={15}
                      placeholder="Paste your full resume here…"
                      value={resumeText} onChange={e => setResumeText(e.target.value)} />
                  : (
                    <label htmlFor="rf" className="file-drop">
                      <input type="file" id="rf" accept=".pdf,.docx,.txt"
                        onChange={handleFileChange} style={{ display: 'none' }} />
                      {resumeFile
                        ? <><span className="file-icon">✅</span>
                            <span className="file-nm">{resumeFile.name}</span>
                            <span className="file-sz">({(resumeFile.size / 1024).toFixed(1)} KB)</span></>
                        : <><span style={{ fontSize: '2rem' }}>⬆️</span>
                            <span>Click to upload PDF, DOCX, or TXT</span>
                            <span className="file-hint">Max 10 MB</span></>
                      }
                    </label>
                  )
                }
              </div>

              <div className="form-col">
                <div className="col-head"><h2>Job Description</h2></div>
                <textarea className="text-input" rows={15}
                  placeholder="Paste the job description here…"
                  value={jdText} onChange={e => setJdText(e.target.value)} />
              </div>
            </div>

            {error && <div className="error-msg">⚠️ {error}</div>}
            <div className="form-foot">
              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? <><span className="spinner" /> Analyzing…</> : '🔍 Analyze Match'}
              </button>
            </div>
          </form>

        ) : (
          <div className="results">
            <div className="results-top">
              <h2>Match Analysis</h2>
              <button className="reset-btn" onClick={handleReset}>← New Analysis</button>
            </div>

            {/* Row 1: main score + mini scores */}
            <div className="top-row">
              <div className="card main-card" style={{ background: scoreBg(result.match_percentage) }}>
                <h3>Overall Suitability Score</h3>
                <ScoreRing score={result.match_percentage} />
                <p className="score-sub">
                  Blended from keyword coverage, section alignment, and skill cluster analysis
                </p>
              </div>

              <div className="card mini-card">
                <h3>Score Breakdown</h3>
                <div className="mini-grid">
                  <MiniRing score={result.ats_score} label="ATS Score" />
                  <MiniRing score={result.keyword_coverage} label="Keyword Coverage" />
                  <MiniRing score={result.experience_match} label="Experience Match" />
                  <MiniRing score={result.projects_match} label="Projects Match" />
                  <MiniRing score={result.cluster_score} label="Cluster Coverage" />
                  <MiniRing score={result.weighted_score} label="Weighted Sections" />
                </div>
              </div>
            </div>

            {/* Row 2: section bars + reasoning */}
            <div className="mid-row">
              <div className="card">
                <h3>📊 Section Breakdown</h3>
                <p className="section-sub">Skills 35% · Experience 35% · Projects 20% · Education 5% · Certs 5%</p>
                <div className="bars">
                  {sectionMeta.map(({ key, label, weight }) => (
                    <Bar key={key} label={label} value={result.section_scores?.[key] ?? 0} weight={weight} />
                  ))}
                </div>
              </div>

              <ReasoningPanel reasoning={result.reasoning} />
            </div>

            {/* Row 3: skill clusters */}
            {result.cluster_results && Object.keys(result.cluster_results).length > 0 && (
              <div className="card">
                <h3>🧩 Skill Cluster Analysis</h3>
                <p className="section-sub">
                  <span className="legend-item"><span className="dot matched" />Exact match</span>
                  <span className="legend-item"><span className="dot partial" />Transferable (partial credit)</span>
                  <span className="legend-item"><span className="dot missing" />Missing</span>
                </p>
                <div className="cluster-grid">
                  {Object.entries(result.cluster_results).map(([name, data]) => (
                    <ClusterCard key={name} name={name} data={data} />
                  ))}
                </div>
              </div>
            )}

            {/* Row 4: keyword lists */}
            <div className="kw-row">
              <div className="card">
                <h3>✅ Matched Keywords</h3>
                <p className="kw-count">{result.matched_keywords?.length} exact matches</p>
                <div className="kw-list">
                  {result.matched_keywords?.length > 0
                    ? result.matched_keywords.map(k => <Badge key={k} word={k} type="matched" />)
                    : <p className="kw-empty">None found.</p>}
                </div>
              </div>

              {result.partial_keywords?.length > 0 && (
                <div className="card">
                  <h3>🔄 Transferable Matches</h3>
                  <p className="kw-count">{result.partial_keywords.length} partial-credit matches</p>
                  <div className="kw-list">
                    {result.partial_keywords.map(p => (
                      <span key={p.keyword} className="badge badge-partial" title={`${Math.round(p.credit * 100)}% credit`}>
                        {p.keyword} <span className="partial-credit">{Math.round(p.credit * 100)}%</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="card">
                <h3>❌ Missing Keywords</h3>
                <p className="kw-count">{result.missing_keywords?.length} not found</p>
                <div className="kw-list">
                  {result.missing_keywords?.length > 0
                    ? result.missing_keywords.map(k => <Badge key={k} word={k} type="missing" />)
                    : <p className="kw-empty">All key terms covered! 🎉</p>}
                </div>
              </div>
            </div>

            {/* Tips */}
            <div className="card">
              <h3>💡 Improvement Tips</h3>
              <ul className="tips">
                {result.match_percentage >= 80 && <li>Excellent fit — tailor your cover letter to emphasise your key projects.</li>}
                {result.match_percentage >= 70 && result.match_percentage < 80 && <li>Strong match — a few targeted additions could push you to excellent.</li>}
                {result.match_percentage >= 50 && result.match_percentage < 70 && <li>Solid foundation — bridge the gaps in your weaker sections to become a top candidate.</li>}
                {result.match_percentage < 50 && <li>Consider upskilling in the clusters marked ❌ before applying.</li>}
                {result.missing_keywords?.length > 0 && (
                  <li>Add these JD terms where applicable: <strong>{result.missing_keywords.slice(0, 6).join(', ')}</strong></li>
                )}
                {result.section_scores?.experience < 40 && (
                  <li>Rewrite experience bullets using terminology from the job description.</li>
                )}
                {result.section_scores?.projects < 30 && (
                  <li>Highlight projects that use technologies listed in the JD.</li>
                )}
                <li>Quantify results (e.g. "improved load time by 40%") to stand out to recruiters.</li>
              </ul>
            </div>

            <DebugPanel debug={result.debug} />
          </div>
        )}
      </main>

      <footer className="app-footer">
        Resume JD Matcher · Skill clusters · Transferable credit · Recruiter-style scoring
      </footer>
    </div>
  );
}
