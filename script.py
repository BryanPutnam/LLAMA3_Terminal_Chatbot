# Tells OS to run as python executible 

#!/usr/bin/env python3

# Library for rich markdown conversion
from rich.console import Console
from rich.markdown import Markdown
# Library for terminal width to calculate separation barrier
import shutil
# Library for Groq
from groq import Groq
console = Console()

# Initialize conversation history list 
conversation_history = []
prompt_counter = 0

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
        #print(response_chunk, end="") #(ORIGINAL CODE NO MARKDOWN SUPPORT)
        response += response_chunk
        # NEW MARKDOWN CODE
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
            conversation(prompt_counter)
            prompt_counter += 1
    except KeyboardInterrupt: 
        print("\nGoodbye!")
        print("=" * getTermWidth())
    