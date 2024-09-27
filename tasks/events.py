import utils.tasks as tasks
from aiohttp import ClientSession
import json
import win11toast
from utils.logger import log


def handle_sse_event(event_data):
    lines = event_data.split("\n")
    event = {}
    for line in lines:
        if line.startswith("data: "):
            event["data"] = json.loads(line[6:])
        elif line.startswith("event: "):
            event["event"] = line[7:]
        elif line.startswith("id: "):
            event["id"] = line[4:]
        elif line.startswith("retry: "):
            event["retry"] = line[7:]
    if event.get("event") == "heartbeat":
        log("Tasks").debug("Received event heartbeat")
        return
    else:
        return event


@tasks.loop(seconds=0.1)
async def event_receiver(page):
    event_receiver.cancel()
    try:
        async with ClientSession() as session:
            async with session.get(
                "https://kiwiapi.aallyn.xyz/v1/events/", timeout=None
            ) as response:
                log("Tasks").info("Connected to events stream")
                buffer = ""
                async for chunk in response.content.iter_any():
                    chunk = chunk.decode("utf-8")
                    buffer += chunk
                    if "\n\n" in buffer:
                        events = buffer.split("\n\n")
                        buffer = events.pop()
                        for event in events:
                            event = handle_sse_event(event)
                            if event is not None:
                                ...  # This is where the event is handled
    except Exception as e:
        log("Tasks").error(f"Failed to receive events: {e}\nRetrying...")
