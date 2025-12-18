import asyncio
import os
import subprocess
import sys

import agents
import openai


def read_file(path: str):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write_file(path: str, file: str):
    with open(path, "w", encoding="utf-8") as f:
        return f.write(file)

@agents.tool.function_tool
def str_replace_editor(command: str, path: str, file_text: str | None = None, view_range: list[int] | None = None, old_str: str | None = None, new_str: str | None = None, insert_line: int | None = None):
    """
    Custom editing tool for viewing, creating and editing files
    * State is persistent across command calls and discussions with the user
    * If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
    * The `create` command cannot be used if the specified `path` already exists as a file
    * If a `command` generates a long output, it will be truncated and marked with `<response clipped>`

    Notes for using the `str_replace` command:
    * The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
    * If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
    * The `new_str` parameter should contain the edited lines that should replace the `old_str`

    Args:
    command (str): The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`.
    file_text (str): Required parameter of `create` command, with the content of the file to be created.
    insert_line (int): Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.
    new_str (str): Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.
    old_str (str): Required parameter of `str_replace` command containing the string in `path` to replace.
    path (str): Absolute path to file or directory, e.g. `/repo/file.py` or `/repo`.
    view_range (list of int): Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.
    """
    def make_output(content: str, file: str, init_line: int = 1, expand_tabs: bool = True):
        content = content if len(content) <= 16000 else content[:16000] + "<response clipped><NOTE>To save on context only part of this file has been shown to you. You should retry this tool after you have searched inside the file with `grep -n` in order to find the line numbers of what you are looking for.</NOTE>"
        content = content.expandtabs() if expand_tabs else content
        content = "\n".join([f"{i + init_line:6}\t{line}" for i, line in enumerate(content.split("\n"))])
        return f"Here's the result of running `cat -n` on {file}:\n" + content + "\n"

    location = os.getcwd()
    if not os.path.commonpath([os.path.abspath(location), os.path.abspath(path)]):
        raise ValueError(f"The path '{path}' is not within the directory '{location}'.")
    if not os.path.isabs(path):
        raise NotADirectoryError(f"The path '{path}' is not an absolute path, it should start with `/`.")
    if command != "create" and not os.path.exists(path):
        raise FileNotFoundError(f"The path '{path}' does not exist")
    if command == "create" and os.path.exists(path):
        raise FileExistsError(f"File already exists at '{path}' and cannot be overwritten using `create`")
    if command != "view" and os.path.isdir(path):
        raise IsADirectoryError(f"The path '{path}' is a directory and only the `view` command can be used on directories")
    if command == "view":
        print(f"\n\U0001F50D\033[32m > {command} {os.path.relpath(path, location)}{':'+(':'.join(str(_) for _ in view_range)) if view_range else ''}\033[0m")
        if os.path.isdir(path):
            if view_range:
                raise ValueError("The `view_range` parameter is not allowed when `path` points to a directory.")
            result = []
            for root, _, files in os.walk(path):
                rel = os.path.relpath(root, path)
                depth = 0 if rel == "." else rel.count(os.sep) + 1
                if depth < 2 and (rel == '.' or not rel.startswith(".")):
                    if rel != ".":
                        result.append(os.path.join(".", rel, ""))
                    for file in files:
                        result.append(os.path.join(".", file) if rel == "." else os.path.join(".", rel, file))
            return sorted(result)
        content = read_file(path)
        first = 1
        if view_range:
            if len(view_range) != 2 or not all(isinstance(i, int) for i in view_range):
                raise ValueError("Invalid `view_range`. It should be a list of two integers.")
            lines = content.split("\n")
            line_count = len(lines)
            first, last = view_range
            if first < 1 or first > line_count:
                raise ValueError(f"Invalid `view_range`: {view_range}. Its first element `{first}` should be within the range of lines of the file: {[1, line_count]}")
            if last > line_count:
                raise ValueError(f"Invalid `view_range`: {view_range}. Its second element `{last}` should be smaller than the number of lines in the file: `{line_count}`")
            if last != -1 and last < first:
                raise ValueError(f"Invalid `view_range`: {view_range}. Its second element `{last}` should be larger or equal than its first `{first}`")
            content = "\n".join(lines[first - 1 :]) if last == -1 else "\n".join(lines[first - 1 : last])
        return make_output(content, str(path), init_line=first)
    print(f"\n\u270F\uFE0F\033[32m  > {command} {os.path.relpath(path, location)}\033[0m")
    if command == "create":
        if file_text is None:
            raise ValueError("Parameter `file_text` required for command 'create'.")
        write_file(path, file_text)
        return f"File created successfully: '{path}'."
    if command == "str_replace":
        if old_str is None:
            raise ValueError("Parameter `old_str` required for command 'str_replace'.")
        content = read_file(path).expandtabs()
        old_str = old_str.expandtabs()
        new_str = new_str.expandtabs() if new_str else ""
        occurrences = content.count(old_str)
        if occurrences == 0:
            raise ValueError(f"No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}")
        if occurrences > 1:
            raise ValueError(f"No replacement was performed. Multiple occurrences of old_str `{old_str}` in lines {[i + 1 for i, line in enumerate(content.splitlines()) if old_str in line]}. Please ensure it is unique.")
        new_content = content.replace(old_str, new_str)
        write_file(path, new_content)
        replacement = content.split(old_str)[0].count("\n")
        start = max(0, replacement - 4)
        end = replacement + 4 + new_str.count("\n")
        snippet = "\n".join(new_content.split("\n")[start : end + 1])
        output = make_output(snippet, f"a snippet of {path}", start + 1)
        return f"The file {path} has been edited. {output}Review the changes and make sure they are as expected. Edit the file again if necessary."
    if command == "insert":
        if insert_line is None or new_str is None:
            raise ValueError("Parameters `insert_line` and `new_str` are required for command 'insert'.")
        content = read_file(path).expandtabs()
        new_str = new_str.expandtabs()
        lines = content.split("\n")
        if insert_line < 0 or insert_line > len(lines):
            raise ValueError(f"Invalid `insert_line` parameter: {insert_line}. It should be within the range of lines of the file: {[0, len(lines)]}")
        new_lines = new_str.split("\n")
        snippet = "\n".join(lines[max(0, insert_line - 4) : insert_line] + new_lines + lines[insert_line : insert_line + 4])
        write_file(path, "\n".join(lines[:insert_line] + new_lines + lines[insert_line:]))
        output = make_output(snippet, "a snippet of the edited file", max(1, insert_line - 4 + 1))
        return f"The file {path} has been edited. {output}Review the changes and make sure they are as expected (correct indentation, no duplicate lines, etc). Edit the file again if necessary."
    raise ValueError(f'Unrecognized command {command}.')

