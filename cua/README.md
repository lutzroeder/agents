
# cua

A minimal computer-use agent in 100 lines of Python code using the OpenAI Agents SDK.

## Get started

1. Clone this repository
```bash
git clone https://github.com/lutzroeder/agents
```
2. Install the OpenAI Agents SDK and PyAutoGUI
```bash
pip install openai-agents pyautogui
```
3. Set OpenAI API key
```bash
set OPENAI_API_KEY=...
```
4. Example interaction with the agent:
```bash
python ./agents/cua/main.py
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