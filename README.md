# Tiny Agents

Minimal coding, computer-use, and research agents using the OpenAI Agents SDK.

* [code.py](code.py) - A minimal coding agent in 250 lines of Python code.
* [cua.py](cua.py) - A minimal computer-use agent in 100 lines of Python code.
* [research.py](research.py) - A minimal research agent in 100 lines of Python code.

## Get started

Clone this repository, install the OpenAI Agents SDK, and set the OpenAI API key

```bash
git clone https://github.com/lutzroeder/agents
pip install openai-agents
# Windows
set OPENAI_API_KEY=...
# macOS/Linux
export OPENAI_API_KEY=...
```

## Coding Agent

A minimal coding agent inspired by [Raising the bar on SWE-bench](https://www.anthropic.com/engineering/swe-bench-sonnet) in 250 lines of Python code.

```bash
python code.py <directory>
```
```
👤 User: Explain this code to me
🤖 I'll help you understand the code in this repository. Let's first explore the repository structure to get a better understanding of what we're looking at.
🔍 > view .
Let's check the main code file, gpt2.py:
🔍 > view gpt2.py
Let's also check the README to understand more about this project:
🔍 > view README.md
This repository contains a minimalist implementation of OpenAI's GPT-2 language model using PyTorch.
...
```

## Computer-Use Agent

A minimal computer-use agent in 100 lines of Python code.

```bash
pip install pyautogui
python cua.py
```
```
👤 User: Open browser at lutzroeder.com
   screenshot {}

🤖 Action: Opening web browser, checking Edge icon
   click {'button': 'left', 'x': 1388, 'y': 1544}
   wait {}

🤖 Action: Navigating to lutzroeder.com in Edge
   click {'button': 'left', 'x': 1056, 'y': 104}
   type {'text': 'lutzroeder.com'}
   keypress {'keys': ['ENTER']}
   wait {}

🤖 Agent: The website lutzroeder.com is open in the browser...

👤 User: 
```

## Research Agent

A minimal research agent in 100 lines of Python code.

```bash
python research.py
```
```
👤 User: top news today
🤖 Planning ✔
🔍 Searching ✔
📝 Summarizing ✔

This comprehensive report synthesizes today's top news...
```
