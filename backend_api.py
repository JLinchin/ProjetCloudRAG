"""Backend FastAPI pour l'assistant documentaire RAG (version minimale)."""

import os
import chromadb
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from sentence_transformers import SentenceTransformer

import storage_minio

load_dotenv("conf.env")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_data")
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
TOP_K = 4

app = FastAPI(title="RAG Barack Obama - Backend")

_embedding_model = None
_chroma_client = None
_collection = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model


def get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = _chroma_client.get_or_create_collection("rag_passages")
    return _collection


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Découpe un texte en passages de taille chunk_size avec chevauchement overlap."""
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def build_prompt(question: str, context: str) -> str:
    return (
        "Tu es un assistant documentaire.\n"
        "Réponds uniquement à partir du contexte fourni.\n"
        "Si l'information n'est pas présente dans le contexte, réponds :\n"
        '"Je ne trouve pas cette information dans le document fourni."\n\n'
        f"Contexte :\n{context}\n\n"
        f"Question :\n{question}\n\n"
        "Réponse :"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    storage_minio.upload_bytes(file.filename, data)
    return {"filename": file.filename, "size": len(data)}


@app.post("/index")
def index(filename: str):
    data = storage_minio.download_bytes(filename)
    text = data.decode("utf-8", errors="ignore")
    chunks = chunk_text(text)

    model = get_embedding_model()
    embeddings = model.encode(chunks).tolist()

    collection = get_collection()
    ids = [f"{filename}-{i}" for i in range(len(chunks))]
    metadatas = [{"filename": filename, "passage_num": i} for i in range(len(chunks))]

    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

    return {"filename": filename, "nb_passages": len(chunks)}


@app.post("/ask")
def ask(question: str, top_k: int = TOP_K):
    model = get_embedding_model()
    question_embedding = model.encode([question]).tolist()

    collection = get_collection()
    results = collection.query(query_embeddings=question_embedding, n_results=top_k)

    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []

    context = "\n\n".join(documents)
    prompt = build_prompt(question, context)

    response = requests.post(
        OLLAMA_URL,
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    response.raise_for_status()
    answer = response.json().get("response", "").strip()

    sources = [
        {
            "filename": meta.get("filename"),
            "passage_num": meta.get("passage_num"),
            "extrait": doc[:200],
            "score": dist,
        }
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]

    return {"answer": answer, "sources": sources}
