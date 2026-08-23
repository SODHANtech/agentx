from langchain_groq import ChatGroq
from backend.config import settings

llm = ChatGroq(
    model=settings.LLM_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0
)