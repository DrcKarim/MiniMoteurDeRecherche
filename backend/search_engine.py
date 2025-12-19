import os
import re
import glob
import sqlite3
from collections import Counter, defaultdict
from pdfminer.high_level import extract_text
import docx

import spacy
# Load French model once
nlp = spacy.load("fr_core_news_sm")

DB_PATH = "search_engine.db"
DOCUMENTS_DIR = "documents"
STOPWORDS_FILE = "stopwords.txt"


# -------------------------- STOPWORDS LOADING --------------------------
def load_stopwords():
    stopwords = set()
    if os.path.exists(STOPWORDS_FILE):
        with open(STOPWORDS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    stopwords.add(w)
    return stopwords


STOPWORDS = load_stopwords()


# -------------------------- NORMALISATION --------------------------
"""
def normalisation(text: str):
     
    Same logic as your Streamlit version: lowercase, keep alphabetic tokens,
    remove stopwords.
     
    text = text.lower()
    tokens = re.findall(r"[a-zA-ZÀ-ÿ'-]+", text)
    tokens = [t for t in tokens if t not in STOPWORDS]
    return tokens
"""

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

    # Join tokens back so spaCy can process them
    doc = nlp(" ".join(tokens))

    normalized = []
    for token in doc:
        lemma = token.lemma_.lower().strip()

        if (
            lemma
            and lemma not in STOPWORDS
            and len(lemma) > 2
            and lemma.isalpha()
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


# -------------------------- ACQUISITION --------------------------
def acquisition(path=DOCUMENTS_DIR):
    corpus = {}
    for filepath in glob.glob(os.path.join(path, "*")):
        filename = os.path.basename(filepath)

        try:
            if filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    corpus[filename] = f.read()

            elif filename.endswith(".pdf"):
                corpus[filename] = lire_pdf(filepath)

            elif filename.endswith(".docx"):
                corpus[filename] = lire_docx(filepath)

        except Exception as e:
            print(f" Error reading {filename}: {e}")

    return corpus


# -------------------------- EXTRACTION --------------------------
def extraction(corpus):
    freqs = {}
    for filename, content in corpus.items():
        tokens = normalisation(content)
        freqs[filename] = Counter(tokens)
    return freqs


# -------------------------- INDEXATION --------------------------
def build_index(freqs):
    index = defaultdict(set)
    for filename, counter in freqs.items():
        for word in counter.keys():
            index[word].add(filename)
    return index


# -------------------------- RECHERCHE --------------------------
def recherche(query: str, index):
    """
    Recherche en français :
    - "mot1 mot2"        => OU par défaut
    - "mot1 et mot2"    => ET
    - "mot1 ou mot2"    => OU
    """
    q = query.lower().strip()

    # ----- Détection opérateurs -----
    if " et " in q:
        mot1, mot2 = q.split(" et ", 1)
        set1 = index.get(mot1, set())
        set2 = index.get(mot2, set())
        return set1 & set2   # ET

    if " ou " in q:
        mot1, mot2 = q.split(" ou ", 1)
        set1 = index.get(mot1, set())
        set2 = index.get(mot2, set())
        return set1 | set2   # OU

    # ----- OU par défaut pour plusieurs mots -----
    mots = q.split()

    if len(mots) == 1:
        return index.get(mots[0], set())

    # Sinon : OU pour tous les mots
    result = set()
    for m in mots:
        result |= index.get(m, set())

    return result


# -------------------------- LOADING ON STARTUP --------------------------
print("📚 Loading documents...")
CORPUS = acquisition()
FREQS = extraction(CORPUS)
INDEX = build_index(FREQS)
print("✔️ Search engine ready")