@agents.tool.function_tool
def bash(command: str) -> str:
    """
    Run commands in a bash shell
    When invoking this tool, the contents of the "command" parameter does NOT need to be XML-escaped.
    You don't have access to the internet via this tool.
    You do have access to a mirror of common linux and python packages via apt and pip.
    State is persistent across command calls and discussions with the user.
    To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.
    Please avoid commands that may produce a very large amount of output.
    Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.

    Args:
    command (str): The bash command to run.
    """
    print(f"\n\U0001F5A5\033[32m  > {command}\033[0m")
    return subprocess.run(command, shell=True, capture_output=True, text=True, check=True).stdout

@agents.tool.function_tool
def apply_patch(patch_text: str) -> str:
    print("\n\U0001F4DD\033[32m  > apply_patch\033[0m")
    def write_lines(path: str, content: list) -> None:
        if "/" in path:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        write_file(path, "\n".join(content))
    lines = patch_text.strip().split("\n")
    if not lines or not lines[0].startswith("*** Begin Patch"):
        return "Error: Patch must start with '*** Begin Patch'"
    i = 1
    while i < len(lines) and not lines[i].startswith("*** End Patch"):
        cmd, i = lines[i], i + 1
        if cmd.startswith("*** Add File: "):
            path, content = cmd[14:], []
            while i < len(lines) and not lines[i].startswith("***"):
                content.append(lines[i][1:] if lines[i].startswith("+") else lines[i])
                i += 1
            if os.path.exists(path):
                raise FileExistsError(f"Cannot add file '{path}': file already exists")
            write_lines(path, content)
        elif cmd.startswith("*** Delete File: "):
            os.remove(cmd[17:])
        elif cmd.startswith("*** Update File: "):
            file_lines = read_file(cmd[17:]).split("\n")
            idx, result = 0, []
            while i < len(lines) and not lines[i].startswith("***"):
                patch_line, i = lines[i], i + 1
                if not patch_line:
                    continue
                if patch_line.startswith("@@ "):
                    found = next((j for j, line in enumerate(file_lines[idx:], idx) if line == patch_line[3:]), idx)
                    result.extend(file_lines[idx:found])
                    idx = found
                elif patch_line[0] in " -":
                    content = patch_line[1:]
                    if idx >= len(file_lines) or file_lines[idx] != content:
                        raise ValueError(f"{'Context' if patch_line[0] == ' ' else 'Deletion'} mismatch at {idx}: expected {repr(content)}, found {repr(file_lines[idx] if idx < len(file_lines) else 'EOF')}")
                    result.append(file_lines[idx]) if patch_line[0] == " " else None
                    idx += 1
                elif patch_line[0] == "+":
                    result.append(patch_line[1:])
            result.extend(file_lines[idx:])
            write_lines(cmd[17:], result)
    return "Patch applied successfully"

