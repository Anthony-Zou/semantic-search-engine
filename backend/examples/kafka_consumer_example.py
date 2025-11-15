"""
Kafka Consumer Example

This script demonstrates how to consume messages from Kafka topics.
Run this to see messages being consumed in real-time.
"""
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import json
import signal
import sys

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n🛑 Shutting down consumer...")
    running = False

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

def consume_messages(topic, group_id='example-consumer-group'):
    """Consume messages from a Kafka topic"""
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=['localhost:9092'],  # Use localhost when running outside Docker
        group_id=group_id,
        auto_offset_reset='earliest',  # Start from beginning if no offset
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=1000,  # Timeout for polling
    )
    
    print(f"📡 Consuming messages from topic: {topic}")
    print(f"   Consumer group: {group_id}")
    print(f"   Press Ctrl+C to stop\n")
    
    try:
        for message in consumer:
            if not running:
                break
                
            print("=" * 60)
            print(f"📨 New Message Received")
            print(f"   Topic: {message.topic}")
            print(f"   Partition: {message.partition}")
            print(f"   Offset: {message.offset}")
            print(f"   Key: {message.key.decode('utf-8') if message.key else 'None'}")
            print(f"\n   Value:")
            print(f"   {json.dumps(message.value, indent=2)}")
            print()
            
            # Process the message here
            # process_message(message.value)
            
    except KeyboardInterrupt:
        print("\n🛑 Consumer interrupted")
    except KafkaError as e:
        print(f"❌ Kafka error: {e}")
    finally:
        consumer.close()
        print("✅ Consumer closed")

if __name__ == "__main__":
    print("🚀 Kafka Consumer Example")
    print("=" * 50)
    
    # Choose which topic to consume
    topic = input("\nEnter topic name (default: document-uploads): ").strip() or 'document-uploads'
    
    consume_messages(topic)

