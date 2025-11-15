"""
Kafka Producer Example

This script demonstrates how to produce messages to Kafka topics.
Run this to send test messages that can be consumed by the worker.
"""
from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import time

# Create producer
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],  # Use localhost when running outside Docker
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None,
    acks='all',  # Wait for all replicas to acknowledge
    retries=3,
)

def send_message(topic, key, value):
    """Send a message to Kafka"""
    try:
        future = producer.send(topic, key=key, value=value)
        # Wait for the message to be sent
        record_metadata = future.get(timeout=10)
        print(f"✅ Message sent successfully!")
        print(f"   Topic: {record_metadata.topic}")
        print(f"   Partition: {record_metadata.partition}")
        print(f"   Offset: {record_metadata.offset}")
        return True
    except KafkaError as e:
        print(f"❌ Error sending message: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Kafka Producer Example")
    print("=" * 50)
    
    # Example 1: Send a document upload message
    print("\n1. Sending document upload message...")
    document_message = {
        'document_id': 999,
        'title': 'Test Document from Producer',
        'content': 'This is a test document. It has multiple sentences. Each sentence will become a chunk. The embedding worker will process this.',
        'status': 'pending',
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%S')
    }
    send_message('document-uploads', 'doc_999', document_message)
    
    # Example 2: Send search analytics
    print("\n2. Sending search analytics message...")
    search_message = {
        'query': 'What is Python?',
        'results_count': 3,
        'top_similarity': 0.85,
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
    }
    send_message('search-analytics', None, search_message)
    
    # Example 3: Send multiple messages
    print("\n3. Sending multiple messages...")
    for i in range(3):
        message = {
            'document_id': 1000 + i,
            'title': f'Document {i+1}',
            'content': f'This is document number {i+1}. It contains some content.',
            'status': 'pending',
            'created_at': time.strftime('%Y-%m-%dT%H:%M:%S')
        }
        send_message('document-uploads', f'doc_{1000+i}', message)
        time.sleep(0.5)  # Small delay between messages
    
    # Flush to ensure all messages are sent
    print("\n4. Flushing producer...")
    producer.flush()
    print("✅ All messages sent!")
    
    producer.close()
    print("\n✨ Producer example completed!")

