import { useEffect, useState } from "react";
import { getWordCloud } from "../services/api";
import "./WordCloudModal.css";

type CloudWord = {
  word: string;
  count: number;
};

export default function WordCloudModal() {
  const [isOpen, setOpen] = useState(false);
  const [filename, setFilename] = useState("");
  const [words, setWords] = useState<CloudWord[]>([]);
  const [selected, setSelected] = useState<string[]>([]); // NEW: selected words

  useEffect(() => {
    const listener = async (e: any) => {
      const file = e.detail?.filename;
      if (!file) return;

      setFilename(file);
      setOpen(true);
      setSelected([]); // reset selection

      try {
        const data = await getWordCloud(file);
        setWords(data.top_words || []);
      } catch (err) {
        console.error("Word cloud error:", err);
      }
    };

    window.addEventListener("openWordCloud", listener);
    return () => window.removeEventListener("openWordCloud", listener);
  }, []);

  if (!isOpen) return null;

  // Toggle selection of a word
  const toggleSelect = (word: string) => {
    setSelected((prev) =>
      prev.includes(word)
        ? prev.filter((w) => w !== word)
        : [...prev, word]
    );
  };

  // Send multi-word search
  const runMultiSearch = () => {
    if (!selected.length) return;
    const query = selected.join(" ");
    window.dispatchEvent(
      new CustomEvent("searchFromCloud", { detail: { word: query } })
    );
    setOpen(false);
  };

  const max = Math.max(...words.map((w) => w.count), 1);

  return (
    <div className="wc-overlay" onClick={() => setOpen(false)}>
      <div className="wc-box" onClick={(e) => e.stopPropagation()}>
        <button className="wc-close-btn" onClick={() => setOpen(false)}>
          ✕
        </button>

      {/*  <h2 className="wc-title">Nuage de mots — {filename}</h2> */}

        <div className="wc-cloud">
          {words.map((w, i) => {
            const size = 14 + (w.count / max) * 60;
            const isSelected = selected.includes(w.word);

            return (
              <span
                key={i}
                className="wc-word"
                style={{
                  fontSize: `${size}px`,
                  padding: "4px 8px",
                  borderRadius: "6px",
                  cursor: "pointer",
                  margin: "5px 10px",
                  display: "inline-block",
                  background: isSelected ? "rgba(26, 115, 232, 0.20)" : "transparent",
                  border: isSelected ? "1px solid #1a73e8" : "none",
                }}
                onClick={() => toggleSelect(w.word)}
              >
                {w.word}
              </span>
            );
          })}
        </div>

        {selected.length > 0 && (
          <button className="wc-search-btn" onClick={runMultiSearch}>
            🔍 Rechercher ces {selected.length} mots
          </button>
        )}
      </div>
    </div>
  );
}
