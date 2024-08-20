# LLAMA 3.1 Terminal Chat

### Overview
This project provides a terminal-based application that allows users to interact with the LLAMA 3.1 model using a Groq API key. It supports markdown formatting for conversation responses and features robust memory management through Redis and local storage.

### Features
- LLAMA 3.1 Integration: Engage in conversations with the LLAMA 3.1 model through the terminal.
- Markdown Support: Responses are formatted using Markdown for enhanced readability.
- Persistent Memory:
    - Redis Integration: Data is stored and retrieved from a Redis database for persistent memory       across sessions.
    - Local Memory: If Redis is unavailable, local memory ensures conversational continuity for the current session.

### Setup
##### Prerequisites
 - Python 3.x
 - Redis (for persistent memory)
 - Groq API key

##### Installation
1) Clone the Repository:
```git clone <repository-url>```

2) Navigate to the Project Directory:
```cd <project-directory>```

3) Install Dependencies:
```pip install <dependencies>```

4) Create a .env File:
```touch .env```

Create a .env file in the project root directory and add your Groq API key and Redis connection details:
```GROQ_API_KEY=your_groq_api_key```
```REDIS_FLOW=/path/to/redis_db.py```
```CONFIG_PATH=/path/to/config/if/using```

5) Create config.json: 
```touch config.json```

Create a config.json in the project root directory and add your Redis Database information: 
```{ 
    "redis": { 
        "endpoint": <database_endpoint>, 
        "password": <database_password>
    }
}
```
6) Run the Application 
```python script.py```

### Usage
- Start a Conversation: Launch the application and start chatting with the LLAMA 3.1 model.
- Markdown Responses: Enjoy Markdown-formatted responses in the terminal.
- Automatic Data Storage: Data is saved automatically to Redis if available, otherwise, local memory is used.

### Troubleshooting
- Redis Connection Issues: Ensure Redis is running and accessible. Check the Redis URL in your .env file.
- API Key Errors: Verify your Groq API key is correctly configured in the .env file.

### License 
- This project is licensed under the MIT License 