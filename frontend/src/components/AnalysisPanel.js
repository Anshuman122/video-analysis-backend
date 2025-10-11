import React, { useState } from "react";
import ReportViewer from "./ReportViewer";



function AnalysisPanel({ selectedJob, latestReport, handleAnalyze , isLoading}) {
  const [videoLink, setVideoLink] = useState("");

  
  const onAnalyzeClick = () => {
    if (!videoLink) {
      alert("Please enter a video link.");
      return;
    }
    console.log("Analyze video:", videoLink);
    
    handleAnalyze(videoLink);
  };

  return (
    <div className="analysis-panel">
      <h1>🎥 Video Analysis</h1>
      <div className="input-section">
        <input
          type="text"
          placeholder="Enter Google Drive or Direct Video Link..."
          value={videoLink}
          onChange={(e) => setVideoLink(e.target.value)}
        />
        {/* 3. The button calls our local onAnalyzeClick function */}
        <button onClick={onAnalyzeClick} disabled={isLoading}>
               {isLoading ? "Analyzing..." : "Analyze"}
               {isLoading && <p className="loading-message">Processing video, this may take several minutes...</p>}
          </button>
      </div>

      <div className="report-section">
        <h2>Report Details</h2>
        {/* 4. This now correctly displays either the latest report or a selected one */}
        <ReportViewer report={latestReport || selectedJob} />
      </div>
    </div>
  );
}

export default AnalysisPanel;
