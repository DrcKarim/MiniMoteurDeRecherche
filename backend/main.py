from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query
from search_engine import CORPUS, FREQS, INDEX, recherche

from fastapi import HTTPException
import os
from search_engine import CORPUS, FREQS, INDEX, recherche

from fastapi.responses import FileResponse

import os
from fastapi import Query
from fastapi.responses import JSONResponse


import sqlite3
from fastapi import HTTPException

from fastapi import FastAPI
import sqlite3
import difflib

import Levenshtein

import re
import unicodedata

app = FastAPI(
    title="DocuFind API",
    description="Backend API for the document search engine",
    version="1.0.0",
)

# --- CORS (to allow React frontend later) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # later you can restrict to http://localhost:5173 etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DOCS_DIR = "Documents"  # folder where files are stored

def clean_text(text: str) -> str:
    """
    Removes URLs, special characters, excessive spaces,
    normalizes unicode accents, and converts to lowercase.
    """
    if not text:
        return ""

    import re
    import unicodedata

    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", "", text)

    # Normalize unicode accents (é → e, ç → c)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

    # Keep only letters, numbers, and basic punctuation
    text = re.sub(r"[^a-zA-Z0-9 ,.;!?'-]", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Convert everything to lowercase
    return text.lower()



def extract_snippet(filepath: str, max_chars: int = 200):
    """
    Reads first characters of a document to use as a snippet.
    Supports TXT, DOCX, PDF.
    Returns a clean, normalized text with no links or special characters.
    """
    raw_text = ""

    # TXT
    if filepath.lower().endswith(".txt"):
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read(max_chars)

    # DOCX
    elif filepath.lower().endswith(".docx"):
        import docx
        doc = docx.Document(filepath)
        full_text = " ".join([p.text for p in doc.paragraphs])
        raw_text = full_text[:max_chars]

    # PDF
    elif filepath.lower().endswith(".pdf"):
        import PyPDF2
        try:
            pdf = PyPDF2.PdfReader(filepath)
            text = pdf.pages[0].extract_text() or ""
            raw_text = text[:max_chars]
        except:
            return "PDF preview not available"

    else:
        return "No preview available"

    # CLEAN + NORMALIZE → RETURN SNIPPET
    return clean_text(raw_text)

# --- Health check endpoint ---
@app.get("/ping")
def ping():
    return {"status": "ok", "message": "DocuFind API is running 🚀"}


@app.get("/search")
def search(query: str = Query(..., min_length=1)):
    """
    Return enriched search results:
    - filename
    - snippet
    - score (ranking indicator)
    - path
    """

    # Get list of filenames from the existing search
    filenames = recherche(query, INDEX)
    terms = query.lower().split()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    results = []

    for filename in filenames:

        # ---- 1️⃣ GET DOCUMENT ID
        cursor.execute("SELECT id, content FROM documents WHERE filename = ?", (filename,))
        row = cursor.fetchone()

        if not row:
            continue

        doc_id, content = row

        # ---- 2️⃣ CALCULATE SCORE BASED ON FREQUENCY OF SEARCH TERMS
        score = 0
        for term in terms:
            cursor.execute("""
                SELECT count FROM word_frequencies
                WHERE document_id = ? AND word = ?
            """, (doc_id, term.lower()))
            freq = cursor.fetchone()
            if freq:
                score += freq[0]

        # ---- 3️⃣ Extract snippet
        filepath = os.path.join(DOCS_DIR, filename)
        snippet = extract_snippet(filepath)

        # ---- 4️⃣ Package results
        results.append({
            "filename": filename,
            "snippet": snippet,
            "path": f"/raw/{filename}",
            "score": score
        })

    conn.close()

    # ---- 5️⃣ Sort results by score DESC
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return {
        "query": query,
        "count": len(results),
        "results": results
    }

# --- Root endpoint (optional welcome) ---
@app.get("/")
def root():
    return {
        "app": "DocuFind API",
        "endpoints": ["/ping", "/docs", "/redoc"],
        "message": "Backend ready to receive search, document, and cloud requests.",
    }

@app.get("/document/{filename}")
def get_document(filename: str):
    if filename not in CORPUS:
        raise HTTPException(status_code=404, detail="Document not found")

    content = CORPUS[filename]

    # A small snippet preview
    snippet = content[:500] + "..." if len(content) > 500 else content

    return {
        "filename": filename,
        "snippet": snippet,
        "full_content": content if filename.endswith(".txt") else None,
        "message": "Use frontend viewer for PDF/DOCX full display"
    }



DB_PATH = "search_engine.db"

@app.get("/cloud/{filename}")
def cloud(filename: str, limit: int = 40):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1️⃣ Get the document ID
    cursor.execute("SELECT id FROM documents WHERE filename = ?", (filename,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    doc_id = row[0]

    # 2️⃣ Fetch words already filtered by admin.py
    cursor.execute("""
        SELECT word, count 
        FROM word_frequencies
        WHERE document_id = ?
        ORDER BY count DESC
        LIMIT ?
    """, (doc_id, limit))

    top_words = cursor.fetchall()
    conn.close()

    # 3️⃣ Format response
    return {
        "filename": filename,
        "word_count": len(top_words),
        "top_words": [
            {"word": w, "count": c} for w, c in top_words
        ]
    }


@app.get("/raw/{filename}")
def raw_file(filename: str):
    file_path = os.path.join("documents", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)



@app.get("/suggest/{query}")
def suggest(query: str):
    conn = sqlite3.connect("search_engine.db")
    cursor = conn.cursor()

    cursor.execute("SELECT word FROM word_frequencies ORDER BY count DESC LIMIT 5000")
    vocab = [row[0] for row in cursor.fetchall()]

    best = sorted(
        vocab,
        key=lambda w: Levenshtein.distance(query.lower(), w.lower())
    )[:1]   # return only 1 suggestion

    return {"suggestions": best}