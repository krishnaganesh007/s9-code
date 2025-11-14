# modules/action.py

from typing import Dict, Any, Union
from pydantic import BaseModel
import asyncio
import types
import json


# Optional logging fallback
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

class ToolCallResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Union[str, list, dict] # Why is there a union here? --> Any would allow literally anything (numbers, booleans, even objects). But here, the developer knows tools will only ever return structured data: strings, lists, or dictionaries.
    raw_response: Any

MAX_TOOL_CALLS_PER_PLAN = 5

async def run_python_sandbox(code: str, dispatcher: Any) -> str:
    print("[action] 🔍 Entered run_python_sandbox()")

    # Create a fresh module scope
    sandbox = types.ModuleType("sandbox")
    # What is types.ModuleType here for? -> It creates a new module object named "sandbox" which provides a separate namespace for executing the dynamically generated code. This helps to isolate the execution environment and avoid conflicts with other parts of the program.
    # Other places where we use types.ModuleType? -> It's commonly used in scenarios where dynamic code execution or module creation is needed, such as in plugin systems, testing frameworks, or sandboxed execution environments.
    # Real world analogy? -> It's like creating a new workspace or room where you can work on a project without disturbing others. Everything you do in that room stays there, and you can bring in only what you need from outside.
    # What is exec() doing here? -> The exec() function is used to execute the dynamically generated code within the context of the sandbox module. It compiles and runs the code, allowing the defined functions and variables to be accessible within that module's namespace.
    # Will there be local and global variable seperation here? -> Yes, the exec() function allows you to specify separate dictionaries for global and local variables. In this case, by passing sandbox.__dict__ as the global namespace, all variables and functions defined in the executed code will be stored in the sandbox module's dictionary.
    # Is this only used to run code or anything else? -> Primarily, exec() is used to run dynamically generated code. However, it can also be used for tasks like defining functions or classes on-the-fly, modifying existing code behavior, or creating interactive environments where users can input and execute code snippets.
    # Has this become popular only in recent years? -> The exec() function has been part of Python since its early versions. While its use has always been somewhat niche due to security and maintainability concerns, it has seen increased interest in recent years with the rise of dynamic programming, interactive computing environments (like Jupyter notebooks), and applications requiring runtime code generation.
    # Is it because of code agents? -> Yes, the rise of code agents and AI-driven programming tools has contributed to the increased interest in dynamic code execution. These applications often require the ability to generate and run code on-the-fly, making functions like exec() more relevant in modern programming contexts.
    # If a variable is defined inside sandbox can it not be accessed outside? -> Correct, variables defined inside the sandbox module will not be accessible outside of it unless explicitly exposed. This isolation helps prevent unintended interactions with other parts of the program.
    # How are guardrails implemented here? -> Guardrails can be implemented by restricting the available built-ins and modules within the sandbox environment, limiting resource usage (like CPU and memory), and monitoring the execution for potentially harmful operations. In this code, the limitation on tool calls is one such guardrail.

    try:
        # Patch MCP client with real dispatcher
        # What is a dispatcher here? -> The dispatcher is an object responsible for managing and routing tool calls to the appropriate MCP (Multi-Client Proxy) servers. It acts as an intermediary that handles communication between the sandboxed code and the external services or tools that the code may need to interact with.
        class SandboxMCP:
            def __init__(self, dispatcher):
                self.dispatcher = dispatcher
                self.call_count = 0

            async def call_tool(self, tool_name: str, input_dict: dict):
                self.call_count += 1
                if self.call_count > MAX_TOOL_CALLS_PER_PLAN:
                    raise RuntimeError(f"Exceeded max tool calls ({MAX_TOOL_CALLS_PER_PLAN}) in solve() plan.")
                # REAL tool call now
                result = await self.dispatcher.call_tool(tool_name, input_dict)
                return result

        sandbox.mcp = SandboxMCP(dispatcher)
        # Is this a definition or an instantiation? -> This line is an instantiation. It creates a new instance of the SandboxMCP class, passing the dispatcher object to its constructor, and assigns it to the mcp attribute of the sandbox module.
        # So everything in dispatcher is now accessible via sandbox.mcp? -> Not everything, but the methods and attributes defined in the SandboxMCP class are accessible via sandbox.mcp. The dispatcher object is encapsulated within the SandboxMCP instance, allowing controlled access to its functionality through the methods provided by SandboxMCP.
        # What methods are available in sandbox.mcp? -> The only method available in sandbox.mcp is call_tool, which allows the sandboxed code to make tool calls while enforcing the maximum call limit.

        # Preload safe built-ins into the sandbox
        import json, re 
        sandbox.__dict__["json"] = json 
        sandbox.__dict__["re"] = re

        # Execute solve fn dynamically
        exec(compile(code, "<solve_plan>", "exec"), sandbox.__dict__)
        # Give an example of the code generated?
        # Example of code: 
        # async def solve():
        #    #     response = await mcp.call_tool("data_analysis_tool", {"data": "sample data"})
        # What would sandbox.__dict__ contain here? -> sandbox.__dict__ would contain all the variables, functions, and classes defined in the dynamically executed code. This includes the solve() function that is expected to be defined in the provided code string.

        solve_fn = sandbox.__dict__.get("solve")
        # What does .get do here? -- would raise KeyError if missing. 
        # .get lets you avoid KeyError and get None instead
        

        if solve_fn is None:
            raise ValueError("No solve() function found in plan.")
        # Does this break the loop?

        if asyncio.iscoroutinefunction(solve_fn): 
        # Why asyncio? - 
        # What does iscoroutinefunction do?
        # It checks if the provided function is a coroutine function, meaning it is defined with async def and returns a coroutine object when called. This is important for determining whether to await the function call.
            result = await solve_fn()
        else:
            result = solve_fn()
            # Then even bother writing await before?

        # Clean result formatting
        if isinstance(result, dict) and "result" in result:
            return f"{result['result']}"
        elif isinstance(result, dict):
            return f"{json.dumps(result)}"
        elif isinstance(result, list):
            return f"{' '.join(str(r) for r in result)}"
        else:
            return f"{result}"






    except Exception as e:
        log("sandbox", f"⚠️ Execution error: {e}")
        return f"[sandbox error: {str(e)}]"
