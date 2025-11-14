# agent.py

import asyncio
import yaml
from core.loop import AgentLoop
from core.session import MultiMCP
from core.context import MemoryItem, AgentContext
import datetime
from pathlib import Path
import json
import re

def log(stage: str, msg: str):
    """Simple timestamped console logger."""
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")

async def main():
    print("🧠 Cortex-R Agent Ready")
    current_session = None

    with open("config/profiles.yaml", "r") as f:
        profile = yaml.safe_load(f)
        mcp_servers_list = profile.get("mcp_servers", [])
        # What does get do here? 
        # It retrieves the value associated with the key "mcp_servers" from the profile dictionary.
        mcp_servers = {server["id"]: server for server in mcp_servers_list}
        # Sample output of mcp_servers?
        # { "server1": {"id": "server1", "description": "This server handles data processing"}, "server2": {"id": "server2", "description": "This server manages user authentication"} }

    multi_mcp = MultiMCP(server_configs=list(mcp_servers.values()))
    # Initialize the MultiMCP with the list of server configurations extracted from the profile.
    await multi_mcp.initialize()

    try:
        while True: # When would this be false? -> This loop will continue indefinitely until it is explicitly broken out of, such as when the user types 'exit'.
            # Does control + C break this loop? -> Yes, pressing Control + C raises a KeyboardInterrupt exception, which is caught in the except block, allowing the program to exit gracefully.
            user_input = input("🧑 What do you want to solve today? (type 'exit' to close or 'new' to start afresh) → ")
            if user_input.lower() == 'exit':
                break
            if user_input.lower() == 'new':
                # Example of when this would be used? -> This would be used when the user wants to start a new session or conversation, effectively resetting any previous context or state.
                current_session = None # Why is None assigned here? -> Assigning None to current_session indicates that there is no active session, prompting the system to create a new session ID the next time an AgentContext is instantiated.
                continue

            while True: # When would this be false? -> This inner loop will continue until a final answer is obtained or further processing is no longer required.
                context = AgentContext(
                    user_input=user_input, # Example: "What is the capital of France?"
                    session_id=current_session, # Example: "2024/06/15/session-1712345678-abc123"
                    dispatcher=multi_mcp, # Passing the initialized MultiMCP dispatcher to the AgentContext.
                    mcp_server_descriptions=mcp_servers, # Passing MCP parameters to the AgentContext. Not just descriptions, right? -> Correct, it passes the entire server configuration, which may include more than just descriptions.
                )
                agent = AgentLoop(context) # What does agen contain? Example? -> The agent variable contains an instance of the AgentLoop class, which is initialized with the current AgentContext. This instance will manage the interaction loop for processing the user's input and generating responses.
                if not current_session: # If no current session exists, set it.
                    current_session = context.session_id # How is this session_id generated? -> The session_id is generated within the AgentContext constructor, typically based on the current date and time along with a unique identifier.

                result = await agent.run() # Run with the current context

                if isinstance(result, dict): # Check if this is a dict
                    answer = result["result"] 
                    if "FINAL_ANSWER:" in answer:
                        print(f"\n💡 Final Answer: {answer.split('FINAL_ANSWER:')[1].strip()}")
                        break
                    elif "FURTHER_PROCESSING_REQUIRED:" in answer:
                        user_input = answer.split("FURTHER_PROCESSING_REQUIRED:")[1].strip()
                        print(f"\n🔁 Further Processing Required: {user_input}")
                        continue  # 🧠 Re-run agent with updated input 
                        # How does this continue work here? -> The continue statement causes the inner while loop to skip the rest of its body and start the next iteration. This means that the agent will be re-run with the updated user_input that requires further processing.
                        # Does that mean a new session id is created? -> No, the session_id remains the same because it is stored in the context, which is preserved across iterations of the inner loop.
                        # So only if it breaks out of the inner loop and goes back to the outer loop, a new session id is created? -> Yes, a new session_id is created only when the user types 'new' in the outer loop, which resets current_session to None.
                    else:
                        print(f"\n💡 Final Answer (raw): {answer}") # Why is it called raw? 
                        # Because it doesn't follow the expected format of FINAL_ANSWER or FURTHER_PROCESSING_REQUIRED.
                        break
                else:
                    print(f"\n💡 Final Answer (unexpected): {result}")
                    # When would this happen? -> This would happen if the result returned by agent.run() is not a dictionary, which could occur due to an unexpected error or if the agent's logic produces a different type of output.
                    break
    except KeyboardInterrupt:
        print("\n👋 Received exit signal. Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())



# Find the ASCII values of characters in INDIA and then return sum of exponentials of those values.
# How much Anmol singh paid for his DLF apartment via Capbridge? 
# What do you know about Don Tapscott and Anthony Williams?
# What is the relationship between Gensol and Go-Auto?
# which course are we teaching on Canvas LMS? "H:\DownloadsH\How to use Canvas LMS.pdf"
# Summarize this page: https://theschoolof.ai/
# What is the log value of the amount that Anmol singh paid for his DLF apartment via Capbridge? 