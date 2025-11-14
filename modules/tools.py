# modules/tools.py

from typing import List, Dict, Optional, Any
import re

# Currently used in perception.py
def extract_json_block(text: str) -> str:
    """
    Extracts a JSON code block from a given text string.

    This function searches for a JSON block enclosed within triple backticks ("```json\n(.*?)```").
    If found, it returns the contents of that block as a stripped string.
    If no such block exists, it returns the entire input text stripped of leading and trailing whitespace.

    Args:
        text (str): The input text that may contain a JSON code block.

    Returns:
        str: The extracted JSON block content if found, otherwise the stripped input text.
    """
    match = re.search(r"```json\n(.*?)```", text, re.DOTALL) # What does re.DOTALL do here?
    # re.DOTALL makes the '.' special character match any character at all, including a newline; without it, '.' will match anything except a newline.
    if match: 
        return match.group(1).strip() # What are we checking for here?
    # If a JSON block is found, return its content stripped of whitespace.
    return text.strip()
    # Example usage:
    # input_text = "Here is some text.\n```json\n{\"key\": \"value\"}\n```\nMore text."
    # Output: '{"key": "value"}'


# 
def summarize_tools(tools: List[Any]) -> str:
    """
    Generate a string summary of tools for LLM prompt injection.
    Format: "- tool_name: description"
    """
    return "\n".join(
        f"- {tool.name}: {getattr(tool, 'description', 'No description provided.')}"
        for tool in tools
    )
    # Example output:
    # - search_documents: A tool to search through documents.
    # - calculate_sum: A tool to calculate the sum of numbers.
    # - fetch_data: A tool to fetch data from an API.

# Currently not used
def filter_tools_by_hint(tools: List[Any], hint: Optional[str] = None) -> List[Any]:
    """
    If tool_hint is provided (e.g., 'search_documents'),
    try to match it exactly or fuzzily with available tool names.
    """
    if not hint:
        return tools

    hint_lower = hint.lower()
    filtered = [tool for tool in tools if hint_lower in tool.name.lower()]
    return filtered if filtered else tools

# Currently not used
def get_tool_map(tools: List[Any]) -> Dict[str, Any]:
    """
    Return a dict of tool_name → tool object for fast lookup
    """
    return {tool.name: tool for tool in tools}

# Not used currently
def tool_expects_input(self, tool_name: str) -> bool:
    tool = next((t for t in self.tools if t.name == tool_name), None)
    if not tool or not hasattr(tool, 'parameters') or not isinstance(tool.parameters, dict):
        return False
    # If the top-level parameter is just 'input', we assume wrapping is required
    return list(tool.parameters.keys()) == ['input']

# Used wherever prompts are loaded - perception.py, decision.py, etc.
def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
