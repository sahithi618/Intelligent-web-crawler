import React from "react";

function Result({ result }) {
  if (!result) return null;

  if (result === "loading") {
    return (
      <div className="pipeline-container animate-fade-in" style={{ textAlign: "center", padding: "30px" }}>
        <div className="spinner" style={{ fontSize: "1.8rem", marginBottom: "10px" }}>🔍</div>
        <p>Analyzing and crawling web content...</p>
      </div>
    );
  }

  if (result.error) {
    return <div className="action-guidance-card"><div className="action-guidance-body"><h6>Unable to complete search</h6><p>{result.error}</p></div></div>;
  }

  const synthesizedAnswer = result.synthesized_answer || result.user_friendly?.summary;
  const keyPoints = result.key_points || [];
  const actionPrompt = result.action_prompt || result.recommendation;
  const actionableSteps = result.actionable_steps || [];
  const followUps = result.follow_up_questions || [];
  const jobs = result.jobs || [];
  const products = result.products || [];
  const events = result.events || [];
  const sources = result.sources || [];
  const intent = result.intent || "general";
  const actionable = Boolean(result.actionable || actionPrompt);
  const actionType = result.action_type || "none";
  const confidenceScore = result.confidence_score || result.combined_score || result.user_friendly?.confidence_score || "—";
  const confidenceLevel = result.confidence_level || result.user_friendly?.confidence_level || "medium";

  const sendFollowUp = (question) => {
    window.dispatchEvent(new CustomEvent("truthshield-follow-up", { detail: question }));
  };

  return (
    <div className="result-container animate-fade-in">
      <div className="result-header">
        <span className="badge badge-intent">Intent: {intent.toUpperCase()}</span>
        <span className={`badge badge-conf-${confidenceLevel}`}>Match confidence: {confidenceScore}</span>
      </div>

      {synthesizedAnswer && (
        <div className="answer-section">
          <h4>🧠 Synthesized Answer</h4>
          <p className="main-answer-text">{synthesizedAnswer}</p>
        </div>
      )}

      {keyPoints.length > 0 && (
        <div className="key-points-section">
          <h5>📌 Key Highlights</h5>
          <ul className="key-points-list">{keyPoints.map((point, index) => <li key={index}>{point}</li>)}</ul>
        </div>
      )}

      {actionable && actionPrompt && (
        <div className="action-guidance-card">
          <div className="action-guidance-icon">⚡</div>
          <div className="action-guidance-body">
            <h6>Next Step · {actionType !== "none" ? actionType.toUpperCase() : "ACTION"}</h6>
            <p>{actionPrompt}</p>
            {actionableSteps.length > 0 && (
              <ol className="action-steps-list">
                {actionableSteps.map((step, index) => <li key={index}>{step}</li>)}
              </ol>
            )}
          </div>
        </div>
      )}

      {intent === "jobs" && jobs.length > 0 && (
        <div className="jobs-section animate-fade-in">
          <h5>💼 Matching Openings Found</h5>
          <div className="jobs-grid">
            {jobs.map((job, idx) => (
              <div key={idx} className="job-card">
                <div className="job-card-header"><span className="job-match-badge">{job.match_score}% Match</span></div>
                <h6 className="job-title">{job.title}</h6>
                <div className="job-company">{job.company}</div>
                <div className="job-details"><span>📍 {job.location}</span>{job.salary_range && job.salary_range !== "Not specified" && <span>💵 {job.salary_range}</span>}</div>
                <a href={job.apply_url} target="_blank" rel="noopener noreferrer" className="btn btn-apply">View / Apply 🚀</a>
              </div>
            ))}
          </div>
        </div>
      )}

      {intent === "products" && products.length > 0 && (
        <div className="jobs-section animate-fade-in">
          <h5>🛍️ Recommended Products Found</h5>
          <div className="jobs-grid">
            {products.map((product, idx) => (
              <div key={idx} className="job-card">
                {product.rating && product.rating !== "Not specified" && <div className="job-card-header"><span className="job-match-badge">⭐ {product.rating}</span></div>}
                <h6 className="job-title">{product.name}</h6>
                <div className="job-company">💵 {product.price || "Not specified"}</div>
                <p className="source-snippet">{product.description}</p>
                <a href={product.source_url} target="_blank" rel="noopener noreferrer" className="btn btn-apply">View Product 🛒</a>
              </div>
            ))}
          </div>
        </div>
      )}

      {intent === "events" && events.length > 0 && (
        <div className="jobs-section animate-fade-in">
          <h5>📅 Upcoming Events & Hackathons</h5>
          <div className="jobs-grid">
            {events.map((event, idx) => (
              <div key={idx} className="job-card">
                <div className="job-card-header"><span className="job-match-badge">📅 {event.date || "Upcoming"}</span></div>
                <h6 className="job-title">{event.name}</h6>
                <div className="job-company">📍 {event.location || "Multiple locations"}</div>
                <p className="source-snippet">{event.description}</p>
                <a href={event.url} target="_blank" rel="noopener noreferrer" className="btn btn-apply">Register / Details 🎟️</a>
              </div>
            ))}
          </div>
        </div>
      )}

      {followUps.length > 0 && (
        <div className="follow-up-section">
          <h5>💡 Continue with the crawler</h5>
          <p className="follow-up-subtitle">These questions are based on your current search and can trigger a new targeted crawl.</p>
          <div className="follow-up-list">
            {followUps.map((question, index) => (
              <button key={index} className="follow-up-chip" onClick={() => sendFollowUp(question)}>{question} →</button>
            ))}
          </div>
        </div>
      )}

      {sources.length > 0 && (
        <div className="sources-section">
          <h5>🔗 Cited Sources & References</h5>
          <div className="sources-list">
            {sources.map((source, idx) => (
              <div key={idx} className="source-card">
                <div className="source-card-header">
                  <span className="source-rank">#{source.rank || idx + 1}</span>
                  <a href={source.url} target="_blank" rel="noopener noreferrer" className="source-title">{source.title}</a>
                </div>
                <p className="source-snippet">{source.snippet}</p>
                <div className="source-metadata"><span className="source-domain">🌐 {source.domain}</span><span className="source-score">Relevance: {source.relevance_score}%</span></div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Result;
