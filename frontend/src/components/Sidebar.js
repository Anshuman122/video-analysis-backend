import React from "react";

function Sidebar({ history, setSelectedJob }) {
  return (
    <div className="sidebar">
      <h2>📜 History</h2>
      <ul>
        {history.map((item) => (
          <li key={item.job_id} onClick={() => setSelectedJob(item)}>
            <p>{item.job_id}</p>
            <a href={item.link} target="_blank" rel="noopener noreferrer">
              Download JSON
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Sidebar;
