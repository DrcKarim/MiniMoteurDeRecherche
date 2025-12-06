import { useEffect, useState } from "react";
import { getWordCloud } from "../services/api";
import "./WordCloudModal.css";

type CloudWord = {
  word: string;
  count: number;  // backend returns "count"
};

export default function WordCloudModal() {
  const [isOpen, setOpen] = useState(false);
  const [filename, setFilename] = useState("");
  const [words, setWords] = useState<CloudWord[]>([]);

  useEffect(() => {
    const listener = async (e: any) => {
      const file = e.detail?.filename;
      if (!file) return;

      setFilename(file);
      setOpen(true);

      try {
        const data = await getWordCloud(file);
        setWords(data.top_words || []); // [{word, count}]
      } catch (err) {
        console.error("Word cloud error:", err);
      }
    };

    window.addEventListener("openWordCloud", listener);
    return () => window.removeEventListener("openWordCloud", listener);
  }, []);

  if (!isOpen) return null;

  /** CLICK → SearchBar should receive it */
  const handleWordClick = (word: string) => {
    window.dispatchEvent(
      new CustomEvent("searchFromCloud", { detail: { word } })
    );
    setOpen(false);
  };

  /** 🎨 SCALE SIZES: transform count → font-size */
  const max = Math.max(...words.map((w) => w.count), 1);

  const randomColor = () =>
    `hsl(${Math.floor(Math.random() * 360)}, 70%, 45%)`;

  const randomRotation = () => {
    const angles = [-20, -10, 0, 10, 20];
    return angles[Math.floor(Math.random() * angles.length)];
  };

  return (
    <div className="wc-overlay" onClick={() => setOpen(false)}>
      <div className="wc-box" onClick={(e) => e.stopPropagation()}>
        <button className="wc-close-btn" onClick={() => setOpen(false)}>
          ✕
        </button>

      {/*  <h2 className="wc-title">Word Cloud — {filename}</h2> */}

        <div className="wc-cloud">
          {words.map((w, i) => {
            const size = 14 + (w.count / max) * 60; // dynamic scale 14px → 74px

            return (
              <span
                key={i}
                className="wc-word"
                style={{
                  fontSize: `${size}px`,
                  color: randomColor(),
                  transform: `rotate(${randomRotation()}deg)`,
                  margin: "5px 10px",
                  cursor: "pointer",
                  display: "inline-block",
                }}
                onClick={() => handleWordClick(w.word)}
              >
                {w.word}
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}
