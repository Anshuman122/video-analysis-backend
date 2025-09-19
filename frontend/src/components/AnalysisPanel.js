import React, { useState } from "react";

function AnalysisPanel({ selectedJob }) {
  const [videoLink, setVideoLink] = useState("");

  const handleAnalyze = () => {
    console.log("Analyze video:", videoLink);
    // Call backend API with axios here
  };

  return (
    <div className="analysis-panel">
      <h1>🎥 Video Analysis</h1>
      <div className="input-section">
        <input
          type="text"
          placeholder="Enter Google Drive Video Link..."
          value={videoLink}
          onChange={(e) => setVideoLink(e.target.value)}
        />
        <button onClick={handleAnalyze}>Analyze</button>
      </div>

      <div className="report-section">
        <h2>Latest Report</h2>
        {selectedJob ? (
          <div>
            <p><strong>Job ID:</strong> {selectedJob.job_id}</p>
            <a href={selectedJob.link} download>
              Download JSON
            </a>
          </div>
        ) : (
          <p>No report selected yet.</p>
        )}
      </div>
    </div>
  );
}

export default AnalysisPanel;
