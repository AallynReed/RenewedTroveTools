import utils.tasks as tasks
import json
from utils.logger import log
import websockets


async def challenge_notification(page, event):
    if event["challenge_type"] == "RAMPAGE":
        await page.send_notification(
            "Rampage Challenge", f"A rampage has started.", "Rampage"
        )
    elif event["challenge_type"] == "COLLECTION":
        await page.send_notification(
            "Collection Challenge",
            f"A collection challenge has started. Head to hub and take the portal.",
            "Dragon Coin Challenge",
        )
    elif event["challenge_type"] == "DUNGEON":
        await page.send_notification(
            "Dungeon Challenge",
            f"A dungeon challenge has started in {event['name']} biome.",
            "Dungeon",
        )


async def chaos_chest_notification(page, event):
    await page.send_notification(
        "Chaos Chest",
        f"{event['item']} is now in Chaos Chest with increased odds.",
        "Chaos Chest",
    )


async def luxion_notification(page, event):
    await page.send_notification("Luxion", f"Luxion has arrived in the hub.", "Luxion")


async def corruxion_notification(page, event):
    await page.RTT.send_notification(
        "Corruxion", f"Corruxion has arrived in the hub.", "Corruxion"
    )


async def fluxion_notification(page, event):
    await page.RTT.send_notification(
        "Fluxion", f"Fluxion has arrived in the hub.", "Fluxion"
    )


async def leaderboards_notification(page, event):
    await page.send_notification(
        "Leaderboards",
        f"Leaderboards have been updated on Trovesaurus",
        "Leaderboards",
        url=("Open Trovesaurus", "https://trovesaurus.com/leaderboards"),
    )


async def notification_manager(page, event):
    if event["event"] == "challenge":
        await challenge_notification(page, event["data"])
    elif event["event"] == "chaos_chest":
        await chaos_chest_notification(page, event["data"])
    elif event["event"] == "luxion":
        await luxion_notification(page, event["data"])
    elif event["event"] == "corruxion":
        await corruxion_notification(page, event["data"])
    elif event["event"] == "fluxion":
        await fluxion_notification(page, event["data"])
    elif event["event"] == "leaderboards":
        await leaderboards_notification(page, event["data"])


@tasks.loop(seconds=0.1)
async def event_receiver(page):
    try:
        async with websockets.connect("wss://events.aallyn.xyz/") as ws:
            log("Tasks").info("Connected to events websocket")
            async for message in ws:
                event = json.loads(message)
                log("Tasks").debug(f"Received event: {event}")
                await notification_manager(page, event)
    except Exception as e:
        log("Tasks").error(f"Failed to receive events: {e}\nRetrying...")
