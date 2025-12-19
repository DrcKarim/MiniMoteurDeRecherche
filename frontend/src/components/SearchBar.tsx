import { useState, useEffect } from "react";
import { getSuggestions } from "../services/api";
import "./SearchBar.css";

interface Props {
  onSearch: (q: string) => void;
  keyword?: string;
}

export default function SearchBar({ onSearch, keyword }: Props) {
  const [query, setQuery] = useState(keyword || "");
  const [suggestions, setSuggestions] = useState<string[]>([]);

  //  Keep input synced when Home updates keyword
  useEffect(() => {
    if (keyword !== undefined) {
      setQuery(keyword);
    }
  }, [keyword]);

  //  Suggestion logic
  useEffect(() => {
    if (!query || query.trim().length < 3) {
      setSuggestions([]);
      return;
    }

    const timeout = setTimeout(async () => {
      const data = await getSuggestions(query);
      setSuggestions(data.suggestions || []);
    }, 300);

    return () => clearTimeout(timeout);
  }, [query]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setSuggestions([]); // hide suggestions
    onSearch(query);
  };

  return (
    <div className="searchbar-wrapper">
      <form onSubmit={submit} className="searchbar-container">
        <input
          type="text"
          placeholder="Search documents…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="search-input"
        />

        <button type="submit" className="search-button">
          Search
        </button>
      </form>

      {/* Suggestion dropdown */}
      {suggestions.length > 0 && (
        <div className="suggest-box">
        {/*   <p>Did you mean:</p>  */}
          <ul>
            {suggestions.map((s, i) => (
              <li
                key={i}
                onClick={() => {
                  setQuery(s);        // fill input
                  setSuggestions([]); // hide suggestions
                }}
              >
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
