# 🌾 SmartAgri - Agricultural Knowledge Retrieval System

[![Streamlit App](https://img.shields.io/badge/🚀-Live_Demo-2E7D32?style=for-the-badge&logo=streamlit)](https://smartagri-zhh5v7eappiwmxthi3etp6h.streamlit.app/)
[![GitHub](https://img.shields.io/badge/📂-GitHub_Repo-181717?style=for-the-badge&logo=github)](https://github.com/Goda-Emad/SmartAgri)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

## 📖 Overview

**SmartAgri** is an intelligent **Retrieval-Augmented Generation (RAG)** system designed to answer agricultural questions by retrieving relevant information from a curated knowledge base of agricultural documents, research papers, and reports.

The system combines:
- **Semantic Search** using Sentence Transformers
- **Vector Storage** with ChromaDB
- **Re-ranking** using Cross-Encoders
- **LLM Generation** with Groq API (Llama 3.3 70B)
- **User-Friendly Interface** powered by Streamlit

---

## 🚀 Live Demo

Try the application here:  
👉 [**https://smartagri-zhh5v7eappiwmxthi3etp6h.streamlit.app/**](https://smartagri-zhh5v7eappiwmxthi3etp6h.streamlit.app/)

---

## 🧠 How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  1. User asks a question                                        │
│     "What is crop marketing?"                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Embedding Generation                                        │
│     Convert question to vector using MiniLM                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. Vector Search (ChromaDB)                                    │
│     Retrieve top-k most similar documents                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. Re-ranking (Cross-Encoder)                                  │
│     Re-rank results for better relevance                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Context Construction                                        │
│     Build context from retrieved documents                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. LLM Generation (Groq API)                                   │
│     Generate answer with source citations                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. Answer with Sources                                         │
│     "Crop marketing is..." (Source: Chapter12.pdf)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Embeddings** | Sentence Transformers (`paraphrase-multilingual-MiniLM-L12-v2`) |
| **Vector Store** | ChromaDB |
| **Re-ranking** | Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) |
| **LLM** | Groq API (`llama-3.3-70b-versatile`) |
| **UI Framework** | Streamlit |
| **Language** | Python 3.11+ |

---

## 📁 Project Structure

```
SmartAgri/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── packages.txt              # System packages
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
│
├── .streamlit/
│   └── config.toml           # Streamlit configuration
│
├── assets/
│   └── team/                 # Team member photos
│
├── components/
│   ├── __init__.py
│   ├── sidebar.py            # Unified sidebar component
│   └── chat_utils.py         # Chat utility functions
│
├── core/
│   ├── __init__.py
│   ├── config.py             # Application configuration
│   ├── constants.py          # Application constants
│   └── prompts.py            # Prompt templates
│
├── database/
│   ├── __init__.py
│   ├── chroma_loader.py      # ChromaDB operations
│   ├── embeddings.py         # Embedding generation
│   ├── docx_loader.py        # DOCX file loader
│   └── text_loader.py        # TXT file loader
│
├── knowledge_base/
│   ├── crops/                # Crop-related documents
│   ├── soil/                 # Soil-related documents
│   ├── irrigation/           # Irrigation-related documents
│   ├── fertilizers/          # Fertilizer-related documents
│   └── pests/                # Pest-related documents
│
├── llm/
│   ├── __init__.py
│   └── groq_client.py        # Groq API client
│
├── pages/
│   ├── 1_Chat.py             # Chat interface
│   ├── 2_Documents.py        # Document management
│   └── 3_Analytics.py        # Analytics dashboard
│
├── rag/
│   ├── __init__.py
│   ├── retriever.py          # Document retrieval
│   ├── qa_engine.py          # RAG pipeline
│   ├── reranker.py           # Result re-ranking
│   └── chunking.py           # Text chunking
│
├── scripts/
│   └── build_index.py        # ChromaDB index builder
│
├── services/
│   ├── __init__.py
│   └── chat_service.py       # Chat service logic
│
├── styles/
│   └── custom.css            # Custom CSS styles
│
└── utils/
    ├── __init__.py
    ├── logger.py             # Logging system
    └── file_utils.py         # File utilities
```

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Goda-Emad/SmartAgri.git
cd SmartAgri
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.streamlit/secrets.toml` file:

```toml
GROQ_API_KEY = "your-groq-api-key"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

### 5. Run the Application

```bash
streamlit run app.py
```

---

## 🌍 Deployment

### Streamlit Cloud

1. Push your code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Deploy from your GitHub repository
4. Add secrets in **Settings → Secrets**:

```toml
GROQ_API_KEY = "your-groq-api-key"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

---

## 📊 Features

### ✅ Chat Interface
- Ask agricultural questions in **English or Arabic**
- Get **source-backed answers** with citations
- **Conversation memory** for follow-up questions
- Suggested questions to get started

### ✅ Document Management
- Upload new agricultural documents (PDF, DOCX, TXT)
- Preview document content
- Delete documents from the knowledge base
- Re-index the vector store

### ✅ Analytics Dashboard
- Document statistics by category
- File type distribution
- Farm/crop analysis
- Productivity scores & contract values

### ✅ Green Theme
- Light and Dark mode support
- Responsive design for mobile and desktop
- RTL support for Arabic language

---

## 👥 Team

| Name | Role |
|------|------|
| **Alwafa Ashour** | Team Lead & Business Analyst |
| **Ibrahim Elshafey** | AI/ML Engineer |
| **Goda Emad** | Full-Stack Developer |

---

## 🙏 Acknowledgments

Special thanks to our supervisor:

**Dr. Ibrahim Bassiony** – for his invaluable guidance, vision, and continuous support throughout this project.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

---

## 📧 Contact

For any inquiries, please contact:

- **GitHub:** [Goda-Emad](https://github.com/Goda-Emad)
- **LinkedIn:** [Goda Emad](https://www.linkedin.com/in/goda-emad/)

---

> ⭐ If you find this project useful, please consider giving it a star on GitHub!

*Built with ❤️ by the SmartAgri Team*
