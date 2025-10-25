import streamlit as st
import os
import sqlite3
from collections import Counter
import re, glob, docx
from pdfminer.high_level import extract_text

DB_PATH = "search_engine.db"
UPLOAD_DIR = "documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="⚙️ Admin Panel", layout="wide")
st.title("⚙️ Panneau d'administration — Gestion du moteur de recherche")

# ---- Sidebar menu
st.sidebar.header("📁 Actions disponibles")
action = st.sidebar.radio(
    "Choisissez une action :", 
    ["📤 Ajouter un document", "📊 Voir les statistiques", "🧹 Ré-indexer"]
)

# ---- Function: normalize words
def normalisation(text):
    text = text.lower()
    tokens = re.findall(r"\b[a-zA-ZÀ-ÿ'-]+\b", text)
    return tokens

# ---- Function: read DOCX and PDF
def lire_docx(filepath):
    try:
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs])
    except:
        return ""

def lire_pdf(filepath):
    try:
        return extract_text(filepath)
    except:
        return ""

# =======================================================================================
# 📤 1. Upload new documents
# =======================================================================================
if action == "📤 Ajouter un document":
    st.subheader("📄 Importer un nouveau document")
    uploaded_file = st.file_uploader("Choisissez un fichier (TXT, DOCX, PDF)", type=["txt", "docx", "pdf"])

    if uploaded_file:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ Fichier ajouté : {uploaded_file.name}")
        st.info("Il sera indexé automatiquement au prochain redémarrage ou via 'Ré-indexer'.")

# =======================================================================================
# 📊 2. View keyword statistics
# =======================================================================================
elif action == "📊 Voir les statistiques":
    st.subheader("📈 Statistiques des mots-clés")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT word, SUM(count) FROM word_frequencies GROUP BY word ORDER BY SUM(count) DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()

    if rows:
        st.bar_chart({word: count for word, count in rows})
        st.dataframe(rows, use_container_width=True)
    else:
        st.warning("Aucune donnée disponible. Vous devez peut-être ré-indexer les documents.")

# =======================================================================================
# 🧹 3. Reindex documents
# =======================================================================================
elif action == "🧹 Ré-indexer":
    st.subheader("🔄 Ré-indexation complète")

    files = os.listdir(UPLOAD_DIR)
    if not files:
        st.warning("Aucun fichier trouvé dans le dossier 'documents'.")
    else:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM word_frequencies")

        for file in files:
            path = os.path.join(UPLOAD_DIR, file)
            ext = os.path.splitext(file)[1].lower()
            content = ""

            if ext == ".txt":
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            elif ext == ".docx":
                content = lire_docx(path)
            elif ext == ".pdf":
                content = lire_pdf(path)

            cursor.execute("INSERT INTO documents (filename, filetype, content) VALUES (?, ?, ?)", (file, ext, content))
            doc_id = cursor.lastrowid

            words = Counter(normalisation(content))
            for w, c in words.items():
                cursor.execute("INSERT INTO word_frequencies (document_id, word, count) VALUES (?, ?, ?)", (doc_id, w, c))

        conn.commit()
        conn.close()
        st.success("✅ Ré-indexation terminée avec succès.")
