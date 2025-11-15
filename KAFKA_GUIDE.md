# 🚀 Apache Kafka: Complete Technical Guide & RAG Integration

## Table of Contents

1. [Why Kafka is Essential](#why-kafka-is-essential)
2. [Kafka Fundamentals](#kafka-fundamentals)
3. [Core Concepts Deep Dive](#core-concepts-deep-dive)
4. [Kafka Architecture](#kafka-architecture)
5. [Setting Up Kafka](#setting-up-kafka)
6. [Kafka Python Client (kafka-python)](#kafka-python-client)
7. [Integrating Kafka into RAG Application](#integrating-kafka-into-rag-application)
8. [Use Cases for RAG + Kafka](#use-cases-for-rag--kafka)
9. [Advanced Patterns](#advanced-patterns)
10. [Performance & Optimization](#performance--optimization)
11. [Monitoring & Operations](#monitoring--operations)
12. [Troubleshooting](#troubleshooting)
13. [Best Practices](#best-practices)

---

## Why Kafka is Essential

### What is Apache Kafka?

**Apache Kafka** is a distributed event streaming platform capable of handling trillions of events per day. Originally developed by LinkedIn, it's now an Apache Software Foundation project and the de-facto standard for event-driven architectures.

### Why Engineers Need Kafka

#### 1. **Decoupling Systems**
- Services communicate via events, not direct calls
- Services can be developed, deployed, and scaled independently
- Reduces tight coupling between microservices

#### 2. **High Throughput**
- Handles millions of messages per second
- Low latency (sub-millisecond)
- Horizontal scalability

#### 3. **Durability & Reliability**
- Messages persisted to disk
- Replication for fault tolerance
- At-least-once delivery guarantees

#### 4. **Real-time Processing**
- Stream processing capabilities
- Event-driven architectures
- Real-time analytics

#### 5. **Industry Standard**
- Used by Netflix, Uber, LinkedIn, Twitter
- Essential for modern distributed systems
- Required knowledge for senior engineers

### Common Use Cases

1. **Event Sourcing**: Store all events as they happen
2. **Log Aggregation**: Centralized logging system
3. **Stream Processing**: Real-time data transformation
4. **Message Queuing**: Asynchronous communication
5. **Activity Tracking**: User behavior tracking
6. **Metrics Collection**: System metrics aggregation
7. **Change Data Capture**: Database change streams

---

## Kafka Fundamentals

### Core Terminology

#### **Topic**
- A category or feed name to which messages are published
- Similar to a table in a database or a folder in a filesystem
- Example: `document-uploads`, `search-queries`, `user-events`

#### **Partition**
- Topics are split into partitions for parallelism
- Each partition is an ordered, immutable sequence of records
- Messages within a partition are ordered
- Partitions enable horizontal scaling

#### **Producer**
- Applications that publish (write) data to topics
- Can choose which partition to write to
- Can send messages synchronously or asynchronously

#### **Consumer**
- Applications that read data from topics
- Organized into consumer groups
- Each consumer group processes all partitions

#### **Broker**
- A Kafka server that stores data and serves clients
- A Kafka cluster consists of multiple brokers
- Each broker has a unique ID

#### **Consumer Group**
- A set of consumers working together to consume a topic
- Each partition is consumed by only one consumer in a group
- Enables parallel processing and load balancing

### The Kafka Ecosystem

```
┌─────────────┐
│  Producers  │  (Applications writing to Kafka)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         Kafka Cluster               │
│  ┌──────────┐  ┌──────────┐         │
│  │ Broker 1 │  │ Broker 2 │  ...    │
│  └──────────┘  └──────────┘         │
│       │              │               │
│  ┌────▼──────────────▼─────┐        │
│  │   Topic: documents      │        │
│  │  ┌────┐ ┌────┐ ┌────┐  │        │
│  │  │ P0 │ │ P1 │ │ P2 │  │        │
│  │  └────┘ └────┘ └────┘  │        │
│  └─────────────────────────┘        │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────┐
│  Consumers  │  (Applications reading from Kafka)
└─────────────┘
```

---

## Core Concepts Deep Dive

### Topics and Partitions

#### Topic Structure

```
Topic: "document-uploads"
├── Partition 0: [msg1, msg4, msg7, ...]
├── Partition 1: [msg2, msg5, msg8, ...]
└── Partition 2: [msg3, msg6, msg9, ...]
```

**Key Properties:**
- **Ordering**: Messages within a partition are ordered
- **Parallelism**: Multiple partitions = parallel processing
- **Replication**: Each partition replicated across brokers
- **Persistence**: Messages stored on disk

#### Partitioning Strategy

**Producer decides partition using:**
1. **Key-based**: Same key → same partition (ensures ordering)
2. **Round-robin**: Distributes evenly across partitions
3. **Custom partitioner**: Custom logic

**Example:**
```python
# Same document_id always goes to same partition
producer.send('document-uploads', 
              key='doc_123',  # Ensures ordering per document
              value=document_data)
```

### Producer Behavior

#### Delivery Semantics

1. **At-most-once**: May lose messages, no duplicates
2. **At-least-once**: No message loss, may have duplicates (default)
3. **Exactly-once**: No loss, no duplicates (requires idempotent producer)

#### Producer Configuration

```python
producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    acks='all',  # Wait for all replicas
    retries=3,
    max_in_flight_requests_per_connection=1,  # For ordering
    enable_idempotence=True,  # Exactly-once semantics
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
```

### Consumer Behavior

#### Consumer Groups

```
Topic: "document-uploads" (3 partitions)

Consumer Group: "embedding-processors"
├── Consumer 1 → Partition 0
├── Consumer 2 → Partition 1
└── Consumer 3 → Partition 2

If Consumer 2 crashes:
├── Consumer 1 → Partition 0
├── Consumer 3 → Partition 1, Partition 2 (rebalancing)
```

**Rebalancing:**
- Happens when consumers join/leave
- Partitions redistributed among active consumers
- Brief pause in processing during rebalance

#### Consumer Offsets

- Kafka tracks what each consumer group has read
- Stored in `__consumer_offsets` topic
- Enables resuming from last position
- Can commit automatically or manually

```python
consumer = KafkaConsumer(
    'document-uploads',
    bootstrap_servers=['kafka:9092'],
    group_id='embedding-processors',
    auto_offset_reset='earliest',  # Start from beginning if no offset
    enable_auto_commit=True,  # Auto-commit offsets
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)
```

### Message Format

```python
{
    "topic": "document-uploads",
    "partition": 0,
    "offset": 12345,
    "key": "doc_123",
    "value": {
        "document_id": 123,
        "title": "Python Guide",
        "content": "..."
    },
    "timestamp": 1699123456789
}
```

---

## Kafka Architecture

### Cluster Architecture

```
┌─────────────────────────────────────────────────────┐
│              Kafka Cluster                          │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │ Broker 1 │    │ Broker 2 │    │ Broker 3 │     │
│  │ (Leader) │    │ (Follower)│   │ (Follower)│     │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘     │
│       │               │               │            │
│  ┌────▼────────────────▼───────────────▼─────┐    │
│  │         Topic: documents                   │    │
│  │  Partition 0 (Leader: B1, Replicas: B2,B3)│    │
│  │  Partition 1 (Leader: B2, Replicas: B1,B3)│    │
│  │  Partition 2 (Leader: B3, Replicas: B1,B2)│    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### Replication

**Replication Factor = 3:**
- 1 Leader: Handles all read/write requests
- 2 Followers: Replicate data, can become leader if leader fails
- Ensures fault tolerance

### Zookeeper (Legacy) vs KRaft (New)

**Zookeeper (Kafka < 3.3):**
- Manages cluster metadata
- Coordinates brokers
- Stores consumer offsets (old versions)

**KRaft (Kafka 3.3+):**
- Kafka-native metadata management
- No Zookeeper dependency
- Better performance and scalability

---

## Setting Up Kafka

### Docker Compose Setup

```yaml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    container_name: kafka-zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    ports:
      - "2181:2181"

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    container_name: kafka-broker
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT_INTERNAL://kafka:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_INTERNAL:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT_INTERNAL
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
      KAFKA_LOG_RETENTION_HOURS: 168
      KAFKA_LOG_SEGMENT_BYTES: 1073741824
    volumes:
      - kafka_data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server localhost:9092 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s
```

**Important Notes:**
- Using version `7.4.0` (not `latest`) ensures compatibility with Zookeeper mode
- The `latest` tag may use KRaft mode which requires different configuration
- Health check ensures Kafka is ready before dependent services start

### Kafka UI (Optional but Recommended)

```yaml
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: kafka-ui
    depends_on:
      - kafka
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9093
```

### Creating Topics

**Using Kafka CLI:**
```bash
docker exec -it kafka-broker kafka-topics \
  --create \
  --topic document-uploads \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

**Using Python:**
```python
from kafka.admin import KafkaAdminClient, NewTopic

admin_client = KafkaAdminClient(
    bootstrap_servers=['localhost:9092']
)

topic = NewTopic(
    name='document-uploads',
    num_partitions=3,
    replication_factor=1
)

admin_client.create_topics([topic])
```

---

## Kafka Python Client

### Installation

```bash
pip install kafka-python
```

### Producer Example

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None
)

# Send a message
future = producer.send(
    'document-uploads',
    key='doc_123',
    value={
        'document_id': 123,
        'title': 'Python Guide',
        'content': 'Python is a programming language...'
    }
)

# Wait for acknowledgment
record_metadata = future.get(timeout=10)
print(f"Sent to {record_metadata.topic}[{record_metadata.partition}][{record_metadata.offset}]")
```

### Consumer Example

```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'document-uploads',
    bootstrap_servers=['localhost:9092'],
    group_id='embedding-processors',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    print(f"Received: {message.value}")
    print(f"Partition: {message.partition}, Offset: {message.offset}")
    # Process message
```

### Async Producer

```python
from kafka import KafkaProducer
import json
import asyncio

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def on_send_success(record_metadata):
    print(f"Sent to {record_metadata.topic}[{record_metadata.partition}][{record_metadata.offset}]")

def on_send_error(exception):
    print(f"Error: {exception}")

# Async send
producer.send(
    'document-uploads',
    value={'document_id': 123, 'title': 'Test'}
).add_callback(on_send_success).add_errback(on_send_error)

producer.flush()  # Ensure all messages are sent
```

---

## Integrating Kafka into RAG Application

### Architecture with Kafka

```
┌──────────────┐
│   Frontend   │
└──────┬───────┘
       │ HTTP
┌──────▼──────────────────────────────────────┐
│         FastAPI Backend                      │
│  ┌────────────────────────────────────────┐  │
│  │ POST /documents                        │  │
│  │  → Publish to Kafka                    │  │
│  │  → Return immediately (async)          │  │
│  └────────────────────────────────────────┘  │
└──────┬───────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│         Kafka Topic: document-uploads       │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│    Embedding Worker (Consumer)              │
│  - Consumes from Kafka                      │
│  - Generates embeddings                     │
│  - Stores in MySQL/Redis                    │
│  - Publishes completion event               │
└─────────────────────────────────────────────┘
```

### Use Case 1: Async Document Processing

**Problem:** Document embedding generation is slow and blocks the API

**Solution:** Use Kafka for async processing

#### Updated API Endpoint

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9093"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.post("/documents")
def add_document(doc: Document):
    """Add document - async processing via Kafka"""
    # Insert document metadata immediately
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO documents (title, content) VALUES (%s, %s)",
            (doc.title, doc.content)
        )
        doc_id = cursor.lastrowid
        conn.commit()
        
        # Publish to Kafka for async embedding generation
        producer.send(
            'document-uploads',
            key=f'doc_{doc_id}',
            value={
                'document_id': doc_id,
                'title': doc.title,
                'content': doc.content,
                'status': 'pending'
            }
        )
        producer.flush()
        
        return {
            "status": "accepted",
            "document_id": doc_id,
            "message": "Document queued for processing"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
```

#### Embedding Worker (Consumer)

```python
# worker.py
from kafka import KafkaConsumer
import json
import pymysql
import redis
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# Initialize
model = SentenceTransformer('all-MiniLM-L6-v2')
redis_client = redis.Redis(host='redis', port=6379, decode_responses=False)

def get_db():
    return pymysql.connect(
        host='mysql',
        user='raguser',
        password='ragpassword',
        database='rag_db'
    )

consumer = KafkaConsumer(
    'document-uploads',
    bootstrap_servers=['kafka:9093'],
    group_id='embedding-workers',
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

def process_document(message):
    data = message.value
    doc_id = data['document_id']
    content = data['content']
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Split into chunks
        chunks = content.split('. ')
        
        # Process each chunk
        for idx, chunk in enumerate(chunks):
            if chunk.strip():
                # Generate embedding
                embedding = model.encode(chunk)
                
                # Store in Redis
                redis_key = f"emb:doc{doc_id}:chunk{idx}"
                redis_client.set(redis_key, embedding.tobytes())
                
                # Store metadata
                cursor.execute(
                    """INSERT INTO embeddings 
                    (document_id, chunk_text, chunk_index, redis_key) 
                    VALUES (%s, %s, %s, %s)""",
                    (doc_id, chunk, idx, redis_key)
                )
        
        conn.commit()
        print(f"Processed document {doc_id} with {len(chunks)} chunks")
        
    except Exception as e:
        conn.rollback()
        print(f"Error processing document {doc_id}: {e}")
    finally:
        conn.close()

# Main loop
print("Starting embedding worker...")
for message in consumer:
    process_document(message)
```

### Use Case 2: Search Analytics

Track all search queries for analytics.

```python
# In search endpoint
@app.post("/search")
def search(query: Query):
    # ... existing search logic ...
    
    # Publish search event to Kafka
    producer.send(
        'search-analytics',
        value={
            'query': query.question,
            'results_count': len(top_results),
            'timestamp': datetime.now().isoformat()
        }
    )
    
    return {"query": query.question, "results": top_results}
```

### Use Case 3: Event Sourcing

Store all document events for audit trail.

```python
# Event types
EVENT_TYPES = {
    'DOCUMENT_CREATED': 'document-created',
    'DOCUMENT_UPDATED': 'document-updated',
    'DOCUMENT_DELETED': 'document-deleted',
    'EMBEDDING_GENERATED': 'embedding-generated'
}

def publish_event(event_type, data):
    producer.send(
        'document-events',
        key=event_type,
        value={
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
    )
```

---

## Use Cases for RAG + Kafka

### 1. **Async Document Processing**
- **Benefit**: Fast API responses, background processing
- **Implementation**: API publishes to Kafka, workers consume and process

### 2. **Search Analytics**
- **Benefit**: Track popular queries, improve search
- **Implementation**: All searches published to analytics topic

### 3. **Multi-Worker Processing**
- **Benefit**: Scale embedding generation horizontally
- **Implementation**: Multiple workers in same consumer group

### 4. **Event Sourcing**
- **Benefit**: Complete audit trail, replay capability
- **Implementation**: All state changes as events

### 5. **Real-time Notifications**
- **Benefit**: Notify users when processing completes
- **Implementation**: Worker publishes completion event, notification service consumes

### 6. **Data Pipeline**
- **Benefit**: Process documents through multiple stages
- **Implementation**: Chained topics (upload → chunk → embed → index)

### 7. **Backpressure Handling**
- **Benefit**: Handle traffic spikes gracefully
- **Implementation**: Kafka buffers messages, workers process at their pace

---

## Advanced Patterns

### Pattern 1: Request-Reply

**Use Case:** Wait for processing completion

```python
# Producer (API)
correlation_id = str(uuid.uuid4())
producer.send(
    'document-uploads',
    key=correlation_id,
    value={'document_id': doc_id, 'correlation_id': correlation_id}
)

# Consumer (Worker) - publishes reply
producer.send(
    'document-replies',
    key=correlation_id,
    value={'document_id': doc_id, 'status': 'completed', 'correlation_id': correlation_id}
)

# API polls or uses WebSocket for reply
```

### Pattern 2: Dead Letter Queue (DLQ)

**Use Case:** Handle failed messages

```python
def process_with_dlq(message):
    try:
        process_document(message)
    except Exception as e:
        # Send to DLQ
        producer.send(
            'document-uploads-dlq',
            value={
                'original_message': message.value,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        )
```

### Pattern 3: Exactly-Once Processing

```python
# Use idempotent producer
producer = KafkaProducer(
    bootstrap_servers=['kafka:9093'],
    enable_idempotence=True,
    acks='all',
    max_in_flight_requests_per_connection=1
)

# Track processed messages
processed_ids = set()

def process_document(message):
    doc_id = message.value['document_id']
    if doc_id in processed_ids:
        return  # Already processed
    
    # Process...
    processed_ids.add(doc_id)
```

### Pattern 4: Stream Processing with Kafka Streams

```python
from kafka import KafkaConsumer, KafkaProducer

# Simple stream processing example
consumer = KafkaConsumer('document-uploads', ...)
producer = KafkaProducer(...)

for message in consumer:
    data = message.value
    
    # Transform
    processed = {
        'document_id': data['document_id'],
        'word_count': len(data['content'].split()),
        'processed_at': datetime.now().isoformat()
    }
    
    # Send to next topic
    producer.send('document-metrics', value=processed)
```

---

## Performance & Optimization

### Producer Optimization

```python
producer = KafkaProducer(
    bootstrap_servers=['kafka:9093'],
    # Batch settings
    batch_size=16384,  # 16KB batches
    linger_ms=10,  # Wait 10ms to batch
    compression_type='snappy',  # Compress messages
    # Buffer settings
    buffer_memory=33554432,  # 32MB buffer
    max_request_size=1048576,  # 1MB max request
)
```

### Consumer Optimization

```python
consumer = KafkaConsumer(
    'document-uploads',
    bootstrap_servers=['kafka:9093'],
    # Fetch settings
    fetch_min_bytes=1,
    fetch_max_wait_ms=500,
    max_partition_fetch_bytes=1048576,  # 1MB per partition
    # Consumer settings
    max_poll_records=500,  # Process 500 at a time
    session_timeout_ms=30000,
    heartbeat_interval_ms=3000
)
```

### Partitioning Strategy

**Key-based partitioning for ordering:**
```python
# Same document_id always goes to same partition
producer.send('document-uploads', key=f'doc_{doc_id}', value=data)
```

**Round-robin for load balancing:**
```python
# No key = round-robin distribution
producer.send('document-uploads', value=data)
```

### Scaling Consumers

```
Topic: document-uploads (6 partitions)

1 Consumer:  Processes all 6 partitions
2 Consumers: Each processes 3 partitions
3 Consumers: Each processes 2 partitions
6 Consumers: Each processes 1 partition
7+ Consumers: Some idle (can't have more consumers than partitions)
```

**Rule:** Number of consumers ≤ Number of partitions

---

## Monitoring & Operations

### Key Metrics

1. **Producer Metrics:**
   - Messages sent per second
   - Bytes sent per second
   - Error rate
   - Latency

2. **Consumer Metrics:**
   - Messages consumed per second
   - Lag (messages behind)
   - Processing time
   - Error rate

3. **Broker Metrics:**
   - Disk usage
   - Network I/O
   - Request rate
   - Replication lag

### Monitoring Tools

1. **Kafka UI**: Web interface for topics, consumers, messages
2. **Prometheus + Grafana**: Metrics and dashboards
3. **Kafka Manager**: Cluster management
4. **Burrow**: Consumer lag monitoring

### Health Checks

```python
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

def check_kafka_health():
    try:
        producer = KafkaProducer(
            bootstrap_servers=['kafka:9093'],
            request_timeout_ms=5000
        )
        # Try to get metadata
        metadata = producer.list_topics(timeout=5)
        producer.close()
        return True
    except KafkaError:
        return False
```

---

## Troubleshooting

### Common Issues

#### 1. **Consumer Lag**

**Symptom:** Consumers falling behind

**Solutions:**
- Add more consumers
- Optimize processing logic
- Increase `max_poll_records`
- Use parallel processing

#### 2. **Message Loss**

**Symptom:** Messages not received

**Solutions:**
- Check `acks` setting (use 'all')
- Check replication factor
- Verify consumer group offset

#### 3. **Rebalancing Issues**

**Symptom:** Frequent rebalancing

**Solutions:**
- Increase `session_timeout_ms`
- Reduce processing time
- Check network connectivity

#### 4. **High Latency**

**Symptom:** Slow message delivery

**Solutions:**
- Increase batch size
- Tune `linger_ms`
- Check network bandwidth
- Use compression

---

## Best Practices

### 1. **Topic Naming**

✅ Good:
- `document-uploads`
- `search-analytics`
- `user-events`

❌ Bad:
- `topic1`
- `data`
- `test`

### 2. **Partitioning**

- Use keys for ordering requirements
- Use round-robin for load balancing
- Plan partitions for future scale (can't decrease)

### 3. **Error Handling**

```python
def safe_consume():
    try:
        for message in consumer:
            try:
                process_message(message)
            except ProcessingError as e:
                # Log and continue
                logger.error(f"Processing error: {e}")
                # Optionally send to DLQ
    except KafkaError as e:
        # Handle connection errors
        logger.error(f"Kafka error: {e}")
        # Implement retry logic
```

### 4. **Idempotency**

- Make consumers idempotent
- Track processed message IDs
- Handle duplicate messages gracefully

### 5. **Monitoring**

- Monitor consumer lag
- Track error rates
- Alert on high latency
- Monitor disk usage

### 6. **Security**

- Use SASL/SSL in production
- Implement ACLs (Access Control Lists)
- Encrypt sensitive data
- Use authentication

---

## Integration Checklist

### For RAG Application

- [ ] Add Kafka to docker-compose.yml
- [ ] Install kafka-python
- [ ] Create topics (document-uploads, search-analytics, etc.)
- [ ] Update API to publish events
- [ ] Create embedding worker consumer
- [ ] Implement error handling
- [ ] Add monitoring
- [ ] Test with multiple workers
- [ ] Set up DLQ for failed messages
- [ ] Document event schemas

---

## Next Steps

1. **Set up Kafka** in your docker-compose
2. **Create basic producer/consumer** examples
3. **Integrate async document processing**
4. **Add search analytics**
5. **Implement monitoring**
6. **Scale with multiple workers**
7. **Explore Kafka Streams** for advanced processing

---

## Resources

- [Kafka Official Documentation](https://kafka.apache.org/documentation/)
- [Confluent Kafka Python Client](https://github.com/confluentinc/confluent-kafka-python)
- [Kafka Python Client](https://github.com/dpkp/kafka-python)
- [Kafka: The Definitive Guide](https://www.confluent.io/resources/kafka-the-definitive-guide/)
- [Kafka UI](https://github.com/provectus/kafka-ui)

---

**Happy Streaming! 🚀**

