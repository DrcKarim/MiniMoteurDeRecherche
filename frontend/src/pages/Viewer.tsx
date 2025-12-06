import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getDocument, getRawFileUrl } from "../services/api";
import "./Viewer.css";

export default function Viewer() {
  const { filename } = useParams<{ filename: string }>();
  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDoc = async () => {
      if (!filename) return;
      const data = await getDocument(filename);
      setDoc(data);
      setLoading(false);
    };
    fetchDoc();
  }, [filename]);

  if (loading) {
    return <p className="viewer-loading">Loading document…</p>;
  }

  if (!doc) {
    return <p className="viewer-error">Document not found.</p>;
  }

  const rawUrl = getRawFileUrl(filename!);
  const isPDF = filename!.toLowerCase().endsWith(".pdf");

  return (
    <div className="viewer-container">

      <Link to="/" className="viewer-back">
        ← Retour à la recherche
      </Link>

      <h1 className="viewer-title">{filename}</h1>

      {/* Preview Box
      <div className="viewer-preview">
        <h2 className="viewer-preview-title">Preview</h2>
        <pre className="viewer-snippet">
          {doc.snippet || "No preview available…"}
        </pre>
      </div>  */}

      {/* Buttons */}
      <div className="viewer-buttons">
        <a href={rawUrl} target="_blank" rel="noreferrer" className="viewer-btn-primary">
          Ouvrir le document complet
        </a>

       {/*  <button className="viewer-btn-secondary">
          Word Cloud
        </button> */}
      </div>

      {/* PDF Viewer */}
      {isPDF && (
        <iframe src={rawUrl} className="viewer-pdf"></iframe>
      )}
    </div>
  );
}
