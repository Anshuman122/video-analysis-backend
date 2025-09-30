import React from "react";

function ReportViewer({ report }) {

  if (!report) {
    return <p>Submit a video to analyze or select a job from the history.</p>;
  }

 
  if (report.error) {
    return <p style={{ color: 'red' }}>An error occurred: {report.error}</p>;
  }

  const { job_id, input, comparison } = report;
  const mismatches = comparison?.mismatches || [];
  const spelling_errors = comparison?.spelling_errors || [];

  return (
    <div className="report-viewer">
      <h3>Job ID: {job_id}</h3>
      <p><strong>Input:</strong> {input}</p>
      
      <div className="mismatches">
        <h4>Mismatches</h4>
        {mismatches.length > 0 ? (
          <ul>
            {mismatches.map((item, index) => (
              <li key={index}>
                <strong>Time: {item.time}</strong> - {item.detail}
              </li>
            ))}
          </ul>
        ) : (
          <p>No mismatches found.</p>
        )}
      </div>

      <div className="spelling-errors">
        <h4>Spelling Errors</h4>
        {spelling_errors.length > 0 ? (
          <ul>
            {spelling_errors.map((item, index) => (
              <li key={index}>
                <strong>Time: {item.time}</strong> - Found "<em>{item.word}</em>"
              </li>
            ))}
          </ul>
        ) : (
          <p>No spelling errors found.</p>
        )}
      </div>
    </div>
  );
}

export default ReportViewer;
