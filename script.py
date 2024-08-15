# Tells OS to run as python executible 
#!/usr/bin/env python3
import os

# Import Redis Database info from config.json
import json
import redis

# Figure it out 
import signal
import sys

# Library for terminal width to calculate separation barrier
import shutil

# Library for rich markdown conversion
from rich.console import Console
from rich.markdown import Markdown

# Library for Groq
from groq import Groq

# Initialize console for markdown
console = Console()

# Initialize conversation history list 
conversation_history = []

# Initialize counter for prompt message
prompt_counter = 0

# Global redis client 
redis_client = None

def get_api_key(): 
    API_KEY = os.getenv('GROQ_API_KEY')
    return API_KEY

def get_redis_client():
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
            print(f"Error connecting to Redis: {err}")
            sys.exit(1)
    # Load conversation history after successful connection to database
    load_conversation_history()
    return redis_client

def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list

def load_conversation_history(): 
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
        print(f"Failed to load conversation history: {e}")
        
def push_conversation_history():
    try:
        if redis_client:
            if conversation_history:
                # Push as list
                redis_client.rpush("conversation_history_list", json.dumps(conversation_history))
                print("Pushing to Redis...")
            else: 
                print("Conversation Empty. Skipping Push...")
    except Exception as e:
        print(f"Failed to push to Redis: {e}", redis_client)

def handle_exit(signal, frame):
    global redis_client
    if redis_client:
        print("Closing Redis Connection...")
        try:
            push_conversation_history()
            redis_client.close()
        except Exception as e:
            print(f"Error during Redis client cleanup: {e}")
        finally:
            redis_client = None  # Ensure it's not referenced again
            print("Finished")
    print("=" * getTermWidth())
    sys.exit(0)

def getTermWidth(): 
    term_width = shutil.get_terminal_size().columns
    return term_width

def prompt(prompt_counter): 
    print("=" * getTermWidth())
    if(prompt_counter < 1): 
        #print("=" * getTermWidth())
        user_input = input("What would you like help with today?\n > ")
    else: 
        user_input = input("\n > ")
    
    return user_input


def conversation(prompt_counter): 
    API_KEY = get_api_key()
    client = Groq(api_key=API_KEY)

    # Append the user's input to the converstation history
    conversation_history.append({ 
        "role": "user", 
        "content": prompt(prompt_counter)
        })

    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=conversation_history,
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    
    print("\n")
    
    response = ""
    for chunk in completion:
        response_chunk = chunk.choices[0].delta.content or ""
        response += response_chunk
    markdown = Markdown(response)
    console.print(markdown, end="")
    
    conversation_history.append({ 
        "role": "user", 
        "content": response
        })
    
if __name__ == "__main__":
    #get_redis_client() # Comment this out if you do not with to use Redis AT ALL (No connection, loaded history, or pushed data)
    try: 
        while True:
            conversation(prompt_counter)
            prompt_counter += 1
    except KeyboardInterrupt: 
        print("\nGoodbye!")
        print("=" * getTermWidth())
        handle_exit(signal.SIGINT, None)
    