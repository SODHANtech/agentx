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
            "answer": response.content
        }