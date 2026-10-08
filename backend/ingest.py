from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

embedding = FastEmbedEmbeddings()

DB = Chroma(
    persist_directory="backend/vector_db",
    embedding_function=embedding
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=700,
    chunk_overlap=100
)

DATA_DIR = Path("backend/data")

documents = []

# Scan all PDFs recursively in backend/data (including REGULATIONS and yearlyCalender)
all_pdfs = [p for p in DATA_DIR.rglob("*.pdf") if "uploads" not in p.parts]

for pdf in all_pdfs:
    print(f"Loading {pdf.relative_to(DATA_DIR)}")
    try:
        loader = PyPDFLoader(str(pdf))
        docs = loader.load()
        # Clean metadata source to be relative/clean filename
        for d in docs:
            d.metadata["source"] = pdf.name
        chunks = splitter.split_documents(docs)
        documents.extend(chunks)
    except Exception as e:
        print(f"Warning: Failed to load {pdf.name}: {e}")

print(f"Total Chunks: {len(documents)}")

# Clear previous vector collection to avoid stale duplicates
try:
    DB.reset_collection()
except Exception:
    pass

# Batch insertion into Chroma vector store
BATCH_SIZE = 100
for i in range(0, len(documents), BATCH_SIZE):
    batch = documents[i:i + BATCH_SIZE]
    DB.add_documents(batch)
    print(f"Indexed batch {i//BATCH_SIZE + 1}/{(len(documents) + BATCH_SIZE - 1)//BATCH_SIZE}")

print("Vector DB Created Successfully with all Regulations & Calendars!")