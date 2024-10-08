# CONTAINS CODE FOR REDIS DATABASE OPERATIONS

import json
import os
import sys
import redis 
import time 
import secrets

# Library for rich markdown conversion
from rich.console import Console

# Load .env file
from dotenv import load_dotenv 
load_dotenv()

class RedisOperations:
    
    def __init__(self): 
        self.console = Console()
        self.redis_client = None
        self.session_key = ""

    def get_redis_client(self, conversation_history):
        if self.redis_client is None:
            config_path = os.getenv('CONFIG_PATH', 'config.json')
            with open(config_path, 'r') as file: 
                config = json.load(file)
            redis_endpoint = config['redis']['endpoint']
            redis_password = config['redis']['password']
            
            try:
                self.redis_client = redis.Redis(host=redis_endpoint, port=18656, password=redis_password)
                print("Connecting to Redis...")
            except Exception as err:
                self.console.print(f"[bold red]WARNING:[/bold red] Error connecting to Redis: {err}")
                sys.exit(1)
        self.create_session_list()
        self.load_conversation_history(conversation_history)
        return self.redis_client

    def create_session_list(self): 
        epoch_time = int(time.time()) # Store timestamp
        salt = secrets.token_hex(16)
        session_id = f"{epoch_time:x}{salt}"
        
        self.session_key = f"session:{session_id}"
    
    def add_key(self): 
        self.redis_client.lpush("Key_List", self.session_key)
        self.redis_client.ltrim("Key_List", 0, 99) # Only keep last 100 keys
        
    def flatten_list(self, nested_list):
        flat_list = []
        for item in nested_list:
            if isinstance(item, list):
                flat_list.extend(self.flatten_list(item))
            else:
                flat_list.append(item)
        return flat_list

    def process_data(self, data):
        processed_data = []
        for item in data:
            if isinstance(item, list):
                processed_data.extend(self.process_data(item)) # Recursively process items within the list
            elif isinstance(item, bytes):
                decoded_item = item.decode('utf-8') # Decode bytes to string
                json_data = json.loads(decoded_item) # Convert JSON string to Python object
                processed_data.append(json_data)
            else:
                processed_data.append(item) # Append item directly if it's already in the correct format

        flat_data = self.flatten_list(processed_data) # Flatten the processed data
        return flat_data

    def get_last_session_keys(self, num_values): 
        if(num_values != 3): 
            last_sessions = self.redis_client.lrange("Key_List", 0, -1) # Dumps all sessions
        else: 
            last_sessions = self.redis_client.lrange("Key_List", 0, num_values - 1)
        last_sessions = [item.decode('utf-8') for item in last_sessions]
        return last_sessions

    def get_last_session_values(self, keys): 
        values = []
        for key in keys: 
            list_values = self.redis_client.lrange(key, 0, -1)
            values.append(list_values)
        return values

    def load_conversation_history(self, conversation_history):
        try: 
            if self.redis_client: 
                data = []
                if((self.redis_client.execute_command('DBSIZE') - 1) >= 3):
                    try:
                        last_three_keys = self.get_last_session_keys(3)
                        last_three_vals = self.get_last_session_values(last_three_keys)
                        data = last_three_vals
                    except Exception as e: 
                        self.console.print(f"[bold red]WARNING:[/bold red] Error retrieving from Redis: {e}")
                else: 
                    try:  
                        all_keys = self.get_last_session_keys(0)
                        all_vals = self.get_last_session_values(all_keys)
                        data = all_vals
                    except Exception as e: 
                        self.console.print(f"[bold red]WARNING:[/bold red] Error retrieving from Redis: {e}")
                flat_data = self.process_data(data)
                if(flat_data):
                    conversation_history[:] = flat_data # Load data into conversation history (load in place
                    print("Loading Conversation History...")
                else: print("No Available History...")
        except Exception as e:
            self.console.print(f"[bold red]WARNING:[/bold red] Failed to load Redis data: No previously stored data will be available moving forward. \n {e}")
            
    def push_conversation_history(self, qa_segment):
        try:
            if self.redis_client:
                if qa_segment:
                    self.redis_client.rpush(self.session_key, json.dumps(qa_segment)) # Push as list
                    print("\nPushing to Redis...")
                else: 
                    print("Conversation Empty. Skipping Push...")
        except Exception as e:
            self.console.print(f"[bold red]WARNING:[/bold red] Failed to push to Redis: {e}", self.redis_client)

    def handle_exit(self, term_width):
        if self.redis_client:
            self.add_key()
            print("Closing Redis Connection...")
            try:
                self.redis_client.close()
            except Exception as e:
                self.console.print(f"[bold red]WARNING:[/bold red] Error during Redis client cleanup: {e}")
            finally:
                self.redis_client = None  # Ensure it's not referenced again
                print("Finished")
        print("=" * term_width)
        sys.exit(0)
        