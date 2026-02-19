# RAG Customer Support System

A production-ready Retrieval-Augmented Generation (RAG) customer support system built with Flask, Streamlit, Amazon Bedrock, FAISS, and AWS S3.

---

## Architecture

```
┌──────────────┐     HTTP      ┌─────────────────────────────────────┐
│  Streamlit   │ ◄──────────── │          Flask REST API              │
│  Frontend    │               │                                     │
│  :8501       │               │  /api/documents  /api/search        │
└──────────────┘               │  /api/rag        /health            │
                               └──────────┬──────────────────────────┘
                                          │
                    ┌─────────────────────┼──────────────────────┐
                    │                     │                      │
               ┌────▼─────┐      ┌───────▼──────┐    ┌─────────▼──────┐
               │ Amazon   │      │  FAISS CPU   │    │  Amazon        │
               │ S3       │      │  Vector Store│    │  Bedrock       │
               │ (raw docs│      │  (embeddings)│    │  • Titan Embed │
               │  storage)│      └──────────────┘    │  • Claude 3    │
               └──────────┘                          └────────────────┘
```

### Request flow for a user question

1. **User types a question** in the Streamlit chat.
2. Frontend POSTs `{ query, session_history }` to `/api/rag/query`.
3. Backend **embeds** the query with Bedrock (Titan Embed Text v2).
4. Backend **searches** FAISS for the top-K most similar document chunks.
5. If the best score < `CONFIDENCE_THRESHOLD` (default 0.30) → returns a polite fallback.
6. Otherwise, top-K chunks are injected into a **prompt** and sent to Claude 3 Haiku.
7. Response (answer + citations + confidence) is returned to the frontend.

---

## Project Structure

```
rag-support/
├── backend/
│   ├── app.py                  # Flask app factory
│   ├── config.py               # Dev / Prod / Test configs
│   ├── requirements.txt
│   ├── api/
│   │   ├── documents.py        # Upload, list, delete endpoints
│   │   ├── search.py           # Semantic search endpoint
│   │   └── rag.py              # RAG query endpoint
│   ├── services/
│   │   ├── bedrock_service.py  # Embeddings + LLM calls
│   │   ├── s3_service.py       # S3 upload / download
│   │   ├── faiss_service.py    # FAISS CRUD + search
│   │   └── chunker.py          # Text splitting
│   └── tests/
│       └── test_api.py         # Pytest unit tests
├── frontend/
│   └── streamlit_app.py        # Streamlit chat UI
├── infra/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
├── .env.example                # Copy → .env and fill in values
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI/CD skeleton
└── README.md
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Docker + Docker Compose | Latest |
| AWS CLI | 2.x |
| AWS account with Bedrock access | — |

---

## AWS Setup

### 1. Enable Bedrock Models

In the AWS Console → **Amazon Bedrock → Model access**:

- ✅ `amazon.titan-embed-text-v2:0`
- ✅ `anthropic.claude-3-haiku-20240307-v1:0`

> Models must be enabled in the **same region** as your deployment.

### 2. Create an S3 Bucket

```bash
aws s3 mb s3://rag-support-docs --region us-east-1
# Enable versioning (recommended for audit trail)
aws s3api put-bucket-versioning \
  --bucket rag-support-docs \
  --versioning-configuration Status=Enabled
```

### 3. IAM Policy

Create an IAM policy and attach it to your deployment role (ECS Task Role, EC2 Instance Profile, or IAM user for local dev).

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
      ]
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::rag-support-docs",
        "arn:aws:s3:::rag-support-docs/*"
      ]
    }
  ]
}
```

> **Production best practice**: Use IAM Roles (ECS Task Role / EC2 Instance Profile) instead of static access keys. The app automatically uses the instance credentials via boto3's credential chain.

---

## Local Development

### Without Docker

```bash
# 1. Clone and enter the project
git clone https://github.com/yourorg/rag-support.git
cd rag-support

# 2. Set up virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your AWS credentials and bucket name

# 5. Start the Flask backend
cd backend
export FLASK_ENV=development
flask --app app:create_app run --debug --port 5000

# 6. In a new terminal, start the Streamlit frontend
cd frontend
pip install streamlit requests
# Edit API_BASE in streamlit_app.py → "http://localhost:5000"
streamlit run streamlit_app.py
```

### With Docker Compose

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your values

# 2. Build and start all services
docker compose -f infra/docker-compose.yml up --build

