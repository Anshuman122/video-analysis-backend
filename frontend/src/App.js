import React, { useState, useEffect } from "react";
import axios from "axios";
import Sidebar from "./components/Sidebar";
import AnalysisPanel from "./components/AnalysisPanel";
import "./App.css";

function App() {
  const [history, setHistory] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [latestReport, setLatestReport] = useState(null);

  // Fetch history on initial load
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/history");
      setHistory(res.data);
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  };

  // Submit video for analysis
  const handleAnalyze = async (videoUrl) => {
    setLatestReport(null);
    try {
      const formData = new FormData();
      formData.append("video_url", videoUrl);

      const res = await axios.post("http://127.0.0.1:8000/analyze", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setLatestReport(res.data);
      // Refresh history
      fetchHistory();
    } catch (err) {
      alert("Error analyzing video");
      console.error(err);
    }
  };

  // Download JSON report
  const handleDownload = async (jobId) => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/download/${jobId}`);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], {
        type: "application/json",
      });
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `${jobId}_report.json`;
      link.click();
    } catch (err) {
      alert("Error downloading report");
      console.error(err);
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        history={history}
        setSelectedJob={setSelectedJob}
        handleDownload={handleDownload}
      />
      <AnalysisPanel
        selectedJob={selectedJob}
        latestReport={latestReport}
        handleAnalyze={handleAnalyze}
      />
    </div>
  );
}

export default App;
