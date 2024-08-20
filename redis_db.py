# CONTAINS CODE FOR REDIS DATABASE OPERATIONS

import json
import os
import sys
import redis 
import time 
import secrets

# Library for rich markdown conversion
from rich.console import Console
from rich.markdown import Markdown

console = Console()

# Global redis client 
redis_client = None

list_key = ""

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

def create_session_list(): 
    epoch_time = int(time.time()) # Store timestamp
    salt = secrets.token_hex(16)
    session_id = f"{epoch_time:x}{salt}"
    
    list_key = f"session:{session_id}"
    return list_key 
    
def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list

def process_data(data):
    processed_data = []
    for item in data:
        if isinstance(item, list):
            processed_data.extend(process_data(item)) # Recursively process items within the list
        elif isinstance(item, bytes):
            decoded_item = item.decode('utf-8') # Decode bytes to string
            json_data = json.loads(decoded_item) # Convert JSON string to Python object
            processed_data.append(json_data)
        else:
            processed_data.append(item) # Append item directly if it's already in the correct format

    flat_data = flatten_list(processed_data) # Flatten the processed data
    return flat_data

def get_last_session_keys(redis_client, num_values): 
    if(num_values != 3): 
        last_sessions = redis_client.lrange("Key_List", 0, -1) # Dumps all sessions
    else: 
        last_sessions = redis_client.lrange("Key_List", 0, num_values - 1)
    last_sessions = [item.decode('utf-8') for item in last_sessions]
    return last_sessions

def get_last_session_values(redis_client, keys): 
    values = []
    for key in keys: 
        list_values = redis_client.lrange(key, 0, -1)
        values.append(list_values)
    return values

def add_key(session_key): 
    global redis_client
    redis_client.lpush("Key_List", session_key)
    redis_client.ltrim("Key_List", 0, 99) # Only keep last 100 keys

def load_conversation_history(conversation_history):
    global redis_client # YOU MIGHT BE ABLE TO GET RID OF THIS??? (PASS AS PARAM)
    try: 
        if redis_client: 
            data = [] # Initialize 
            # Retrieve last 3 elements from the Redis list 
            if((redis_client.execute_command('DBSIZE') - 1) >= 3):
                try:
                    last_three_keys = get_last_session_keys(redis_client, 3)
                    last_three_vals = get_last_session_values(redis_client, last_three_keys)
                    data = last_three_vals
                except Exception as e: 
                    console.print(f"[bold red]WARNING:[/bold red] Error retrieving from Redis: {e}")
            else: 
                try:  
                    all_keys = get_last_session_keys(redis_client, 0)
                    all_vals = get_last_session_values(redis_client, all_keys)
                    data = all_vals
                except Exception as e: 
                    console.print(f"[bold red]WARNING:[/bold red] Error retrieving from Redis: {e}")
            # Load data into conversation history (load in place)
            flat_data = process_data(data)
            if(flat_data):
                conversation_history[:] = flat_data
                print("Loading Conversation History...")
            else: print("No Available History...")
    except Exception as e:
        console.print(f"[bold red]WARNING:[/bold red] Failed to load Redis data: No previously stored data will be available moving forward. \n {e}")
        
def push_conversation_history(qa_segment, list_key):
    try:
        if redis_client:
            if qa_segment:
                redis_client.rpush(list_key, json.dumps(qa_segment)) # Push as list
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
            redis_client.close()
        except Exception as e:
            console.print(f"[bold red]WARNING:[/bold red] Error during Redis client cleanup: {e}")
        finally:
            redis_client = None  # Ensure it's not referenced again
            print("Finished")
    print("=" * term_width)
    sys.exit(0)
    
    
    
    ########
    # YOU NEED TO MAKE SURE THAT THE SESSION KEY IS NOT PUSHED INTO THE KEY_LIST LIST IF DATA 1) FAILS TO PUSH 
    # TO REDIS, OR 2) FORCEFULLY DOES NOT PUSH BECAUSE OF EMPTY QA_SEGMENT