# Frontend: http://localhost:8501
# Backend:  http://localhost:5000/health
```

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
FLASK_ENV=testing pytest tests/ -v
```

Tests mock AWS calls (Bedrock + S3) so no AWS credentials are required.

---

## API Reference

### Health

```
GET /health
→ { "status": "ok", "service": "rag-support-api" }
```

### Upload Document

```
POST /api/documents/upload
Content-Type: multipart/form-data
Body: file=<binary>

→ 201 { "document_id": "...", "filename": "...", "s3_key": "...", "num_chunks": 12 }
→ 400 / 415 / 500 { "error": "..." }
```

Supported file types: `.txt`, `.pdf`, `.md`, `.html`, `.csv`

### List Documents

```
GET /api/documents/
→ 200 { "documents": [ { "document_id": "...", "filename": "..." } ] }
```

### Delete Document

```
DELETE /api/documents/<document_id>
→ 200 { "document_id": "...", "removed_chunks": 5 }
```

### Semantic Search

```
POST /api/search/
Content-Type: application/json
Body: { "query": "refund policy", "top_k": 5 }

→ 200 {
    "query": "refund policy",
    "results": [
      {
        "score": 0.87,
        "document_id": "...",
        "filename": "policy.txt",
        "chunk_index": 2,
        "text": "..."
      }
    ]
  }
```

### RAG Query

```
POST /api/rag/query
Content-Type: application/json
Body: {
  "query": "How do I reset my password?",
  "top_k": 5,
  "session_history": [           ← optional, for multi-turn
    { "role": "user",      "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}

→ 200 {
    "answer": "To reset your password, click ...",
    "confidence": 0.87,
    "citations": [
      {
        "passage_id": 1,
        "filename": "kb.txt",
        "document_id": "...",
        "chunk_index": 0,
        "text": "...",
        "score": 0.87
      }
    ],
    "fallback": false
  }
```

**Confidence & Fallback logic:**
- `confidence` = cosine similarity of the best matching chunk (0.0 – 1.0).
- If `confidence < CONFIDENCE_THRESHOLD` (default `0.30`), `fallback: true` and a polite "no relevant information found" message is returned instead of calling the LLM.

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (required) | Flask secret key |
| `FLASK_ENV` | `production` | `development` / `production` / `testing` |
| `CORS_ORIGINS` | `http://localhost:8501` | Comma-separated allowed origins |
| `AWS_REGION` | `us-east-1` | AWS region |
| `AWS_ACCESS_KEY_ID` | — | Leave blank to use IAM role |
| `AWS_SECRET_ACCESS_KEY` | — | Leave blank to use IAM role |
| `S3_BUCKET_NAME` | `rag-support-docs` | S3 bucket for raw documents |
| `BEDROCK_EMBED_MODEL` | `amazon.titan-embed-text-v2:0` | Embedding model ID |
| `BEDROCK_LLM_MODEL` | `anthropic.claude-3-haiku-20240307-v1:0` | LLM model ID |
| `BEDROCK_MAX_TOKENS` | `1024` | Max tokens per LLM response |
| `FAISS_INDEX_PATH` | `/tmp/faiss_index` | Path to persist FAISS index |
| `FAISS_METADATA_PATH` | `/tmp/faiss_metadata.pkl` | Path to persist chunk metadata |
| `CHUNK_SIZE` | `800` | Characters per text chunk |
| `CHUNK_OVERLAP` | `150` | Overlap between consecutive chunks |
| `TOP_K_RESULTS` | `5` | Chunks retrieved per query |
| `CONFIDENCE_THRESHOLD` | `0.30` | Minimum score for non-fallback response |

---

## Production Deployment Tips

- **Persist FAISS index**: mount a volume (or copy to S3 on shutdown) so the index survives container restarts.
- **Scale horizontally**: if running multiple backend replicas, move FAISS to a shared volume (EFS) or replace with a managed vector DB (OpenSearch, Pinecone).
- **IAM Roles over keys**: attach an ECS Task Role with the policy above; remove `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` from your environment.
- **Secrets management**: use AWS Secrets Manager or SSM Parameter Store; inject secrets as environment variables at runtime.
- **Rate limiting**: add `flask-limiter` to the backend to protect the `/api/rag/query` endpoint.

---

## Multi-language Support

The default embedding model (`amazon.titan-embed-text-v2:0`) natively supports **100+ languages**. Upload documents in any supported language and query in the same (or a different) language – Titan will embed both into the same semantic space.

For generation, Claude 3 Haiku also supports multilingual input/output.
