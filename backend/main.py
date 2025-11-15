from fastapi import FastAPI, HTTPException, Query as FastAPIQuery
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import pymysql
import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from kafka import KafkaProducer
from kafka.errors import KafkaError
from datetime import datetime

app = FastAPI(title="Simple RAG Knowledge Base")

# Initialize Kafka Producer (lazy initialization)
_kafka_producer = None

def get_kafka_producer():
    """Get or create Kafka producer (singleton pattern)"""
    global _kafka_producer
    if _kafka_producer is None:
        kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9093").split(',')
        try:
            _kafka_producer = KafkaProducer(
                bootstrap_servers=kafka_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,
            )
        except Exception as e:
            print(f"Warning: Could not connect to Kafka: {e}")
            print("Kafka features will be disabled. API will work in sync mode.")
    return _kafka_producer

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
        database=os.getenv("MYSQL_DATABASE", "rag_db"),
        ssl_disabled=True  # Disable SSL for local Docker MySQL
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
    except Exception as e:
        redis_status = f"disconnected: {str(e)}"
    
    try:
        conn = get_db()
        conn.close()
        mysql_status = "connected"
    except Exception as e:
        mysql_status = f"disconnected: {str(e)}"
    
    # Check Kafka
    kafka_status = "disconnected"
    try:
        producer = get_kafka_producer()
        if producer:
            # Check if producer is connected by checking bootstrap servers
            # KafkaProducer doesn't have list_topics, so we check bootstrap_connected
            if hasattr(producer, 'bootstrap_connected'):
                if producer.bootstrap_connected():
                    kafka_status = "connected"
                else:
                    kafka_status = "disconnected: not connected to bootstrap servers"
            else:
                # Fallback: try to get cluster metadata
                from kafka import KafkaAdminClient
                admin = KafkaAdminClient(
                    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9093").split(','),
                    request_timeout_ms=2000
                )
                admin.list_topics(timeout_ms=2000)
                admin.close()
                kafka_status = "connected"
        else:
            kafka_status = "disconnected: producer not initialized"
    except Exception as e:
        kafka_status = f"disconnected: {str(e)}"
    
    return {
        "redis": redis_status,
        "mysql": mysql_status,
        "kafka": kafka_status
    }

@app.post("/documents")
def add_document(
    doc: Document,
    async_mode: bool = FastAPIQuery(False, description="Process asynchronously via Kafka")
):
    """
    Add a document and create embeddings.
    
    - async_mode=False: Process synchronously (blocking, returns when done)
    - async_mode=True: Queue document for async processing via Kafka (returns immediately)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Insert document into MySQL
        cursor.execute(
            "INSERT INTO documents (title, content) VALUES (%s, %s)",
            (doc.title, doc.content)
        )
        doc_id = cursor.lastrowid
        conn.commit()
        
        # If async mode, publish to Kafka
        if async_mode:
            producer = get_kafka_producer()
            if producer:
                try:
                    producer.send(
                        'document-uploads',
                        key=f'doc_{doc_id}',
                        value={
                            'document_id': doc_id,
                            'title': doc.title,
                            'content': doc.content,
                            'status': 'pending',
                            'created_at': datetime.now().isoformat()
                        }
                    )
                    producer.flush()  # Ensure message is sent
                    
                    return {
                        "status": "accepted",
                        "document_id": doc_id,
                        "message": "Document queued for async processing",
                        "processing_mode": "async"
                    }
                except KafkaError as e:
                    # Fall back to sync if Kafka fails
                    print(f"Kafka error: {e}. Falling back to sync processing.")
        
        # Synchronous processing (original behavior)
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
            "chunks_created": len(chunks),
            "processing_mode": "sync"
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
        
        # Publish search analytics to Kafka (non-blocking)
        try:
            producer = get_kafka_producer()
            if producer:
                producer.send(
                    'search-analytics',
                    value={
                        'query': query.question,
                        'results_count': len(top_results),
                        'top_similarity': float(top_results[0]['similarity']) if top_results else 0.0,
                        'timestamp': datetime.now().isoformat()
                    }
                )
                # Don't flush - let it send async
        except:
            pass  # Don't fail search if analytics fails
        
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
