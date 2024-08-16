# Tells OS to run as python executible 
#!/usr/bin/env python3
import os
import sys

# Figure it out 
import signal

# Library for terminal width to calculate separation barrier
import shutil

# Library for rich markdown conversion
from rich.console import Console
from rich.markdown import Markdown

# Library for Groq
from groq import Groq

# Import functions from REDIS_FLOW (redis_db.py)
redis_flow_path = os.environ.get('REDIS_FLOW')
sys.path.insert(0, os.path.dirname(redis_flow_path))
from redis_db import get_redis_client, handle_exit

# Initialize console for markdown
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
        #print("=" * getTermWidth())
        user_input = input("What would you like help with today?\n > ")
    else: 
        user_input = input("\n > ")
    
    return user_input


def conversation(prompt_counter): 
    API_KEY = get_api_key()
    
    try:
        client = Groq(api_key=API_KEY)
    except Exception as e: 
        console.print(f"[bold red]WARNING:[/bold red] Failed to connect to Groq. Please check your API KEY and/or Network Connnection") 

    # Append the user's input to the converstation history
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
    
        conversation_history.append({ 
            "role": "user", 
            "content": response
            })
    except Exception as e: 
        console.print(f"[bold red]WARNING:[/bold red] Unable to Complete Request: Check Groq Server Status")
        sys.exit(0)
    
if __name__ == "__main__":
    get_redis_client(conversation_history) # Comment this out if you do not with to use Redis AT ALL (No connection, loaded history, or pushed data)
    try: 
        while True:
            conversation(prompt_counter)
            prompt_counter += 1
    except KeyboardInterrupt: 
        print("\nGoodbye!")
        print("=" * getTermWidth())
        handle_exit(signal.SIGINT, None, conversation_history, term_width=getTermWidth())
    