const API_URL = "http://127.0.0.1:8000";

export async function searchDocuments(query: string) {
  const res = await fetch(
    `${API_URL}/search?query=${encodeURIComponent(query)}`
  );
  return await res.json();
}

export async function getDocument(filename: string) {
  const res = await fetch(`${API_URL}/document/${filename}`);
  return await res.json();
}

export async function getWordCloud(filename: string) {
  const res = await fetch(`${API_URL}/cloud/${filename}`);
  return await res.json();
}

export function getRawFileUrl(filename: string) {
  return `${API_URL}/raw/${filename}`;
}

export async function getSuggestions(query: string) {
  const res = await fetch(`${API_URL}/suggest/${query}`);
  return await res.json();
}
