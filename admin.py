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
