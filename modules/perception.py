# modules/perception.py

from typing import List, Optional
from pydantic import BaseModel
from modules.model_manager import ModelManager
from modules.tools import load_prompt, extract_json_block
from core.context import AgentContext

import json


# Optional logging fallback
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

model = ModelManager() # Does this call instantiate a model manager object? -> Yes, it creates an instance of the ModelManager class.
# Why not call modelmanager.initialize()? -> It might be that the initialization is handled within the ModelManager's constructor (__init__ method), so calling ModelManager() is sufficient to set it up.
# Got it. So model is now an instance of ModelManager that we can use to generate text.


prompt_path = "prompts/perception_prompt.txt"

class PerceptionResult(BaseModel): 
    intent: str
    entities: List[str] = []
    tool_hint: Optional[str] = None
    tags: List[str] = []
    selected_servers: List[str] = []  # 🆕 NEW field


# Overall in the function below,
# 1. We prepare a list of MCP servers with their descriptions.
# 2. We load a prompt template and format it with the server list and user input.
# 3. We use the model to generate text based on the prompt.
# 4. We parse the generated text to extract perception details into a PerceptionResult object.
# 5. If parsing fails, we log an error and return a fallback PerceptionResult selecting all servers.

async def extract_perception(user_input: str, mcp_server_descriptions: dict) -> PerceptionResult:
    """
    Extracts perception details and selects relevant MCP servers based on the user query.
    """

    server_list = []
    for server_id, server_info in mcp_server_descriptions.items():
        description = server_info.get("description", "No description available")
        server_list.append(f"- {server_id}: {description}") # How does the output look like here? -> The output will be a list of strings, each string formatted as "- server_id: description". For example, if there is a server with ID "server1" and description "This server handles data processing", the corresponding string in the list would be "- server1: This server handles data processing".

    servers_text = "\n".join(server_list)
    # Why not directly use server_list? -> Joining the list into a single string with newline characters makes it easier to include in the prompt template, as it will appear as a formatted list when the prompt is generated.
    # Ah! So server_list is a list of strings, and servers_text is a single string with each server on a new line.


    prompt_template = load_prompt(prompt_path)
    

    prompt = prompt_template.format(
        servers_text=servers_text, #example: "- server1: Description of server 1\n- server2: Description of server 2"
        user_input=user_input #Example: "I need to analyze customer feedback data and generate a report."
    )
    

    try:
        raw = await model.generate_text(prompt)
        raw = raw.strip() # Why is strip() used here? -> The strip() method is used to remove any leading or trailing whitespace characters (like spaces, tabs, or newlines) from the generated text. This ensures that the output is clean and doesn't have any unnecessary whitespace that could interfere with parsing or further processing.
        log("perception", f"Raw output: {raw}")

        # Try parsing into PerceptionResult
        json_block = extract_json_block(raw) # What does extract_json_block do? --> It extracts a JSON code block from the given text. If the text contains a JSON block enclosed within triple backticks (```json ... ```), it returns the content of that block. If no such block exists, it returns the entire input text stripped of leading and trailing whitespace.
        # In this case the expected output is a JSON block containing fields like intent, entities, tool_hint, tags, and selected_servers.
        # Example of the output: '{"intent": "analyze_data", "entities": ["customer feedback"], "tool_hint": "data_analysis_tool", "tags": ["analysis", "report"], "selected_servers": ["server1", "server2"]}'
        result = json.loads(json_block) # What does json.loads do?
        # json.loads takes a JSON-formatted string and converts it into a corresponding Python dictionary (or other data structures like lists, depending on the JSON content).

        # If selected_servers missing, fallback
        if "selected_servers" not in result: # Then select all servers
            result["selected_servers"] = list(mcp_server_descriptions.keys())
        log("perception", f"Parsed result: {result}")
        print("result", result) # Why not log here? -> Using print here is likely for debugging purposes to quickly see the result in the console. It could be changed to log for consistency with the rest of the logging in the function.

        return PerceptionResult(**result) # Why is there a ** here? --> Basically it unpacks the dictionary so that each key-value pair is passed as a separate keyword argument to the PerceptionResult constructor.

    except Exception as e: 
        # What kind of errors could happen here? --> Several types of errors could occur here, including:
        # JSONDecodeError if the generated text is not valid JSON.
        # KeyError if expected keys are missing from the parsed result.
        # TypeError if the structure of the parsed result doesn't match what PerceptionResult expects.
        # Any other unexpected exceptions during text generation or processing.
        
        log("perception", f"⚠️ Perception failed: {e}")
        # Fallback: select all servers
        return PerceptionResult(
            intent="unknown",
            entities=[],
            tool_hint=None,
            tags=[],
            selected_servers=list(mcp_server_descriptions.keys())
        )
        # Will the process stop here? --> No, the process will not stop here. The exception is caught, logged, and a fallback PerceptionResult is returned, allowing the program to continue running.


# In this wrapper function,
# 1. We accept an AgentContext and optional user input.
# 2. We call extract_perception with either the provided user input or the one from the context.
# AgentContext contains: mcp_server_descriptions and user_input among other things.
async def run_perception(context: AgentContext, user_input: Optional[str] = None):

    """
    Clean wrapper to call perception from context.
    """
    return await extract_perception(
        user_input = user_input or context.user_input, # Is or a fall back option? --> Yes, it acts as a fallback. If user_input is provided (not None), it will be used; otherwise, context.user_input will be used.
        mcp_server_descriptions=context.mcp_server_descriptions
    )

