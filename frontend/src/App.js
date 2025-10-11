import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import Sidebar from "./components/Sidebar";
import AnalysisPanel from "./components/AnalysisPanel";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL;

function App() {
  const [history, setHistory] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [latestReport, setLatestReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [pollingJobId, setPollingJobId] = useState(null);

  const pollingIntervalRef = useRef(null);

  // Function to fetch history
  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_URL}/history`);
      setHistory(res.data);
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  };

  // useEffect to fetch history on initial load
  useEffect(() => {
    fetchHistory();
  }, []);

  // useEffect to handle polling
  useEffect(() => {
    // Stop any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    // If there's a new job to poll for, start polling
    if (pollingJobId) {
      pollingIntervalRef.current = setInterval(async () => {
        try {
          const res = await axios.get(`${API_URL}/status/${pollingJobId}`);
          if (res.data.status === "completed") {
            console.log("Job completed! Fetching final report.");
            clearInterval(pollingIntervalRef.current); // Stop polling
            setPollingJobId(null);
            setIsLoading(false);
            setLatestReport(res.data.result);
            fetchHistory(); // Refresh the history list
          } else if (res.data.status === "failed") {
            console.error("Job failed!");
            clearInterval(pollingIntervalRef.current);
            setPollingJobId(null);
            setIsLoading(false);
            alert("Analysis failed on the backend.");
          } else {
            console.log("Job status:", res.data.status); // e.g., "processing"
          }
        } catch (err) {
          console.error("Error during polling:", err);
          clearInterval(pollingIntervalRef.current);
          setPollingJobId(null);
          setIsLoading(false);
          alert("Error checking job status.");
        }
      }, 5000); // Poll every 5 seconds
    }

    // Cleanup function to stop polling when the component unmounts
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [pollingJobId]);

  const handleAnalyze = async (videoUrl) => {
    setLatestReport(null);
    setSelectedJob(null);
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("video_url", videoUrl);
      const res = await axios.post(`${API_URL}/analyze`, formData);
      
      // The backend now immediately returns a job ID
      const { job_id } = res.data;
      if (job_id) {
        console.log("Analysis started for job ID:", job_id);
        setPollingJobId(job_id); // This will trigger the polling useEffect
      }
    } catch (err) {
      alert("Error starting analysis");
      console.error(err);
      setIsLoading(false);
    }
  };

  const handleDownload = (jobId) => {
    const link = document.createElement('a');
    link.href = `${API_URL}/download/${jobId}`;
    link.click();
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
        isLoading={isLoading}
      />
    </div>
  );
}

export default App;