import asyncio
import base64
import io
import platform

import agents
import pyautogui


class LocalComputer(agents.AsyncComputer):

    def __init__(self):
        screenshot = pyautogui.screenshot()
        self.size = screenshot.size

    @property
    def environment(self) -> agents.Environment:
        system = platform.system().lower()
        return "mac" if system == "darwin" else system

    @property
    def dimensions(self) -> tuple[int, int]:
        return self.size

    async def screenshot(self) -> str:
        buffer = io.BytesIO()
        pyautogui.screenshot().save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    async def click(self, x: int, y: int, button: str = "left") -> None:
        if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
            button = "middle" if button == "wheel" else button
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.click(x, y, button=button)

    async def double_click(self, x: int, y: int) -> None:
        if 0 <= x < self.size[0] and 0 <= y < self.size[1]:
            pyautogui.moveTo(x, y, duration=0.1)
            pyautogui.doubleClick(x, y)

    async def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        pyautogui.scroll(-scroll_y, x=x, y=y)
        pyautogui.hscroll(scroll_x, x=x, y=y)

    async def type(self, text: str) -> None:
        pyautogui.write(text)

    async def wait(self, ms: int = 1000) -> None:
        await asyncio.sleep(ms / 1000)

    async def move(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y, duration=0.1)

    async def keypress(self, keys: list[str]) -> None:
        keymap = {
            "arrowdown": "down", "arrowleft": "left",
            "arrowright": "right", "arrowup": "up",
        }
        keys = [keymap.get(key.lower(), key.lower()) for key in keys]
        for key in keys:
            pyautogui.keyDown(key)
        for key in keys:
            pyautogui.keyUp(key)

    async def drag(self, path: list[tuple[int, int]]) -> None:
        if len(path) >= 2:
            pyautogui.moveTo(path[0][0], path[0][1], duration=0.5)
            for point in path[1:]:
                pyautogui.dragTo(point[0], point[1], duration=1.0, button="left")

async def main():
    agent = agents.Agent(
        "computer-use",
        "You are a helpful agent. DO NOT ask the user for confirmations.",
        model="computer-use-preview",
        model_settings=agents.ModelSettings(truncation="auto",
            reasoning={"generate_summary": "concise"}),
        tools=[agents.ComputerTool(LocalComputer())],
    )
    while True:
        prompt = input("\U0001F464 User: ")
        stream = agents.Runner.run_streamed(agent, prompt, max_turns=100)
        async for event in stream.stream_events():
            if event.type == 'run_item_stream_event':
                if event.name == 'tool_called':
                    action_args = vars(event.item.raw_item.action) | {}
                    action = action_args.pop("type")
                    print(f"   {action} {action_args}")
                elif event.name == "reasoning_item_created":
                    summary = "".join([_.text for _ in event.item.raw_item.summary])
                    print(f"\n\U0001F916 Action: {summary}")
            if event.type == 'raw_response_event':
                if event.data.type == "response.output_text.done":
                    print(f"\n\U0001F916 Agent: {event.data.text}\n")

asyncio.run(main())
