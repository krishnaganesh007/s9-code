
# Cortex-R Agent Framework
An extensible, multi-tool, multi-step *agentic reasoning framework* with MCP server orchestration, LLM-based perception, planning, sandboxed action execution, and heuristic safeguards.

## 📌 Overview
Cortex-R is a modular AI agent framework designed for:
- Multi-step reasoning
- Tool-augmented problem solving
- Dynamic plan generation
- Sandboxed code execution
- Cross-server MCP tool orchestration
- Memory tracking
- Heuristic evaluation (query + result safety layers)

It enables safe, auditable execution of LLM-generated plans (`solve()` functions) while interacting with multiple structured tool servers such as:
- Web search
- Document retrieval
- Math solvers
- Local/Custom MCP tools

## 📑 Table of Contents
- Overview
- Architecture
- Features
- Installation
- Running the Agent
- Project Structure
- Usage Examples
- Heuristics Layer
- Troubleshooting & FAQ
- Contributing
- License
- Credits

## 🏗 Hand-Drawn Architecture
![hand-drawn-architecture](/architecture.jpg)

## 🏗 Architecture
At a high level, the agent operates in a **Perception → Planning → Action → Memory → Evaluation** loop.

User Query  
↓  
Perception (LLM interprets intent, selects tool servers)  
↓  
Planning (LLM creates `solve()` using available tools)  
↓  
Sandbox (executes code securely)  
↓  
Memory (stores steps & results)  
↓  
Final Answer  

## 🛠 Installation
### Prerequisites
- Python 3.10+
- pip / venv
- MCP servers installed locally
- OpenAI or Gemini API keys

### Setup
```bash
git clone <repo-url>
cd <project>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables
Create `.env`:
```
OPENAI_API_KEY=xxxx
GEMINI_API_KEY=xxxx
```

## ▶️ Running the Agent
```bash
python agent.py
```

## 📂 Project Structure
```
.
├── agent.py
├── core/
│   ├── context.py
│   ├── loop.py
│   ├── session.py
│   ├── strategy.py
├── modules/
│   ├── action.py
│   ├── decision.py
│   ├── perception.py
│   ├── model_manager.py
│   ├── tools.py
│   ├── heuristics.py
├── mcp_servers/
│   ├── websearch_server.py
│   ├── document_server.py
│   ├── math_server.py
├── config/
│   ├── profiles.yaml
├── requirements.txt
└── README.md
```

## 🤝 Contributing
PRs and issues welcome.

## 📄 License
MIT License.

## 🙏 Credits
Developed by Ganesh Yeluri & contributors.
