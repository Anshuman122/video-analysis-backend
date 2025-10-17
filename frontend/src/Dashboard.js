import React, { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import { useAuth0 } from "@auth0/auth0-react";
import Sidebar from "./components/Sidebar";
import AnalysisPanel from "./components/AnalysisPanel";
import "./App.css";

const API_URL = process.env.REACT_APP_API_URL;

function Dashboard() {
  const { getAccessTokenSilently, isAuthenticated } = useAuth0();
  const [history, setHistory] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [latestReport, setLatestReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [pollingJobId, setPollingJobId] = useState(null);

  const pollingIntervalRef = useRef(null);

  const fetchHistory = useCallback(async () => {
    try {
      const token = await getAccessTokenSilently();
      const res = await axios.get(`${API_URL}/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setHistory(res.data);
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  }, [getAccessTokenSilently]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchHistory();
    }
  }, [isAuthenticated, fetchHistory]);

  useEffect(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    if (pollingJobId) {
      pollingIntervalRef.current = setInterval(async () => {
        try {
          const token = await getAccessTokenSilently();
          const res = await axios.get(`${API_URL}/status/${pollingJobId}`, {
            headers: { Authorization: `Bearer ${token}` },
          });

          if (res.data.status === "completed") {
            clearInterval(pollingIntervalRef.current);
            setPollingJobId(null);
            setIsLoading(false);
            setLatestReport(res.data.result);
            fetchHistory();
          } else if (res.data.status === "failed") {
            clearInterval(pollingIntervalRef.current);
            setPollingJobId(null);
            setIsLoading(false);
            alert("Analysis failed on the backend.");
          }
        } catch (err) {
          clearInterval(pollingIntervalRef.current);
          setPollingJobId(null);
          setIsLoading(false);
          alert("Error checking job status.");
        }
      }, 5000);
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [pollingJobId, getAccessTokenSilently, fetchHistory]);

  const handleAnalyze = async (videoUrl) => {
    console.log("1. 'Analyze' button clicked. Starting handleAnalyze.");
    setLatestReport(null);
    setSelectedJob(null);
    setIsLoading(true);

    try {
      console.log("2. Inside try block. Checking for getAccessTokenSilently function...");
      console.log("Is getAccessTokenSilently a function?", typeof getAccessTokenSilently);

      if (typeof getAccessTokenSilently !== 'function') {
        throw new Error("Auth0's getAccessTokenSilently function is not available.");
      }

      console.log("3. Attempting to get token from Auth0...");
      const token = await getAccessTokenSilently();
      console.log("4. Successfully got a token.");

      const formData = new FormData();
      formData.append("video_url", videoUrl);

      console.log("5. Sending API request to /analyze...");
      const res = await axios.post(`${API_URL}/analyze`, formData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      console.log("6. API request successful.");
      const { job_id } = res.data;
      if (job_id) {
        setPollingJobId(job_id);
      }
    } catch (err) {
      // This will now log the specific error object
      console.error("💥 ERROR caught in handleAnalyze:", err);
      alert("Error starting analysis. Check the console for details.");
      setIsLoading(false);
    }
  };

  const handleDownload = async (jobId) => {
    try {
      const token = await getAccessTokenSilently();
      const res = await axios.get(`${API_URL}/download/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob",
      });

      const blob = new Blob([res.data], { type: "application/json" });
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `${jobId}_report.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error("Download failed", error);
      alert("Could not download the report.");
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
        isLoading={isLoading}
      />
    </div>
  );
}

export default Dashboard;

