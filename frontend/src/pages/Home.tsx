import { useEffect, useState } from "react";
import SearchBar from "../components/SearchBar";
import ResultsList from "../components/ResultsList";
import { searchDocuments } from "../services/api";
import "./Home.css";

export default function Home() {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");

  const handleSearch = async (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    const data = await searchDocuments(q);
    setResults(data.results || []);
    setLoading(false);
  };

  // ⭐ Cloud click -> ONLY fill the input (no search)
  useEffect(() => {
    const listener = (e: any) => {
      const word = e.detail?.word;
      if (word) {
        setQuery(word); // <– puts the word into input
      }
    };

    window.addEventListener("searchFromCloud", listener);
    return () => window.removeEventListener("searchFromCloud", listener);
  }, []);

  return (
    <div className="container">
      <h1 className="title">🔍 DocuFind</h1>

      <div className="search-section">
        <SearchBar 
          onSearch={handleSearch}
          keyword={query}   // <-- send the cloud word to SearchBar
        />
      </div>

      <div className="results-section">
        {loading ? <p>Searching…</p> : <ResultsList results={results} />}
      </div>
    </div>
  );
}
