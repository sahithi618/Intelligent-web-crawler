import React, { useState } from "react";
import { analyzeText } from "../api";
import Result from "./Result";

function Dashboard({ token, logout }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(0);

  // Helper delay to visual progress
  const delay = (ms) => new Promise((res) => setTimeout(res, ms));

  const detect = async () => {
    if (!text || text.trim() === "") {
      alert("⚠️ Please enter a search query or question");
      return;
    }

    setLoading(true);
    setResult(null);
    setStep(0);

    // Simulate pipeline phases visually
    setStep(1);
    await delay(700);

    setStep(2);
    await delay(700);

    setStep(3);
    await delay(800);

    setStep(4);
    await delay(700);

    setStep(5);

    try {
      const data = await analyzeText(text, token);
      setResult(data);
      setStep(6); // Done
    } catch (error) {
      setResult({ error: "Something went wrong" });
      setStep(0);
    }

    setLoading(false);
  };

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
        <button onClick={logout} className="btn btn-secondary" style={{ padding: "8px 16px", borderRadius: "10px" }}>
          Logout
        </button>
      </div>

      <p style={{ color: "#9ca3af", textAlign: "left", marginBottom: "24px" }}>
        Enter a question, search for reviews, or query job boards. SearchShield AI will crawl relevant pages, rank them by relevance, and present cited answers.
      </p>

      <div style={{ position: "relative" }}>
        <textarea
          rows="3"
          placeholder="Ask me anything... (e.g., 'Find me remote Python developer jobs' or 'What's the best budget mechanical keyboard?')"
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

      {/* PIPELINE PROGRESS INDICATOR */}
      {loading && (
        <div className="pipeline-container animate-fade-in">
          <h6 style={{ margin: "0 0 14px 0", color: "#9ca3af", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "1px" }}>
            Execution Pipeline
          </h6>
          <div className={`pipeline-step ${step === 1 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 1 ? 1 : 0.25 }}>
            {step > 1 ? "✅" : "🎯"} Classifying query intent...
          </div>
          <div className={`pipeline-step ${step === 2 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 2 ? 1 : 0.25 }}>
            {step > 2 ? "✅" : "🔍"} Searching the web...
          </div>
          <div className={`pipeline-step ${step === 3 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 3 ? 1 : 0.25 }}>
            {step > 3 ? "✅" : "🕷️"} Crawling matching pages...
          </div>
          <div className={`pipeline-step ${step === 4 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 4 ? 1 : 0.25 }}>
            {step > 4 ? "✅" : "📊"} Ranking by relevance (TF-IDF)...
          </div>
          <div className={`pipeline-step ${step === 5 ? "pipeline-step-active" : ""}`} style={{ opacity: step >= 5 ? 1 : 0.25 }}>
            {step > 5 ? "✅" : "💬"} Synthesizing answer & actions...
          </div>
        </div>
      )}

      {/* RENDER RESULT */}
      <Result result={result} />
    </>
  );
}

export default Dashboard;