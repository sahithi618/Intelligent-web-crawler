import React, { useEffect, useState } from "react";
import { analyzeText } from "../api";
import Result from "./Result";

function Dashboard({ token, logout }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);

  const delay = (ms) => new Promise((res) => setTimeout(res, ms));

  const runQuery = async (query) => {
    if (!query || !query.trim() || loading) return;
    setText(query);
    setLoading(true);
    setResult(null);
    setStep(1);

    await delay(300);
    setStep(2);
    await delay(300);
    setStep(3);
    await delay(300);
    setStep(4);
    await delay(300);
    setStep(5);

    try {
      const data = await analyzeText(query.trim(), token);
      setResult(data);
      setStep(6);
    } catch (error) {
      setResult({ error: error.message || "Something went wrong while contacting the crawler." });
      setStep(0);
    } finally {
      setLoading(false);
    }
  };

  const detect = () => runQuery(text);

  useEffect(() => {
    const handleFollowUp = (event) => runQuery(event.detail);
    window.addEventListener("truthshield-follow-up", handleFollowUp);
    return () => window.removeEventListener("truthshield-follow-up", handleFollowUp);
  }, [loading, token]);

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      detect();
    }
  };

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h4 style={{ margin: 0, color: "#a855f7" }}>🛡️ SearchShield AI Workspace</h4>
        <button onClick={logout} className="btn btn-secondary" style={{ padding: "8px 16px", borderRadius: "10px" }}>Logout</button>
      </div>

      <p style={{ color: "#9ca3af", textAlign: "left", marginBottom: "24px" }}>
        Ask a question, find jobs or products, discover events, or locate services. SearchShield AI interprets the request, searches and crawls relevant pages, ranks the evidence, and provides an answer with intent-aware next steps.
      </p>

      <div style={{ position: "relative" }}>
        <textarea
          rows="3"
          placeholder="Try: 'Find remote Python developer jobs posted this week' or 'What's the best budget mechanical keyboard?'
          "
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyPress}
          style={{ resize: "vertical", minHeight: "80px" }}
        />
      </div>

      <div style={{ display: "flex", gap: "12px", justifyContent: "flex-start", marginBottom: "20px" }}>
        <button onClick={detect} disabled={loading} style={{ flex: 1 }}>
          {loading ? "Crawling & Answering..." : "Search & Crawl 🚀"}
        </button>
      </div>

      {loading && (
        <div className="pipeline-container animate-fade-in">
          <h6 style={{ margin: "0 0 14px 0", color: "#9ca3af", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "1px" }}>Execution Pipeline</h6>
          <div className={`pipeline-step ${step === 1 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 1 ? 1 : 0.25 }}>{step > 1 ? "✅" : "🎯"} Classifying query intent...</div>
          <div className={`pipeline-step ${step === 2 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 2 ? 1 : 0.25 }}>{step > 2 ? "✅" : "🔍"} Planning and searching the web...</div>
          <div className={`pipeline-step ${step === 3 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 3 ? 1 : 0.25 }}>{step > 3 ? "✅" : "🕷️"} Crawling matching pages...</div>
          <div className={`pipeline-step ${step === 4 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 4 ? 1 : 0.25 }}>{step > 4 ? "✅" : "📊"} Ranking evidence with TF-IDF...</div>
          <div className={`pipeline-step ${step === 5 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 5 ? 1 : 0.25 }}>{step > 5 ? "✅" : "⚡"} Detecting actions and follow-ups...</div>
        </div>
      )}

      <Result result={result} />
    </>
  );
}

export default Dashboard;
