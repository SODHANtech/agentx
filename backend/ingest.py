from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

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

for pdf in DATA_DIR.glob("*.pdf"):

    print(f"Loading {pdf.name}")

    loader = PyPDFLoader(str(pdf))

    docs = loader.load()

    chunks = splitter.split_documents(docs)

    documents.extend(chunks)

print(f"Total Chunks: {len(documents)}")

DB.add_documents(documents)

print("Vector DB Created Successfully!")