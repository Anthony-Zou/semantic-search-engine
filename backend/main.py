from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import pymysql
import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np

app = FastAPI(title="Simple RAG Knowledge Base")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=False  # For storing binary embeddings
)

def get_db():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "mysql"),
        user=os.getenv("MYSQL_USER", "raguser"),
        password=os.getenv("MYSQL_PASSWORD", "ragpassword"),
        database=os.getenv("MYSQL_DATABASE", "rag_db")
    )

# Pydantic models
class Document(BaseModel):
    title: str
    content: str

class Query(BaseModel):
    question: str
    top_k: int = 3

# Endpoints
@app.get("/")
def read_root():
    return {"message": "Simple RAG Knowledge Base API"}

@app.get("/health")
def health_check():
    try:
        redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"
    
    try:
        conn = get_db()
        conn.close()
        mysql_status = "connected"
    except:
        mysql_status = "disconnected"
    
    return {"redis": redis_status, "mysql": mysql_status}

@app.post("/documents")
def add_document(doc: Document):
    """Add a document and create embeddings"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Insert document into MySQL
        cursor.execute(
            "INSERT INTO documents (title, content) VALUES (%s, %s)",
            (doc.title, doc.content)
        )
        doc_id = cursor.lastrowid
        
        # Split content into chunks (simple: by sentences)
        chunks = doc.content.split('. ')
        
        # Create embeddings for each chunk
        for idx, chunk in enumerate(chunks):
            if chunk.strip():
                # Generate embedding
                embedding = model.encode(chunk)
                
                # Store in Redis
                redis_key = f"emb:doc{doc_id}:chunk{idx}"
                redis_client.set(redis_key, embedding.tobytes())
                
                # Store metadata in MySQL
                cursor.execute(
                    """INSERT INTO embeddings 
                    (document_id, chunk_text, chunk_index, redis_key) 
                    VALUES (%s, %s, %s, %s)""",
                    (doc_id, chunk, idx, redis_key)
                )
        
        conn.commit()
        return {
            "status": "success",
            "document_id": doc_id,
            "chunks_created": len(chunks)
        }
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/documents")
def list_documents():
    """List all documents"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, created_at FROM documents ORDER BY created_at DESC")
    docs = cursor.fetchall()
    
    conn.close()
    
    return {
        "documents": [
            {"id": d[0], "title": d[1], "created_at": str(d[2])}
            for d in docs
        ]
    }

@app.post("/search")
def search(query: Query):
    """Semantic search using RAG"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Generate embedding for query
        query_embedding = model.encode(query.question)
        
        # Get all embeddings from MySQL
        cursor.execute("""
            SELECT e.id, e.chunk_text, e.redis_key, d.title 
            FROM embeddings e
            JOIN documents d ON e.document_id = d.id
        """)
        all_chunks = cursor.fetchall()
        
        if not all_chunks:
            return {"results": [], "message": "No documents found"}
        
        # Calculate similarities
        similarities = []
        for chunk_id, chunk_text, redis_key, doc_title in all_chunks:
            # Get embedding from Redis
            embedding_bytes = redis_client.get(redis_key)
            if embedding_bytes:
                chunk_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
                
                # Cosine similarity
                similarity = np.dot(query_embedding, chunk_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                )
                
                similarities.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "document_title": doc_title,
                    "similarity": float(similarity)
                })
        
        # Sort by similarity and get top_k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = similarities[:query.top_k]
        
        return {
            "query": query.question,
            "results": top_results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.delete("/documents/{doc_id}")
def delete_document(doc_id: int):
    """Delete a document and its embeddings"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get Redis keys to delete
        cursor.execute(
            "SELECT redis_key FROM embeddings WHERE document_id = %s",
            (doc_id,)
        )
        redis_keys = [row[0] for row in cursor.fetchall()]
        
        # Delete from Redis
        for key in redis_keys:
            redis_client.delete(key)
        
        # Delete from MySQL (cascade will handle embeddings table)
        cursor.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
        
        conn.commit()
        return {"status": "deleted", "document_id": doc_id}
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
