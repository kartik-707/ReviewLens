/**
 * App.jsx
 * Root component for the ReviewLens dashboard.
 * Orchestrates search, state, and all dashboard sections.
 */
import { useState, useRef } from "react";
import useInsights from "./hooks/useInsights";
import AspectChart from "./components/AspectChart";
import EvidenceCard from "./components/EvidenceCard";

const SAMPLE_IDS = [
  "AVphgVaX1cnluZ0-DR74",
  "AVpfl8cLLJeJML43AE3S",
  "AV1YE_muvKc47QAVgpwE",
  "AVqkIhwDv8e3D1O-lebb",
  "AV1YnRtnglJLPUi8IJmV",
];

export default function App() {
  const [query, setQuery]   = useState("");
  const { data, loading, error, queried, search } = useInsights();
  const inputRef = useRef(null);

  const handleSearch = (pid) => {
    const id = pid ?? query;
    if (id.trim()) search(id.trim());
  };

  const handleSample = (id) => { setQuery(id); search(id); };

  const stars = data
    ? "★".repeat(Math.round(data.overall.average_rating)) +
      "☆".repeat(5 - Math.round(data.overall.average_rating))
    : "";

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <div className="logo-group">
          <div className="logo">Review<span>Lens</span></div>
          <div className="tagline">Aspect-Level Sentiment Intelligence</div>
        </div>
        <div className="header-meta">
          Amazon Product Reviews<br />
          NLP · VADER · Aspect Mining
        </div>
      </header>

      {/* ── Search ── */}
      <div className="search-section">
        <label className="search-label" htmlFor="pid">Product ID</label>
        <div className="search-row">
          <input
            id="pid"
            ref={inputRef}
            className="search-input"
            placeholder="e.g. AVphgVaX1cnluZ0-DR74"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleSearch()}
            spellCheck={false}
          />
          <button
            className="search-btn"
            onClick={() => handleSearch()}
            disabled={loading || !query.trim()}
          >
            {loading ? <span className="spinner" /> : "Analyse"}
          </button>
        </div>
        <div className="sample-ids">
          <span className="sample-label">Try:</span>
          {SAMPLE_IDS.map(id => (
            <button key={id} className="sample-chip" onClick={() => handleSample(id)}>
              {id.slice(0, 16)}…
            </button>
          ))}
        </div>
      </div>

      {/* ── Empty state ── */}
      {!queried && !loading && (
        <div className="state-box">
          <div className="state-icon">🔍</div>
          <div className="state-title">Enter a Product ID</div>
          <div className="state-sub">
            Enter an Amazon product ID above to generate<br />
            aspect-level sentiment insights from customer reviews.
          </div>
        </div>
      )}

      {/* ── Loading state ── */}
      {loading && (
        <div className="state-box">
          <div className="loading-dots">
            <div className="dot" /><div className="dot" /><div className="dot" />
          </div>
          <div className="state-title">Analysing reviews…</div>
          <div className="state-sub">Running NLP pipeline · extracting aspects · scoring sentiment</div>
        </div>
      )}

      {/* ── Error state ── */}
      {error && !loading && (
        <div className="error-box">
          <div className="error-title">⚠ Could not load insights</div>
          <div>{error}</div>
        </div>
      )}

      {/* ── Dashboard ── */}
      {data && !loading && (
        <div className="dashboard">

          {/* Stat cards */}
          <div className="section-title">Overview</div>
          <div className="overview-row">
            <div className="stat-card green">
              <div className="stat-value">{data.overall.average_rating.toFixed(1)}</div>
              <div className="stat-label">Avg Rating</div>
              <div style={{ marginTop: 4, fontSize: "0.78rem", color: "#b5893a", letterSpacing: "0.05em" }}>{stars}</div>
            </div>
            <div className="stat-card">
              <div className="stat-value">{data.review_count.toLocaleString()}</div>
              <div className="stat-label">Reviews</div>
            </div>
            <div className="stat-card gold">
              <div className="stat-value">{data.aspects.length}</div>
              <div className="stat-label">Aspects Found</div>
            </div>
            <div className="stat-card muted">
              <div className="stat-value">
                {Math.round(data.overall.confidence)}
                <span style={{ fontSize: "1rem", opacity: 0.5 }}>/100</span>
              </div>
              <div className="stat-label">Confidence</div>
            </div>
          </div>

          {/* Summary */}
          <div className="summary-card">
            <div className="product-id">PRODUCT · {data.product_id}</div>
            <div className="narrative">{data.overall.narrative}</div>
            <div className="confidence-row">
              <div className="conf-bar-track">
                <div className="conf-bar-fill" style={{ width: `${data.overall.confidence}%` }} />
              </div>
              <div className="conf-label">Confidence {data.overall.confidence.toFixed(0)}%</div>
            </div>
          </div>

          {/* Aspect chart */}
          {data.aspects.length > 0 && (
            <div className="chart-card">
              <div className="card-title">Aspect Sentiment Scores</div>
              <AspectChart aspects={data.aspects} />
              <div style={{ display: "flex", gap: 16, marginTop: 10, justifyContent: "center" }}>
                {[["#3d6b4f", "Positive"], ["#b03a2e", "Negative"], ["#7a7468", "Neutral"]].map(([c, l]) => (
                  <span key={l} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: "0.7rem", color: "var(--muted)", fontFamily: "DM Mono" }}>
                    <span style={{ width: 10, height: 10, borderRadius: 2, background: c, display: "inline-block" }} />
                    {l}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Aspects grid */}
          {data.aspects.length > 0 && (
            <>
              <div className="section-title">All Aspects</div>
              <div className="aspects-grid">
                {data.aspects.map(a => (
                  <div key={a.name} className="aspect-chip">
                    <div className="aspect-name">{a.name}</div>
                    <div className="aspect-mentions">{a.mention_count} mentions</div>
                    <div className="aspect-bar-track">
                      <div
                        className={`aspect-bar-fill ${a.sentiment === "Positive" ? "bar-pos" : a.sentiment === "Negative" ? "bar-neg" : "bar-neu"}`}
                        style={{ width: `${Math.abs(a.score) * 100}%` }}
                      />
                    </div>
                    <div className={`aspect-sentiment ${a.sentiment === "Positive" ? "sent-pos" : a.sentiment === "Negative" ? "sent-neg" : "sent-neu"}`}>
                      {a.sentiment} · {a.score > 0 ? "+" : ""}{a.score.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Pros & Cons */}
          {(data.pros.length > 0 || data.cons.length > 0) && (
            <>
              <div className="section-title">Evidence-Backed Pros &amp; Cons</div>
              <div className="pros-cons-grid">
                <div className="pc-card">
                  <div className="pc-header">
                    <span className="pc-badge badge-pro">Pros</span>
                    <span className="pc-header-title">What customers love</span>
                  </div>
                  {data.pros.length === 0
                    ? <div style={{ color: "var(--muted)", fontSize: "0.82rem" }}>No strong positives detected.</div>
                    : data.pros.map((p, i) => <EvidenceCard key={i} item={p} isPro={true} />)
                  }
                </div>
                <div className="pc-card">
                  <div className="pc-header">
                    <span className="pc-badge badge-con">Cons</span>
                    <span className="pc-header-title">Common complaints</span>
                  </div>
                  {data.cons.length === 0
                    ? <div style={{ color: "var(--muted)", fontSize: "0.82rem" }}>No significant negatives detected.</div>
                    : data.cons.map((c, i) => <EvidenceCard key={i} item={c} isPro={false} />)
                  }
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
