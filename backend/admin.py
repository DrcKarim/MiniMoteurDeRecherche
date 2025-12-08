import streamlit as st
import os
import sqlite3
from collections import Counter
import re, glob, docx
from pdfminer.high_level import extract_text

import spacy
# Load French model once
nlp = spacy.load("fr_core_news_sm")

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

# Load stopwords ONCE
STOPWORDS = set()
if os.path.exists(STOPWORDS_FILE):
    with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
        STOPWORDS = {w.strip().lower() for w in f.read().splitlines()}
else:
    STOPWORDS = {"le","la","les","un","une","et","de","du","des","à","au","aux"}

def normalisation(text: str):
    """
    Full normalization for French:
    - lowercase
    - extract alphabetic tokens
    - lemmatization (infinitive form)
    - remove stopwords & short words
    """
    text = text.lower()

    # Extract only alphabetic words
    tokens = re.findall(r"[a-zA-ZÀ-ÿ'-]+", text)

    if not tokens:
        return []

    # Process with spaCy for lemmatization
    doc = nlp(" ".join(tokens))

    normalized = []
    for token in doc:
        lemma = token.lemma_.lower().strip()

        if (
            lemma
            and lemma.isalpha()
            and len(lemma) > 2
            and lemma not in STOPWORDS
        ):
            normalized.append(lemma)

    return normalized

# -------------------------- FILE READERS --------------------------
def lire_pdf(filepath):
    try:
        return extract_text(filepath)
    except Exception:
        return ""


def lire_docx(filepath):
    try:
        doc = docx.Document(filepath)
        return "\n".join([p.text for p in doc.paragraphs])
    except Exception:
        return ""

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

