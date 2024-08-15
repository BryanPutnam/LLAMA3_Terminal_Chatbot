# Tells OS to run as python executible 
#!/usr/bin/env python3

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
console = Console()

# Initialize conversation history list 
conversation_history = []
prompt_counter = 0

# Global redis client 
redis_client = None

def get_redis_client():
    global redis_client
    if redis_client is None:
        config = json.load(open('config.json'))
        redis_endpoint = config['redis']['endpoint']
        redis_password = config['redis']['password']
        
        try:
            redis_client = redis.Redis(host=redis_endpoint, port=18656, password=redis_password)
            print("Connecting to Redis...")
        except Exception as err:
            print(f"Error connecting to Redis: {err}")
            sys.exit(1)
    return redis_client

# def load_conversation_history(): 
#     # code here  
        
def push_conversation_history():
    try:
        if redis_client:
            # Push as list
            redis_client.rpush("conversation_history_list", json.dumps(conversation_history))
            print("Pushing to Redis...")
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
    # BELOW IS NEW LINE 
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
    client = Groq()

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
    # Handle markdown response
    markdown = Markdown(response)
    console.print(markdown, end="")
    
    conversation_history.append({ 
        "role": "user", 
        "content": response
        })
    
    prompt_counter = 2
    
if __name__ == "__main__":
    try: 
        while True:
            get_redis_client()
            #load_conversation_history()
            conversation(prompt_counter) # Will possibly need to add conversation_history as a param here once load_conversation_history() is set up. 
            prompt_counter += 1
    except KeyboardInterrupt: 
        print("\nGoodbye!")
        print("=" * getTermWidth())
        handle_exit(signal.SIGINT, None)
    