/**
 * EvidenceCard.jsx
 * Expandable card showing a single aspect with evidence quotes from reviews.
 * Evidence is always backed by actual review text - never generated content.
 */
import { useState } from "react";

export default function EvidenceCard({ item, isPro }) {
  const [open, setOpen] = useState(false);
  const score = isPro ? `+${item.score.toFixed(2)}` : item.score.toFixed(2);

  return (
    <div className="evidence-item">
      <button className="evidence-btn" onClick={() => setOpen(o => !o)}>
        <span className="evidence-aspect">{item.aspect}</span>
        <span className={`evidence-score ${isPro ? "score-pos" : "score-neg"}`}>{score}</span>
        <span className={`chevron ${open ? "open" : ""}`}>▼</span>
      </button>
      <div className={`evidence-quotes ${open ? "open" : ""}`}>
        {item.evidence.map((quote, i) => (
          <div key={i} className="quote-item">{quote}</div>
        ))}
      </div>
    </div>
  );
}
