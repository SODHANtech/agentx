from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

embedding = FastEmbedEmbeddings()

db = Chroma(
    persist_directory="backend/vector_db",
    embedding_function=embedding
)

collection = db._collection

print("Total Documents:", collection.count())

query = "attendance"

docs = db.similarity_search(query, k=3)

print("\nRetrieved:", len(docs), "documents\n")

for i, doc in enumerate(docs, 1):
    print(f"\n===== Result {i} =====")
    print(doc.page_content)
    print("\nMetadata:", doc.metadata)
    print("-" * 80)