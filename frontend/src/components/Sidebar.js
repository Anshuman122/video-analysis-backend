import React from "react";

function Sidebar({ history, setSelectedJob, handleDownload }) {
  return (
    <div className="sidebar">
      <h2> 📜 History</h2>
      <ul>
        {history.length > 0 ? (
          history.map((item) => (
            // The key should use the unique ID from the database
            <li key={item.id}> 
              <div
                className="sidebar-item"
                onClick={() => setSelectedJob(item)}
                title="Click to view report"
              >
                {/* Display the job ID */}
                <span>Job ID: {item.id}</span> 
              </div>
              {/* The download button must also use item.id */}
              <button onClick={() => handleDownload(item.id)}> 
                Download
              </button>
            </li>
          ))
        ) : (
          <p className="no-history">No history yet.</p>
        )}
      </ul>
    </div>
  );
}

export default Sidebar;