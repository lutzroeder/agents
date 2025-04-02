
# code

A minimal coding agent inspired by [Raising the bar on SWE-bench](https://www.anthropic.com/engineering/swe-bench-sonnet) in 200 lines of Python code using the OpenAI Agents SDK.

## Get started

1. Clone this agents repository and a sample code repository
```bash
git clone https://github.com/lutzroeder/agents
git clone https://github.com/lutzroeder/models
```
2. Install the OpenAI Agents SDK
```bash
pip install openai-agents
```
3. Set either the Anthropic **or** OpenAI API key
```bash
set ANTHROPIC_API_KEY=...
set OPENAI_API_KEY=...
```
4. Example interaction with the agent:
```bash
python ./agents/code/main.py ./models/gpt2
```
```
👤 User: Explain this code to me
🤖 I'll help you understand the code in this repository. Let's first explore the repository structure to get a better understanding of what we're looking at.
🔍 > view .
Let's check the main code file, gpt2.py:
🔍 > view gpt2.py
Let's also check the README to understand more about this project:
🔍 > view README.md
# Explanation of the GPT-2 Implementation

This repository contains a minimalist implementation of OpenAI's GPT-2 language model using PyTorch.
...
```
```
👤 User: document this code
🤖 I'll help you document the code in this repository. Let's start by exploring the repository structure to understand what we're working with.
🔍 > view .
Let's examine the README.md file first to understand what this project is about:
🔍 > view README.md
Now let's look at the main Python file:
🔍 > view gpt2.py
Great! Based on the examination of the code, I see that the `gpt2.py` file already has some documentation, but we can improve it by adding more detailed docstrings to the classes and methods. Let's add comprehensive documentation to make the code more understandable.

I'll now update the gpt2.py file with better documentation:
📝 > str_replace gpt2.py
Now let's add documentation to the encode and decode
...
```