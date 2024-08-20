# Tells OS to run as python executible 
#!/usr/bin/env python3
import os
import sys

# Library for terminal width to calculate separation barrier
import shutil

# Library for rich markdown conversion
from rich.console import Console
from rich.markdown import Markdown

# Load .env file
from dotenv import load_dotenv 
load_dotenv()

# Library for Groq
from groq import Groq

# Import functions from REDIS_FLOW (redis_db.py)
redis_flow_path = os.environ.get('REDIS_FLOW')
sys.path.insert(0, os.path.dirname(redis_flow_path))
from redis_db import RedisOperations

# Initialize instance of RedisOperations
rdb = RedisOperations()

# Initialize instance of Markdown
console = Console()

# Initialize conversation history list 
conversation_history = []

# Initialize counter for prompt message
prompt_counter = 0

def get_api_key(): 
    API_KEY = os.getenv('GROQ_API_KEY')
    return API_KEY

def getTermWidth(): 
    term_width = shutil.get_terminal_size().columns
    return term_width

def prompt(prompt_counter): 
    print("=" * getTermWidth())
    if(prompt_counter < 1): 
        user_input = input("What would you like help with today?\n > ")
    else: 
        user_input = input("\n > ")
    
    return user_input

def append_list(list, response):
    list.append({ 
            "role": "user", 
            "content": response
            })

def conversation(prompt_counter): 
    API_KEY = get_api_key()
    
    try:
        client = Groq(api_key=API_KEY)
    except Exception as e: 
        console.print(f"[bold red]WARNING:[/bold red] Failed to connect to Groq. Please check your API KEY and/or Network Connnection") 

    conversation_history.append({
        "role": "user", 
        "content": prompt(prompt_counter)
        })
    
    try:
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

        append_list(conversation_history, response)
        qa_segment = [] # Reset qa_segment every question/answer iteration and then store info to be pushed.
        append_list(qa_segment, response)
        
        rdb.push_conversation_history(qa_segment) # Push qa_segment to Redis
        
    except Exception as e: 
        console.print(f"[bold red]WARNING:[/bold red] Unable to Complete Request: Check Groq Server Status: {e}")
        sys.exit(0)
    
if __name__ == "__main__":
    rdb.get_redis_client(conversation_history) # Comment this out if you do not wish to use Redis AT ALL (No connection, loaded history, or pushed data)
    try: 
        while True:
            conversation(prompt_counter)
            prompt_counter += 1
    except KeyboardInterrupt: 
        print("\nGoodbye!")
        print("=" * getTermWidth())
        rdb.handle_exit(term_width=getTermWidth())
