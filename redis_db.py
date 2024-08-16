# CONTAINS CODE FOR REDIS DATABASE OPERATIONS

import json
import os
import sys
import redis 

# Library for rich markdown conversion
from rich.console import Console
from rich.markdown import Markdown

console = Console()

# Global redis client 
redis_client = None

def get_redis_client(conversation_history):
    global redis_client
    if redis_client is None:
        config_path = os.getenv('CONFIG_PATH', 'config.json')
        with open(config_path, 'r') as file: 
            config = json.load(file)
        redis_endpoint = config['redis']['endpoint']
        redis_password = config['redis']['password']
        
        try:
            redis_client = redis.Redis(host=redis_endpoint, port=18656, password=redis_password)
            print("Connecting to Redis...")
        except Exception as err:
            console.print(f"[bold red]WARNING:[/bold red] Error connecting to Redis: {err}")
            sys.exit(1)
    # Load conversation history after successful connection to database
    load_conversation_history(conversation_history)
    return redis_client

def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list

def load_conversation_history(conversation_history): ## ADDED PARAM
    global redis_client
    try: 
        if redis_client: 
            # Retrieve all elements from the Redis list 
            data = redis_client.lrange("conversation_history_list", 0, -1)
            # Load data into conversation history (load in place)
            flat_data = flatten_list([json.loads(item.decode('utf-8')) for item in data if item])
            if(flat_data != []):
                conversation_history[:] = flat_data
                print("Loading Conversation History...")
            else: print("No Available History...")
    except Exception as e:
        console.print(f"[bold red]WARNING:[/bold red] Failed to load Redis data: No previously stored data will be available moving forward. \n {e}")
        
def push_conversation_history(conversation_history): ## ADDED PARAM
    try:
        if redis_client:
            if conversation_history:
                # Push as list
                redis_client.rpush("conversation_history_list", json.dumps(conversation_history))
                print("Pushing to Redis...")
            else: 
                print("Conversation Empty. Skipping Push...")
    except Exception as e:
        console.print(f"[bold red]WARNING:[/bold red] Failed to push to Redis: {e}", redis_client)

def handle_exit(signal, frame, conversation_history, term_width):
    global redis_client
    if redis_client:
        print("Closing Redis Connection...")
        try:
            push_conversation_history(conversation_history)
            redis_client.close()
        except Exception as e:
            console.print(f"[bold red]WARNING:[/bold red] Error during Redis client cleanup: {e}")
        finally:
            redis_client = None  # Ensure it's not referenced again
            print("Finished")
    print("=" * term_width)
    sys.exit(0)