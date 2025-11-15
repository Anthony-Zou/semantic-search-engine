# 🚀 Kafka Integration Guide for RAG Application

## Quick Start

### 1. Start All Services

```bash
docker-compose up -d
```

This will start:
- MySQL
- Redis
- Kafka + Zookeeper
- Kafka UI (http://localhost:8080)
- FastAPI Backend
- Embedding Worker
- Jupyter

### 2. Verify Kafka is Running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "redis": "connected",
#   "mysql": "connected",
#   "kafka": "connected"
# }
```

**Note:** If any service shows as disconnected, check the error message in the response for details.

### 3. Access Kafka UI

Open http://localhost:8080 in your browser to:
- View topics
- Browse messages
- Monitor consumer groups
- Check partitions

## Architecture with Kafka

```
┌──────────────┐
│   Frontend   │
└──────┬───────┘
       │ HTTP
┌──────▼──────────────────────────────────────┐
│         FastAPI Backend                      │
│  POST /documents?async_mode=true             │
│  → Publishes to Kafka                        │
│  → Returns immediately                       │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│    Kafka Topic: document-uploads            │
│    (3 partitions for parallel processing)   │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│    Embedding Worker (Consumer)              │
│  - Consumes from Kafka                       │
│  - Generates embeddings                     │
│  - Stores in MySQL/Redis                    │
└─────────────────────────────────────────────┘
```

## Using the API

### Sync Mode (Default)

```bash
# Process document synchronously
curl -X POST "http://localhost:8000/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Guide",
    "content": "Python is a programming language. It is easy to learn."
  }'
```

**Response:**
```json
{
  "status": "success",
  "document_id": 1,
  "chunks_created": 2,
  "processing_mode": "sync"
}
```

### Async Mode (Kafka)

```bash
# Process document asynchronously via Kafka
curl -X POST "http://localhost:8000/documents?async_mode=true" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python Guide",
    "content": "Python is a programming language. It is easy to learn."
  }'
```

**Response:**
```json
{
  "status": "accepted",
  "document_id": 2,
  "message": "Document queued for async processing",
  "processing_mode": "async"
}
```

The document is immediately queued, and the embedding worker will process it in the background.

## Topics Created

### 1. `document-uploads`
- **Purpose**: Queue documents for async embedding generation
- **Partitions**: 3 (for parallel processing)
- **Consumer Group**: `embedding-workers`

**Message Format:**
```json
{
  "document_id": 123,
  "title": "Document Title",
  "content": "Document content...",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00"
}
```

### 2. `search-analytics`
- **Purpose**: Track search queries for analytics
- **Partitions**: 1
- **Consumer Group**: None (fire-and-forget)

**Message Format:**
```json
{
  "query": "What is Python?",
  "results_count": 3,
  "top_similarity": 0.85,
  "timestamp": "2024-01-15T10:30:00"
}
```

## Running Examples

### Producer Example

```bash
# From backend directory
cd backend/examples
python kafka_producer_example.py
```

This will send test messages to Kafka topics.

### Consumer Example

```bash
# From backend directory
cd backend/examples
python kafka_consumer_example.py
```

This will consume and display messages in real-time.

### Topics Manager

```bash
# List all topics
python kafka_topics_manager.py list

# Create a new topic
python kafka_topics_manager.py create my-topic 3 1

# Describe a topic
python kafka_topics_manager.py describe document-uploads

# Delete a topic
python kafka_topics_manager.py delete my-topic
```

## Monitoring

### Check Worker Logs

```bash
docker logs -f rag-embedding-worker
```

### Check Kafka Logs

```bash
docker logs -f rag-kafka
```

### View Messages in Kafka UI

1. Open http://localhost:8080
2. Select cluster: `local`
3. Click on topic: `document-uploads`
4. View messages in real-time

### Check Consumer Lag

In Kafka UI:
1. Go to "Consumer Groups"
2. Select `embedding-workers`
3. View lag per partition

## Scaling Workers

To scale the embedding worker:

```bash
# Run multiple workers (they'll share the load)
docker-compose up -d --scale embedding-worker=3
```

Each worker will consume from different partitions, enabling parallel processing.

## Troubleshooting

### Kafka Not Connecting

1. Check if Kafka is running:
   ```bash
   docker ps | grep kafka
   ```

2. Check Kafka logs:
   ```bash
   docker logs rag-kafka
   ```

3. Verify health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```

4. **Kafka Version Issue:** If you see `KAFKA_PROCESS_ROLES` errors, ensure you're using `confluentinc/cp-kafka:7.4.0` or later with proper Zookeeper configuration (not KRaft mode).

### MySQL Not Connecting

1. **SSL Issue:** If MySQL shows as disconnected, ensure `ssl_disabled=True` is set in the connection:
   ```python
   pymysql.connect(
       host='mysql',
       user='raguser',
       password='ragpassword',
       database='rag_db',
       ssl_disabled=True  # Required for local Docker MySQL
   )
   ```

2. Check MySQL is running:
   ```bash
   docker ps | grep mysql
   docker logs rag-mysql
   ```

3. Test connection directly:
   ```bash
   docker exec rag-mysql mysql -u raguser -pragpassword -e "SELECT 1" rag_db
   ```

### Messages Not Being Processed

1. Check worker logs:
   ```bash
   docker logs rag-embedding-worker
   ```

2. Check if worker is consuming:
   - Look for "Received message" logs
   - Check Kafka UI for consumer lag

3. Verify topic exists:
   ```bash
   docker exec -it rag-kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

### Consumer Lag Building Up

1. **Add more workers:**
   ```bash
   docker-compose up -d --scale embedding-worker=5
   ```

2. **Check processing speed:**
   - Look at worker logs for processing time
   - Consider optimizing embedding generation

3. **Increase partitions** (requires topic recreation):
   - More partitions = more parallel consumers

## Best Practices

1. **Use async mode for large documents** - Don't block the API
2. **Monitor consumer lag** - Ensure workers keep up
3. **Scale workers horizontally** - Add more workers as needed
4. **Use keys for ordering** - Same document_id → same partition
5. **Handle errors gracefully** - Implement dead letter queue
6. **Monitor Kafka UI** - Keep an eye on topics and consumers

## Next Steps

1. **Add Dead Letter Queue** - Handle failed messages
2. **Implement Retry Logic** - Retry failed processing
3. **Add Metrics** - Track processing time, throughput
4. **Use Schema Registry** - Validate message schemas
5. **Add Authentication** - Secure Kafka in production

## Resources

- [Kafka Guide](./KAFKA_GUIDE.md) - Comprehensive Kafka learning guide
- [Kafka UI](http://localhost:8080) - Web interface
- [API Docs](http://localhost:8000/docs) - FastAPI documentation

---

**Happy Streaming! 🚀**