def lire_html(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        return text
    except:
        return ""



# =======================================================================================
#  1. Upload new documents
# =======================================================================================
if action == "📤 Ajouter un document":
    st.subheader("📄 Importer des documents (plusieurs fichiers à la fois)")

    uploaded_files = st.file_uploader(
        "Choisissez des fichiers (TXT, DOCX, PDF, HTML)",
        type=["txt", "docx", "pdf", "html"],
        accept_multiple_files=True
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)

            # Save each file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"✅ Fichier ajouté : {uploaded_file.name}")

        st.info("Tous les fichiers seront indexés automatiquement au prochain redémarrage ou via 'Ré-indexer'.")


# =======================================================================================
#  1B. Upload with format filtering (CASE À COCHER)
# =======================================================================================
if action == "📤 Ajouter un document":    
    st.subheader("📁 Importer un document (avec choix des formats)")

    # Cases à cocher
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        allow_txt = st.checkbox("TXT", value=True)
    with col2:
        allow_pdf = st.checkbox("PDF", value=True)
    with col3:
        allow_docx = st.checkbox("DOCX", value=True)
    with col4:
        allow_html = st.checkbox("HTML", value=True)

    allowed_ext = []
    if allow_txt: allowed_ext.append("txt")
    if allow_pdf: allowed_ext.append("pdf")
    if allow_docx: allowed_ext.append("docx")
    if allow_html: allowed_ext.append("html")

    uploaded_filtered = st.file_uploader(
        "Sélectionnez un fichier :",
        type=allowed_ext,   # ❗ Restriction dynamique
        accept_multiple_files=False  # un seul document
    )

    if uploaded_filtered:
        file_ext = uploaded_filtered.name.split(".")[-1].lower()

        if file_ext not in allowed_ext:
            st.error(f"❌ Le format .{file_ext} n'est pas autorisé.")
        else:
            file_path = os.path.join(UPLOAD_DIR, uploaded_filtered.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_filtered.getbuffer())

            st.success(f"✅ Document importé : {uploaded_filtered.name}")
            st.info("Il sera indexé au prochain redémarrage ou via 'Ré-indexer'.")


# =======================================================================================
#  2. View keyword statistics
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

    overview_data = {
        "📄 Nombre total de documents": [total_docs],
        "🔤 Total de mots indexés": [total_words],
        "🧩 Mots uniques": [unique_words],
    }

    import pandas as pd
    overview_df = pd.DataFrame(overview_data)
    # Convert to HTML table to hide index completely
    st.markdown(
    overview_df.to_html(index=False, justify="center"),
    unsafe_allow_html=True
    )

    st.markdown("---")

    # ---- 2️⃣ Top documents by word count
# ---- 2️⃣ Top documents by word count (WITH DELETE BUTTON)
    cursor.execute("""
        SELECT d.id, d.filename, COUNT(w.word) AS total_mots, COUNT(DISTINCT w.word) AS mots_uniques
        FROM documents d
        LEFT JOIN word_frequencies w ON d.id = w.document_id
        GROUP BY d.id
        ORDER BY total_mots DESC
    """)
    doc_stats = cursor.fetchall()

    st.markdown("### 🏆 Top documents par nombre de mots")

    if doc_stats:

        import pandas as pd

        df = pd.DataFrame([
            {
                "ID": doc_id,
                "Document": filename,
                "Mots totaux": total_mots,
                "Mots uniques": mots_uniques
            }
            for doc_id, filename, total_mots, mots_uniques in doc_stats
        ])

        for index, row in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 1])

            with col1:
                st.write(row["Document"])

            with col2:
                st.write(f"📝 Total : {row['Mots totaux']}")

            with col3:
                st.write(f"🔤 Uniques : {row['Mots uniques']}")

            with col5:
                # BOUTON SUPPRIMER
                    if st.button("🗑️", key=f"delete_{row['ID']}"):
                        doc_id = row["ID"]

                        # Delete DB entries
                        cursor.execute("DELETE FROM word_frequencies WHERE document_id = ?", (doc_id,))
                        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                        conn.commit()

                        # Delete file
                        file_path = os.path.join(UPLOAD_DIR, row["Document"])
                        if os.path.exists(file_path):
                            os.remove(file_path)

                        st.success(f"Document supprimé : {row['Document']}")
                        st.rerun()        # ✅ correct refresh

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

    # ---- 1️⃣ Load stopwords
    if os.path.exists(STOPWORDS_FILE):
        with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
            stopwords = set(word.strip().lower() for word in f.read().splitlines() if word.strip())
    else:
        stopwords = set()
        st.warning("⚠️ Aucun fichier de stopwords trouvé. Tous les mots seront indexés.")


    # ---- 2️⃣ List all files
    files = os.listdir(UPLOAD_DIR)
    if not files:
        st.warning("Aucun fichier trouvé dans le dossier 'documents'.")
        st.stop()

    total_files = len(files)

    # ---- Progress UI
    progress_bar = st.progress(0)
    spinner = st.spinner("📚 Indexation en cours, veuillez patienter…")
    status_text = st.empty()

    with spinner:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # ---- Reset database
        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM word_frequencies")

        # ---- 3️⃣ Iterate through files
        for i, file in enumerate(files, start=1):
            path = os.path.join(UPLOAD_DIR, file)
            ext = os.path.splitext(file)[1].lower()
            content = ""

            # ---- Read file content depending on type
            if ext == ".txt":
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

            elif ext == ".docx":
                content = lire_docx(path)

            elif ext == ".pdf":
                content = lire_pdf(path)

            elif ext in [".html", ".htm"]:
                content = lire_html(path)

            else:
                status_text.write(f"⚠️ Format non supporté : {file}")
                continue

            # ---- Insert document into DB
            cursor.execute(
                "INSERT INTO documents (filename, filetype, content) VALUES (?, ?, ?)",
                (file, ext, content)
            )
            doc_id = cursor.lastrowid

            # ---- Normalize & index words
            words = Counter(normalisation(content))
            inserted = 0

            for w, c in words.items():
                w = w.lower().strip()
                if w and w not in stopwords and len(w) > 2:
                    cursor.execute("""
                        INSERT INTO word_frequencies (document_id, word, count)
                        VALUES (?, ?, ?)
                        ON CONFLICT(document_id, word)
                        DO UPDATE SET count = excluded.count;
                    """, (doc_id, w, c))
                    inserted += 1

            # ---- Update progress UI
            progress = i / total_files
            progress_bar.progress(progress)

            if inserted == 0:
                status_text.write(f"ℹ️ Aucun mot utile trouvé dans : **{file}**")
            else:
                status_text.write(f"📄 Indexé : **{file}** ({inserted} mots utiles)")

        conn.commit()
        conn.close()

    st.success("✅ Ré-indexation terminée avec succès !")


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
