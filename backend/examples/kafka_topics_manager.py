"""
Kafka Topics Manager

Utility script to create, list, and manage Kafka topics.
"""
from kafka.admin import KafkaAdminClient, NewTopic, ConfigResource
from kafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError
import sys

def create_admin_client():
    """Create Kafka admin client"""
    return KafkaAdminClient(
        bootstrap_servers=['localhost:9092'],  # Use localhost when running outside Docker
        client_id='topics-manager'
    )

def list_topics():
    """List all topics"""
    admin_client = create_admin_client()
    topics = admin_client.list_topics()
    print(f"\n📋 Available Topics ({len(topics)}):")
    print("-" * 60)
    for topic in sorted(topics):
        print(f"  • {topic}")
    admin_client.close()

def create_topic(name, partitions=3, replication_factor=1):
    """Create a new topic"""
    admin_client = create_admin_client()
    
    topic = NewTopic(
        name=name,
        num_partitions=partitions,
        replication_factor=replication_factor
    )
    
    try:
        admin_client.create_topics([topic])
        print(f"✅ Topic '{name}' created successfully!")
        print(f"   Partitions: {partitions}")
        print(f"   Replication factor: {replication_factor}")
    except TopicAlreadyExistsError:
        print(f"⚠️  Topic '{name}' already exists")
    except Exception as e:
        print(f"❌ Error creating topic: {e}")
    finally:
        admin_client.close()

def delete_topic(name):
    """Delete a topic"""
    admin_client = create_admin_client()
    
    try:
        admin_client.delete_topics([name])
        print(f"✅ Topic '{name}' deleted successfully!")
    except UnknownTopicOrPartitionError:
        print(f"⚠️  Topic '{name}' does not exist")
    except Exception as e:
        print(f"❌ Error deleting topic: {e}")
    finally:
        admin_client.close()

def describe_topic(name):
    """Describe a topic"""
    admin_client = create_admin_client()
    
    try:
        metadata = admin_client.describe_topics([name])
        if name in metadata:
            topic_metadata = metadata[name]
            print(f"\n📊 Topic: {name}")
            print("-" * 60)
            print(f"  Partitions: {len(topic_metadata.partitions)}")
            for partition_id, partition in topic_metadata.partitions.items():
                print(f"    Partition {partition_id}:")
                print(f"      Leader: {partition.leader}")
                print(f"      Replicas: {partition.replicas}")
        else:
            print(f"⚠️  Topic '{name}' not found")
    except Exception as e:
        print(f"❌ Error describing topic: {e}")
    finally:
        admin_client.close()

if __name__ == "__main__":
    print("🚀 Kafka Topics Manager")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python kafka_topics_manager.py list")
        print("  python kafka_topics_manager.py create <topic_name> [partitions] [replication_factor]")
        print("  python kafka_topics_manager.py delete <topic_name>")
        print("  python kafka_topics_manager.py describe <topic_name>")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_topics()
    elif command == 'create':
        if len(sys.argv) < 3:
            print("❌ Error: Topic name required")
            sys.exit(1)
        topic_name = sys.argv[2]
        partitions = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        replication = int(sys.argv[4]) if len(sys.argv) > 4 else 1
        create_topic(topic_name, partitions, replication)
    elif command == 'delete':
        if len(sys.argv) < 3:
            print("❌ Error: Topic name required")
            sys.exit(1)
        delete_topic(sys.argv[2])
    elif command == 'describe':
        if len(sys.argv) < 3:
            print("❌ Error: Topic name required")
            sys.exit(1)
        describe_topic(sys.argv[2])
    else:
        print(f"❌ Unknown command: {command}")

