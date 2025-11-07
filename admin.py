import streamlit as st
import os
import sqlite3
from collections import Counter
import re, glob, docx
from pdfminer.high_level import extract_text

DB_PATH = "search_engine.db"
UPLOAD_DIR = "documents"
STOPWORDS_FILE = "stopwords.txt"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(page_title="🔍 DocuFind — Admin Panel", layout="wide")

# ---- Header with logo and app name ----
st.markdown("""
    <div style='text-align:center; margin-bottom:20px;'>
        <h1 style='font-size:42px;'>🔍 <span style="color:#1a73e8;">DocuFind</span></h1>
        <h3 style='color:gray;'>Panneau d'administration – Gestion du moteur de recherche</h3>
        <hr style='border:1px solid #ddd;'/>
    </div>
""", unsafe_allow_html=True)

# ---- Sidebar menu
st.sidebar.header("📁 Actions disponibles")
action = st.sidebar.radio(
    "Choisissez une action :",
    ["📤 Ajouter un document", "📊 Voir les statistiques", "🧹 Ré-indexer", "✏️ Gérer les stopwords"]
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
    st.subheader("📈 Statistiques globales du moteur DocuFind")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ---- 1️⃣ Global overview
    total_docs = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    total_words = cursor.execute("SELECT COUNT(*) FROM word_frequencies").fetchone()[0]
    unique_words = cursor.execute("SELECT COUNT(DISTINCT word) FROM word_frequencies").fetchone()[0]

    st.markdown("### 🌍 Vue d'ensemble")
    st.metric("📄 Nombre total de documents", total_docs)
    st.metric("🔤 Total de mots indexés", total_words)
    st.metric("🧩 Mots uniques", unique_words)

    st.markdown("---")

    # ---- 2️⃣ Top documents by word count
    cursor.execute("""
        SELECT d.filename, COUNT(w.word) AS total_mots, COUNT(DISTINCT w.word) AS mots_uniques
        FROM documents d
        LEFT JOIN word_frequencies w ON d.id = w.document_id
        GROUP BY d.id
        ORDER BY total_mots DESC
    """)
    doc_stats = cursor.fetchall()

    if doc_stats:
        st.markdown("### 🏆 Top documents par nombre de mots")
        st.dataframe(
            [{"Document": d, "Mots totaux": t, "Mots uniques": u} for d, t, u in doc_stats],
            use_container_width=True
        )
    else:
        st.warning("⚠️ Aucun document indexé pour le moment.")

    st.markdown("---")

    # ---- 3️⃣ Per-document breakdown
    if total_docs > 0:
        st.markdown("### 🔍 Analyse d’un document spécifique")
        cursor.execute("SELECT filename, id FROM documents ORDER BY filename")
        docs = cursor.fetchall()
        doc_names = [d[0] for d in docs]
        selected_doc = st.selectbox("Choisissez un document :", doc_names)

        if selected_doc:
            doc_id = [d[1] for d in docs if d[0] == selected_doc][0]
            cursor.execute("""
                SELECT word, SUM(count) as freq
                FROM word_frequencies
                WHERE document_id = ?
                GROUP BY word
                ORDER BY freq DESC
                LIMIT 10
            """, (doc_id,))
            top_words = cursor.fetchall()

            if top_words:
                st.markdown(f"#### 🔠 Top 10 mots du document : **{selected_doc}**")
                st.bar_chart({w: f for w, f in top_words})
                st.dataframe(top_words, use_container_width=True)
            else:
                st.info("Aucun mot indexé pour ce document (filtré par les stopwords).")

    conn.close()

# =======================================================================================
# 🧹 3. Reindex documents
# =======================================================================================
elif action == "🧹 Ré-indexer":
    st.subheader("🔄 Ré-indexation complète")

    # ---- Load stopwords
    if os.path.exists(STOPWORDS_FILE):
        with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
            stopwords = set(word.strip().lower() for word in f.read().splitlines() if word.strip())
    else:
        stopwords = set()
        st.warning("⚠️ Aucun fichier de stopwords trouvé. Tous les mots seront indexés.")

    files = os.listdir(UPLOAD_DIR)
    if not files:
        st.warning("Aucun fichier trouvé dans le dossier 'documents'.")
    else:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Clear old data
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

            # Insert new document
            cursor.execute("INSERT INTO documents (filename, filetype, content) VALUES (?, ?, ?)", (file, ext, content))
            doc_id = cursor.lastrowid

            # Tokenize and filter stopwords
            words = Counter(normalisation(content))
            added_words = 0
            for w, c in words.items():
                w = w.lower().strip()  # normalize the token
                if w and w not in stopwords and len(w) > 2:
                    cursor.execute(
                        "INSERT INTO word_frequencies (document_id, word, count) VALUES (?, ?, ?)",
                        (doc_id, w, c)
                    )
                    added_words += 1

            if added_words == 0:
                st.info(f"ℹ️ Aucun mot utile indexé pour {file} (filtré par les stopwords).")

        conn.commit()
        conn.close()
        st.success("✅ Ré-indexation terminée avec succès (stopwords exclus et mots normalisés).")


# =======================================================================================
# ✏️ 4. Manage Stopwords
# =======================================================================================
elif action == "✏️ Gérer les stopwords":
    st.subheader("📝 Gestion des Stopwords")

    if not os.path.exists(STOPWORDS_FILE):
        with open(STOPWORDS_FILE, "w", encoding="utf-8") as f:
            f.write("le\nla\nles\nun\nune\net\nde\ndu\ndes\nà\nau\naux\n")

    with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
        stopwords = f.read().splitlines()

    st.markdown("### 🔍 Liste actuelle des stopwords")
    st.write(", ".join(stopwords))

    st.markdown("---")

    new_word = st.text_input("➕ Ajouter un mot à la liste")
    if st.button("Ajouter"):
        if new_word and new_word not in stopwords:
            stopwords.append(new_word)
            with open(STOPWORDS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(stopwords))
            st.success(f"✅ '{new_word}' ajouté à la liste.")
        else:
            st.warning("⚠️ Mot déjà présent ou vide.")

    st.markdown("---")

    remove_word = st.selectbox("🗑️ Supprimer un mot", [""] + stopwords)
    if st.button("Supprimer"):
        if remove_word and remove_word in stopwords:
            stopwords.remove(remove_word)
            with open(STOPWORDS_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(stopwords))
            st.success(f"🗑️ '{remove_word}' supprimé de la liste.")
        else:
            st.warning("⚠️ Sélectionnez un mot valide.")

    st.markdown("---")
    if st.button("🧾 Afficher le contenu brut du fichier"):
        st.code("\n".join(stopwords))
