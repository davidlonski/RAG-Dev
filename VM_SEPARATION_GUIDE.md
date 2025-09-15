# VM Separation Guide

## 🏗️ Architecture Overview

The RAG-Dev application is now designed to run across **3 separate VMs** for optimal separation of concerns and dependency management:

```
┌─────────────────┐    HTTP    ┌─────────────────┐    HTTP    ┌─────────────────┐
│   Main App VM   │ ────────► │  ChromaDB API   │ ────────► │  ChromaDB       │
│   (Lightweight) │           │  Service VM     │           │  Server VM      │
└─────────────────┘           └─────────────────┘           └─────────────────┘
```

## 📁 Project Structure

```
RAG-Dev/
├── app/                          # Main application (App VM)
│   ├── main.py                   # Streamlit app entry point
│   ├── pages/                    # Teacher/Student portals
│   ├── database/                 # PostgreSQL database layer
│   ├── pptx_rag_quizzer/         # RAG core with HTTP client
│   └── requirements-app-only.txt # Lightweight dependencies
├── chroma-api/                   # ChromaDB API service (API VM)
│   ├── main.py                   # FastAPI service
│   ├── requirements.txt          # ChromaDB dependencies
│   └── README.md                 # API service documentation
└── VM_SEPARATION_GUIDE.md        # This guide
```

## 🚀 Deployment Instructions

### VM 1: ChromaDB Server VM

**Purpose**: Run ChromaDB server with all ML dependencies

**Setup**:
```bash
# Install ChromaDB
pip install chromadb==1.0.15

# Start ChromaDB server
chroma run --host 0.0.0.0 --port 8000
```

**Dependencies**: ChromaDB, sentence-transformers, torch, etc.

### VM 2: ChromaDB API Service VM

**Purpose**: REST API wrapper around ChromaDB

**Setup**:
```bash
cd chroma-api
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with ChromaDB server details

# Start API service
python main.py
```

**Dependencies**: FastAPI, ChromaDB client, ML libraries

**Environment Variables**:
```env
CHROMA_SERVER_HOST=your-chromadb-server.com
CHROMA_SERVER_HTTP_PORT=8000
API_HOST=0.0.0.0
API_PORT=8001
```

### VM 3: Main App VM

**Purpose**: Streamlit application with minimal dependencies

**Setup**:
```bash
cd app
pip install -r requirements-app-only.txt

# Configure environment
# Edit .env with API service details

# Start application
streamlit run main.py
```

**Dependencies**: Streamlit, PostgreSQL, requests (NO ChromaDB deps)

**Environment Variables**:
```env
# PostgreSQL Database
POSTGRES_HOST=your-postgres-server.com
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_PORT=5432
POSTGRES_DB=rag_dev

# ChromaDB API Service (NOT direct ChromaDB)
CHROMA_API_URL=http://your-api-server.com:8001

# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key
```

## 🔧 Configuration

### Main App Configuration

The main app now uses the HTTP client instead of direct ChromaDB:

```python
from pptx_rag_quizzer.rag_core import RAGCore

# Production configuration (uses HTTP API)
rag_core = RAGCore(
    use_api=True,
    chroma_api_url="http://your-api-server.com:8001"
)

# Or use environment variable
rag_core = RAGCore(use_api=True)  # Uses CHROMA_API_URL from .env
```

### API Service Configuration

The API service acts as a bridge between the app and ChromaDB:

```python
# API service handles all ChromaDB operations
# App only makes HTTP requests to the API service
```

## 📊 Benefits

### Dependency Separation
- **App VM**: No torch, sentence-transformers, or ChromaDB dependencies
- **API VM**: Contains all ChromaDB and ML dependencies
- **ChromaDB VM**: Pure ChromaDB server

### Scalability
- **Independent Scaling**: Each VM can be scaled based on demand
- **Resource Optimization**: App VM can be lightweight, API VM can be powerful
- **Load Distribution**: ChromaDB operations isolated to dedicated VMs

### Maintainability
- **Clean Separation**: Each VM has a single responsibility
- **Easy Updates**: Update ChromaDB without touching the main app
- **Debugging**: Isolate issues to specific VMs

## 🔒 Security

### Network Configuration
- **Private Networks**: Use VPCs for internal communication
- **Firewall Rules**: Restrict access between VMs
- **API Authentication**: Add API keys if needed

### Access Control
- **App VM**: Accessible to users
- **API VM**: Only accessible from App VM
- **ChromaDB VM**: Only accessible from API VM

## 🧪 Testing

### Health Checks
```bash
# Test ChromaDB server
curl http://chromadb-server:8000/api/v1/heartbeat

# Test API service
curl http://api-server:8001/health

# Test main app
# Access via browser at http://app-server:8501
```

### Integration Testing
```python
# Test the full pipeline
from pptx_rag_quizzer.rag_core import RAGCore

rag_core = RAGCore(use_api=True)
# All operations go through HTTP API
```

## 📈 Performance Considerations

### VM Sizing
- **App VM**: Lightweight (2-4 CPU, 4-8GB RAM)
- **API VM**: Medium (4-8 CPU, 8-16GB RAM)
- **ChromaDB VM**: Powerful (8+ CPU, 16+ GB RAM)

### Network Optimization
- **Low Latency**: Place VMs in same region/availability zone
- **High Bandwidth**: Ensure sufficient network capacity
- **Connection Pooling**: HTTP client reuses connections

## 🎯 Summary

✅ **Complete VM Separation**: Each service runs on its own VM  
✅ **Dependency Isolation**: App VM has no heavy ML dependencies  
✅ **Scalable Architecture**: Each component can scale independently  
✅ **Production Ready**: Proper separation for enterprise deployment  
✅ **Easy Maintenance**: Clear boundaries between components  

The RAG-Dev application now supports true VM separation with ChromaDB operations completely isolated from the main application!
