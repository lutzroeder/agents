
import asyncio
import sys
import threading
import time

import agents
import pydantic


class Progress:

    def __init__(self, text):
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.text = text

    def spin(self):
        status = ""
        while threading.current_thread() is self.thread:
            frame = self.frames[self.index]
            status = f"\r{self.text}... {frame} {self.status}"
            print(status, end="", flush=True)
            time.sleep(0.1)
            self.index = (self.index + 1) % len(self.frames)
        print(f"\r{self.text} ✔{' ' * (len(status) - len(self.text))}")

    def __enter__(self):
        print("\033[?25l", end="", flush=True) # hide cursor
        self.status = ""
        self.index = 0
        self.thread = threading.Thread(target=self.spin, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("\033[?25h", end="", flush=True) # show cursor
        thread = self.thread
        self.thread = None
        thread.join()

class SearchQuery(pydantic.BaseModel):
    reason: str = pydantic.Field(description="One‑sentence rationale why this query advances the user’s goal.")
    query: str = pydantic.Field("Exact phrase to paste into the search engine.")

class SearchPlan(pydantic.BaseModel):
    searches: list[SearchQuery] = pydantic.Field(description="List of distinct web searches to perform to best answer to the user query.")

class Report(pydantic.BaseModel):
    summary: str = pydantic.Field("Less than 75‑word executive summary in plain text.")
    report: str = pydantic.Field("Full Markdown report.")

async def main():
    user_prompt = sys.argv[1] if len(sys.argv) > 1 else None
    user_request = input("\U0001F464 User: ") if not user_prompt else user_prompt
    model_settings = agents.ModelSettings(reasoning={"effort": "low"})
    with Progress("\U0001F916 Planning"):
        prompt = """You are a research planning assistant.
Given a query, create a set of web searches to find content to best answer the query.
Output between 10 and 20 terms to query for."""
        agent = agents.Agent(name="Plan", instructions=prompt, model="gpt-5.2", tools=[agents.WebSearchTool()], model_settings=model_settings, output_type=SearchPlan)
        result = await agents.Runner.run(agent, f"Query: {user_request}")
        plan = result.final_output_as(SearchPlan)
    for item in plan.searches:
        print(f'\033[90m   {item.query}\033[0m')
    with Progress("\U0001F50D Searching") as spinner:
        prompt = """You are a research assistant. Search the web based on a given search term and produce a concise summary of the results.
    The summary must be 2-3 paragraphs and less than 300 words. Capture the main points. Write succinctly, no need to have complete sentences or good grammar.
    This will be consumed by an expert synthesizing a report, so its vital to capture the essence and ignore any fluff.
    Do not include any additional commentary other than the summary itself."""
        agent = agents.Agent(name="Search", instructions=prompt, model="gpt-5-mini", tools=[agents.WebSearchTool()], model_settings=agents.ModelSettings(tool_choice="required"))
        async def search_item(item: SearchQuery) -> str:
            result = await agents.Runner.run(agent, f"Search term: {item.query}\nReason for searching: {item.reason}")
            return str(result.final_output)
        completed = 0
        tasks = [asyncio.create_task(search_item(item)) for item in plan.searches]
        search_results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                search_results.append(result)
            completed += 1
            spinner.status = f"({completed}/{len(tasks)} completed)"
    with Progress("\U0001F4DD Summarizing"):
        prompt = """You are a senior researcher tasked with writing a cohesive report for a user query.
You will be provided with the original query, and initial research done by a research assistant.
First create an outline that describes the structure and flow of the report.
Then, generate the report and return that as your final output.
The final output should be detailed in markdown format with for 5-10 pages of content, at least 1000 words."""
        agent = agents.Agent(name="Summary", instructions=prompt, model="gpt-5.2", model_settings=model_settings, output_type=Report)
        result = await agents.Runner.run(agent, f"Original query: {user_request}\nSummarized search results: {search_results}")
        report = result.final_output_as(Report)
    print(f"\n\n{report.summary}\n")
    print(f"{report.report}")

if __name__ == "__main__":
    asyncio.run(main())