@agents.tool.function_tool
def shell(command: list[str], workdir: str) -> str:
    print(f"\n\U0001F5A5\033[32m  > shell {' '.join(command)} (in {workdir})\033[0m")
    result = subprocess.run(command, cwd=workdir, capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else f"Exit code {result.returncode}\n{result.stderr}"

async def main():
    argv = list(sys.argv[1:])
    model = argv.pop(0) if len(argv) > 0 and argv[0] in ('codex', 'claude', 'gemini') else 'claude'
    if len(argv) < 1 or not os.path.exists(argv[0]):
        print("Usage: python code.py [codex|claude|gemini] <directory> [prompt]")
        sys.exit(1)
    location = os.path.abspath(argv.pop(0))
    os.chdir(location)
    prompt = argv.pop(0) if len(argv) > 0 else None
    model_settings = agents.ModelSettings(truncation="auto")
    if model == 'codex':
        model = 'gpt-5.2-codex'
        model_settings.reasoning = {"effort": "medium"}
        tools = [apply_patch, shell, agents.WebSearchTool()]
    elif model == 'claude':
        tools = [str_replace_editor, bash]
        client = openai.AsyncOpenAI(api_key=os.getenv("ANTHROPIC_API_KEY"), base_url="https://api.anthropic.com/v1/")
        model = agents.OpenAIChatCompletionsModel("claude-opus-4-5", client)
    elif model == 'gemini':
        tools = [str_replace_editor, bash]
        client = openai.AsyncOpenAI(api_key=os.getenv('GEMINI_API_KEY'), base_url='https://generativelanguage.googleapis.com/v1beta/')
        model = agents.OpenAIChatCompletionsModel("gemini-2.5-pro", client)
    instructions = f"""
The code repository is in this directory: <location>{location}</location>
Your task is to answer to the user or make the minimal changes to non-tests files in the <location> directory to ensure the user request is satisfied.

Follow these steps:
1. As a first step, it might be a good idea to explore the repo to familiarize yourself with its structure.
2. If required, edit the source code of the repo to address the user request.
3. If the code changed, try to build the code and fix build errors if there are any!

Your thinking should be thorough and so it's fine if it's very long.
"""
    agent = agents.Agent("code", instructions=instructions, model=model, model_settings=model_settings, tools=tools)
    messages = []
    while True:
        user_request = input("\U0001F464 User: ") if not prompt else prompt
        print("\U0001F916 ", end="", flush=True)
        messages.append({"role": "user", "content": user_request})
        stream = agents.Runner.run_streamed(agent, messages, max_turns=100)
        response = ""
        async for event in stream.stream_events():
            if event.type == 'raw_response_event' and event.data.type == "response.output_text.delta":
                response += event.data.delta
                print(event.data.delta, end="", flush=True)
        messages.append({"role": "assistant", "content": response})
        print("")
        if prompt:
            break

asyncio.run(main())
