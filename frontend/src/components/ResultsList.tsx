import { useState } from "react";
import { Link } from "react-router-dom";
import "./ResultsList.css";

export default function ResultsList({ results }: { results: any[] }) {
  // --- Pagination settings ---
  const RESULTS_PER_PAGE = 5;
  const [page, setPage] = useState(1);

  // Compute total pages
  const totalPages = Math.ceil(results.length / RESULTS_PER_PAGE);

  // Slice results for current page
  const startIndex = (page - 1) * RESULTS_PER_PAGE;
  const shownResults = results.slice(startIndex, startIndex + RESULTS_PER_PAGE);

  const openCloud = (filename: string) => {
    const event = new CustomEvent("openWordCloud", { detail: { filename } });
    window.dispatchEvent(event);
  };

  if (!results || results.length === 0) {
    return <p className="results-empty">No documents found.</p>;
  }

  return (
    <div className="google-results">

      {/* Results */}
      {shownResults.map((item, index) => (
        <div key={index} className="google-card">

          <Link
            to={`/view/${item.filename}`}
            className="google-title"
            target="_blank"
            rel="noopener noreferrer"
            >
            {item.filename}
          </Link>
          
            <button 
              className="wc-btn" 
              onClick={() => openCloud(item.filename)}
            >
              ☁️
            </button>
            <div className="score-tag">{item.score}</div>
          <p className="google-path">Documents/{item.path}</p>
            
          <p className="google-snippet">{item.snippet}</p>
           {/* --- 
          <div className="google-actions">
             
          </div> --- */}
        </div>
      ))}

      {/* --- PAGINATION CONTROLS --- */}
      <div className="pagination">

        <button
          className="pg-btn"
          disabled={page === 1}
          onClick={() => setPage(page - 1)}
        >
          ◀ Previous
        </button>

        {/* Page numbers like Google */}
        <div className="pg-numbers">
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((num) => (
            <button
              key={num}
              className={`pg-number ${num === page ? "active" : ""}`}
              onClick={() => setPage(num)}
            >
              {num}
            </button>
          ))}
        </div>

        <button
          className="pg-btn"
          disabled={page === totalPages}
          onClick={() => setPage(page + 1)}
        >
          Next ▶
        </button>

      </div>
    </div>
  );
}
