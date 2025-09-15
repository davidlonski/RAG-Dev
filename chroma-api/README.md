# ChromaDB API Service

A standalone REST API service that handles all ChromaDB operations. This service runs on its own VM and provides HTTP endpoints for ChromaDB functionality.

## 🏗️ Architecture

```
┌─────────────────┐    HTTP    ┌─────────────────┐    HTTP    ┌─────────────────┐
│   Main App VM   │ ────────► │  ChromaDB API   │ ────────► │  ChromaDB       │
│   (Lightweight) │           │  Service VM     │           │  Server VM      │
└─────────────────┘           └─────────────────┘           └─────────────────┘
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp env.example .env
# Edit .env with your configuration
```

### 3. Start the Service
```bash
python main.py
```

The service will start on `http://localhost:8001` by default.

## 📡 API Endpoints

### Health Check
- **GET** `/health` - Check service health

### Collection Management
- **GET** `/collections` - List all collections
- **POST** `/collections` - Create a new collection
- **DELETE** `/collections/{name}` - Delete a collection
- **GET** `/collections/{name}/exists` - Check if collection exists

### Document Operations
- **POST** `/collections/{name}/add` - Add documents to collection
- **POST** `/collections/{name}/query` - Query collection for similar documents
- **POST** `/collections/{name}/get` - Get all documents from collection

## 🔧 Configuration

### Environment Variables

- `CHROMA_SERVER_HOST` - ChromaDB server hostname (default: localhost)
- `CHROMA_SERVER_HTTP_PORT` - ChromaDB server port (default: 8000)
- `API_HOST` - API service host (default: 0.0.0.0)
- `API_PORT` - API service port (default: 8001)

### Production Deployment

1. **Start ChromaDB Server** (on ChromaDB VM):
   ```bash
   chroma run --host 0.0.0.0 --port 8000
   ```

2. **Start API Service** (on API VM):
   ```bash
   export CHROMA_SERVER_HOST=your-chromadb-server.com
   export API_HOST=0.0.0.0
   export API_PORT=8001
   python main.py
   ```

3. **Configure Main App** (on App VM):
   ```python
   # Use the API service instead of direct ChromaDB
   CHROMA_API_URL = "http://your-api-server.com:8001"
   ```

## 🧪 Testing

Test the API service:

```bash
# Health check
curl http://localhost:8001/health

# List collections
curl http://localhost:8001/collections

# Create collection
curl -X POST http://localhost:8001/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "test_collection", "metadata": {}}'
```

## 🔒 Security

For production deployment:

1. **Network Security**: Use private networks/VPCs
2. **Firewall Rules**: Restrict access to API service
3. **Authentication**: Add API key authentication if needed
4. **HTTPS**: Use SSL/TLS for encrypted communication

## 📊 Monitoring

The service provides health check endpoints and detailed error messages for monitoring and debugging.

## 🎯 Benefits

- **Separation of Concerns**: ChromaDB dependencies isolated to API service
- **Scalability**: API service can be scaled independently
- **Maintainability**: Clean separation between app logic and ChromaDB operations
- **Flexibility**: Easy to swap ChromaDB implementation or add caching
