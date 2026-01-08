import os
import json
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface
from elevenlabs.types import ConversationConfig

load_dotenv()



def load_schedule():
    if os.path.exists("schedule.json"):
        with open("schedule.json", "r")as f:
            return json.load(f)
    return{"meetings": []}

def find_meeting(query):
    data = load_schedule()
    results = [m for m in data["meetings"] if query.lower() in m.lower()]
    if not results:
        return f"I couldn't find any meetings matching '{query}'."
    return f"I found the following: {', '.join(results)}"

def handle_tool_call(tool_name, arguments):
    if tool_name == "find_meeting":
        return find_meeting(arguments.get("query"))
    if tool_name == "update_calendar":
        details = arguments.get("details")
        data = load_schedule()
        data["meetings"].append(details)
        with open("schedule.json", "w") as f:
            json.dump(data, f)
        return f"Saved {details} to your schedule."
   
prompt = """
You are a helpful AI assistant. You have access to a schedule database.
1. To find a meeting: Use the 'find_meeting' tool with a search query.
2. To add a meeting: Use the 'update_calendar' tool.
Always verify with the user if you are unsure of the time.
"""

client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

config = ConversationConfig(
    conversation_config_override={
        "agent": {
            "prompt": {"prompt": prompt},
            "first_message": "Hello! I'm ready. You can ask me to find or add meetings.",
        },
    }
)

conversation = Conversation(
    client,
    os.getenv("AGENT_ID"),
    config=config,
    requires_auth=True,
    audio_interface=DefaultAudioInterface(),
    callback_agent_tool_call=handle_tool_call,
    callback_user_transcript=lambda t: print(f"User: {t}"),
    callback_agent_response=lambda r: print(f"AI: {r}")
)

conversation.start_session()