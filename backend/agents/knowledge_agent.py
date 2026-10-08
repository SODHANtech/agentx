import os
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from backend.llm import llm

embedding = FastEmbedEmbeddings()

db = Chroma(
    persist_directory="backend/vector_db",
    embedding_function=embedding
)


class KnowledgeAgent:

    def ask(self, question: str, history: str = ""):

        docs = db.similarity_search(question, k=3)

        context = "\n\n".join(
            doc.page_content
            for doc in docs
        )

        sources = []
        seen = set()
        for doc in docs:
            src = doc.metadata.get("source", "")
            doc_name = os.path.basename(src) if src else "college_handbook.pdf"
            
            # Normalize page metadata if present
            page_num = doc.metadata.get("page_label")
            if page_num is None and "page" in doc.metadata:
                page_num = doc.metadata["page"] + 1
            elif page_num is not None:
                try:
                    page_num = int(page_num)
                except Exception:
                    pass

            key = (doc_name, page_num)
            if key not in seen:
                seen.add(key)
                src_item = {"document": doc_name}
                if page_num is not None:
                    src_item["page"] = page_num
                sources.append(src_item)

        prompt = f"""
You are Smart Campus AI.

You are having an ongoing conversation with the student.

Previous Conversation:
{history}

Use ONLY the information provided below to answer.

If the answer is not present in the context, reply:

"I couldn't find that information in the college handbook."

Context:
{context}

Current Question:
{question}
"""

        response = llm.invoke(prompt)

        return {
            "answer": response.content,
            "sources": sources
        }