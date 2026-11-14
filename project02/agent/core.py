import json
import sys
import settings
from groq import Groq
from agent.memory import ConversationMemory
from tools.registry import ToolRegistry


def _safe_print(*args):
    text = " ".join("" if a is None else str(a) for a in args)
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


class Agent:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.memory = ConversationMemory()
        self.registry = ToolRegistry()

    def run(self, user_text: str, max_steps: int = 8, on_progress=None):
        self.memory.add_user_message(user_text)

        
        for step in range(max_steps):
            response = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=self.memory.get_messages(),
                tools=self.registry.get_schemas(),
                tool_choice="auto",
            )
            message = response.choices[0].message

            if not message.tool_calls:
                _safe_print("final:", message.content)
                self.memory.add_assistant_message(content=message.content)
                return message.content

            self.memory.add_assistant_message(
                content=message.content,
                tool_calls=[tc.model_dump() for tc in message.tool_calls],
            )

            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments or "{}")
                if on_progress:
                    on_progress(f"Step {step + 1}: calling `{name}`…")
                result = self.registry.execute(name, args)
                if on_progress:
                    on_progress(f"`{name}` finished")
                summary = result if len(result) < 300 else result[:300] + "..."
                _safe_print(f"step {step + 1} ran tool: {name} | {summary}")
                self.memory.add_tool_result(tool_call.id, result[:1500])

        stop_message = "stopped: too many tool steps."
        _safe_print(f"final: {stop_message}")
        return stop_message


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    agent = Agent()
    agent.run("search for python jobs already in the database. do not scrape.")
