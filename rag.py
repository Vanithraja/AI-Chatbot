
import uuid
import chromadb

from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


# Load Embedding Model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chroma_db")

chroma_client = chromadb.PersistentClient(path=DB_PATH)

collection = chroma_client.get_or_create_collection(
    name="document_collection"
)


# Step 1: Extract Text from PDF
def extract_text_from_pdf(pdf_path):

    reader = PdfReader(pdf_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    if not text.strip():
        raise ValueError(
            "No readable text found in PDF"
        )

    return text


# Step 2: Split Text into Chunks
def split_text_into_chunks(
    text,
    chunk_size=500,
    overlap=50
):

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size")

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# Step 3: Store Chunks in ChromaDB
def store_chunks_in_database(chunks, document_id):

    if not chunks:
        raise ValueError("No text chunks found")

    embeddings = embedding_model.encode(chunks)

    ids = [
        f"{document_id}_{i}"
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=[
            {"document_id": document_id}
            for _ in chunks
        ]
    )

    print("Chunks stored successfully!")


# Step 4: Search Relevant Information
def search_relevant_chunks(question, top_k=3):

    if collection.count() == 0:
        return []

    question_embedding = embedding_model.encode(
        [question]
    )

    results = collection.query(
        query_embeddings=question_embedding.tolist(),
        n_results=min(top_k, collection.count())
    )

    documents = results.get("documents", [[]])

    if documents and documents[0]:
        return documents[0]

    return []


# Step 5: Process PDF
def process_pdf(pdf_path):

    document_id = str(uuid.uuid4())

    text = extract_text_from_pdf(pdf_path)

    chunks = split_text_into_chunks(text)

    store_chunks_in_database(
        chunks,
        document_id
    )

    return document_id
