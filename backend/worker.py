"""
Kafka Consumer Worker for Async Document Embedding Processing

This worker consumes messages from the 'document-uploads' Kafka topic,
generates embeddings for document chunks, and stores them in MySQL and Redis.
"""
import os
import json
import logging
import pymysql
import redis
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from sentence_transformers import SentenceTransformer
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize embedding model
logger.info("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
logger.info("Model loaded successfully")

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=False  # For storing binary embeddings
)

def get_db():
    """Get MySQL database connection"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "mysql"),
        user=os.getenv("MYSQL_USER", "raguser"),
        password=os.getenv("MYSQL_PASSWORD", "ragpassword"),
        database=os.getenv("MYSQL_DATABASE", "rag_db")
    )

def process_document(message):
    """
    Process a document message from Kafka:
    1. Extract document data
    2. Split content into chunks
    3. Generate embeddings for each chunk
    4. Store embeddings in Redis
    5. Store metadata in MySQL
    """
    try:
        data = message.value
        doc_id = data.get('document_id')
        content = data.get('content', '')
        title = data.get('title', 'Unknown')
        
        if not doc_id or not content:
            logger.error(f"Invalid message: missing document_id or content")
            return False
        
        logger.info(f"Processing document {doc_id}: {title}")
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            # Split content into chunks (simple: by sentences)
            chunks = content.split('. ')
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
            
            logger.info(f"Document {doc_id}: Split into {len(chunks)} chunks")
            
            # Process each chunk
            processed_chunks = 0
            for idx, chunk in enumerate(chunks):
                try:
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
                    
                    processed_chunks += 1
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {idx} of document {doc_id}: {e}")
                    continue
            
            # Update document status (if you have a status column)
            # cursor.execute(
            #     "UPDATE documents SET status = 'processed' WHERE id = %s",
            #     (doc_id,)
            # )
            
            conn.commit()
            logger.info(f"✅ Successfully processed document {doc_id}: {processed_chunks}/{len(chunks)} chunks")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error processing document {doc_id}: {e}", exc_info=True)
            return False
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        return False

def main():
    """Main worker loop"""
    kafka_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9093").split(',')
    
    logger.info(f"Connecting to Kafka at {kafka_servers}")
    
    consumer = KafkaConsumer(
        'document-uploads',
        bootstrap_servers=kafka_servers,
        group_id='embedding-workers',
        auto_offset_reset='earliest',  # Start from beginning if no offset
        enable_auto_commit=True,  # Auto-commit offsets
        auto_commit_interval_ms=1000,  # Commit every second
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=1000,  # Timeout for polling
        max_poll_records=10,  # Process up to 10 messages at a time
    )
    
    logger.info("✅ Connected to Kafka. Waiting for messages...")
    logger.info(f"Consumer group: embedding-workers")
    logger.info(f"Topic: document-uploads")
    
    try:
        for message in consumer:
            logger.info(f"📨 Received message from partition {message.partition}, offset {message.offset}")
            
            # Process the message
            success = process_document(message)
            
            if success:
                logger.info(f"✅ Message processed successfully")
            else:
                logger.warning(f"⚠️ Message processing failed (check logs above)")
                
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
    except KafkaError as e:
        logger.error(f"Kafka error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        consumer.close()
        logger.info("Worker stopped")

if __name__ == "__main__":
    main()

