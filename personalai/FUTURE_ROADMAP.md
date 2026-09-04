# 🔮 Personal AI System - Future Architecture & Feature Roadmap

This document serves as the master blueprint for Phase 2 development. It preserves all ideas, feature specifications, and architectural upgrades discussed for implementation.

---

## 🗺️ Key Upgrade Areas

### 1. 🖥️ Desktop GUI & Multi-User Permission Controls
- **Dual Toggle Switches**: GUI interface with toggles for:
  - **Native Local AI Mode**: Turn AI on/off for general desktop access.
  - **Cross-Platform Phone Bridge**: Requires explicit user permission before enabling P2P Android listener connection (prevents unauthorized phone access when family members use the laptop).
- **Multi-User Isolation**: Guest/Brother mode vs. Owner (Boss) mode.

---

### 2. 🎭 5 Specialized Persona Modes
- **Mode 1: The Mentor / Teacher 🎓**
  - Designed for exam preparation, deep focus, structured study sessions, and concept explanations.
- **Mode 2: Tony (Senior Software Engineer) 💻**
  - Acts as a veteran tech lead / senior architect. Critiques code against industry standards, predicts failure points, reviews architecture, and catches rookie mistakes.
- **Mode 3: (Reserved for Custom Personality)**
- **Mode 4: (Reserved for Custom Personality)**
- **Mode 5: (Reserved for Custom Personality)**

---

### 3. 🤖 Autonomous CLI & System Execution (Open-Interpreter / Aider)
- Integrated terminal execution layer so the AI can execute PowerShell / Bash commands, fix code, and manage git repositories autonomously using tools like `open-interpreter` and `aider-chat`.

---

### 4. 🔀 Dynamic Multi-Model Router Pipeline
Automatic task-based model switching depending on complexity, domain, and priority:
- **`qwen2.5-coder:7b / 14b`**: Selected for heavy coding, refactoring, and code analysis.
- **`deepseek-r1:8b`**: Selected for complex mathematical reasoning, logic puzzles, and architectural planning.
- **`llama3.1:8b`**: Selected for general conversation, summary, and fast queries.
- **Custom Model Router**: Evaluates prompt intent and routes to the optimal local model automatically.

---

### 5. 🧠 Stack Modernization (LangGraph & Elasticsearch)
- **LangGraph Integration**: Stateful multi-agent graph workflows for complex multi-step reasoning.
- **Hybrid Search Engine**: Combining ChromaDB vector search with Elasticsearch / BM25 keyword search for hybrid RAG.

---

### 6. ⏰ Context-Aware Focus & Break Reminder Guard
- Integration of a smart 30-minute break timer system.
- **Context-Aware Rules**: Detects active mode (e.g. Exam/Study Mode, Coding Session) so break popups never interrupt exams or critical focus blocks.

---

## 📌 Status
**Saved & Stored**: Ready for co-development when you return from college!
