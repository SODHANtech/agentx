import json
from langchain_chroma import Chroma
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from backend.llm import llm

embedding = FastEmbedEmbeddings()
db = Chroma(
    persist_directory="backend/vector_db",
    embedding_function=embedding
)

class QuizAgent:
    
    def generate_quiz(self, topic: str) -> dict:
        """
        Queries ChromaDB vector database for RAG context and uses Groq Llama 
        to generate an academic explanation and a 3-question multiple choice quiz.
        """
        try:
            # Query vector database
            docs = db.similarity_search(topic, k=2)
            context = "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"ChromaDB search failed in QuizAgent: {e}")
            context = "No additional context found in campus manuals."

        prompt = f"""
You are the Academic Assistant and Quiz Generator for CampusOS.

Provide a brief, clear explanation of the topic based on the context below.
Then, generate a practice quiz containing exactly 3 multiple choice questions based on the topic.

Context:
{context}

Topic:
{topic}

Return ONLY a valid JSON object matching this structure (do NOT write any codeblocks, markdown headers, or other conversational text):
{{
    "explanation": "Brief explanation based on the context...",
    "quiz": [
        {{
            "question": "Question text...",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer": "The exact option string that is correct"
        }}
    ]
}}
"""
        try:
            response = llm.invoke(prompt)
            text = response.content.strip()

            # Strip potential JSON block enclosures
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

            data = json.loads(text)
            return data
        except Exception as e:
            print(f"Error in QuizAgent LLM execution: {e}")
            return {
                "explanation": f"Failed to generate structured explanation for: {topic}",
                "quiz": []
            }
