import time
import _thread as thread
from websocket import WebSocketApp
import websocket
import requests
import json
import logging

# --- IMPORTANT CONFIGURATION (FILL THIS PART) ---

# Set the correct game ID.
GAME_ID = ...  # Replace with your actual game ID.

# Replace with your NEW cookie in "NAME=VALUE" format.
# DO NOT SHARE THIS WITH ANYONE!
COOKIE = '.....'

# Replace with your Discord Webhook URLs.
CHANNEL_ANNOUNCEMENTS = 'https://discordapp.com/api/webhooks/......'
CHANNEL_SOLVES = 'https://discordapp.com/api/webhooks/......'

# --- END OF CONFIGURATION ---

# Simple logger configuration.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

RUNNING = True

def sendMsg(url, title, description, color):
    """Sends an embed message to the Discord webhook URL."""
    try:
        webhook_data = {
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
            }]
        }

        # Sending data as JSON
        result = requests.post(
            url,
            json=webhook_data,
            headers={'Content-Type': 'application/json'},
            timeout=(15, 30)
        )

        # Check for errors from Discord's side
        result.raise_for_status()
        logger.info(f"Embed sent: {title}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send embed to Discord: {e}")


def format_detailed_message(arg):
    """
    Formats the argument from the server into a dictionary for a Discord embed.
    """
    try:
        msg_type = arg.get('type')
        values = arg.get('values', [])

        if not values:
            return None

        if msg_type == 'NewChallenge':
            challenge_name = values[0]
            return {
                "title": "New Challenge",
                "description": f"🎉 Challenge **`{challenge_name}`** has been published! 🎉",
                "color": 0x2ecc71 # Green
            }

        elif msg_type == 'NewHint':
            challenge_name = values[0]
            return {
                "title": "New Hint",
                "description": f"💡 A new hint is available for challenge **`{challenge_name}`**.",
                "color": 0x3498db # Blue
            }

        elif msg_type in ['FirstBlood', 'SecondBlood', 'ThirdBlood']:
            solver_name = values[0]
            challenge_name = values[1]

            if msg_type == 'FirstBlood':
                return {
                    "title": "First Blood",
                    "description": f"🥇 Team/User **`{solver_name}`** was the first to solve **`{challenge_name}`**! 🩸",
                    "color": 0xf1c40f # Gold
                }
            elif msg_type == 'SecondBlood':
                return {
                    "title": "Second Blood",
                    "description": f"🥈 Team/User **`{solver_name}`** was the second to solve **`{challenge_name}`**! 😎",
                    "color": 0xc0c0c0 # Silver
                }
            elif msg_type == 'ThirdBlood':
                return {
                    "title": "Third Blood",
                    "description": f"🥉 Team/User **`{solver_name}`** was the third to solve **`{challenge_name}`**! 👍",
                    "color": 0xcd7f32 # Bronze
                }

    except (IndexError, TypeError) as e:
        logger.error(f"Failed to process arg for embed: {arg} - Error: {e}")
        return {
            "title": "Information",
            "description": f"Failed to process notification: `{arg}`",
            "color": 0x95a5a6 # Grey
        }

    return None

def getToken():
    """Gets the connectionToken for the WebSocket session."""
    while RUNNING:
        try:
            logger.info("Attempting to get connectionToken...")
            r = requests.post(
                f'https://gzctfweb/hub/user/negotiate?game={GAME_ID}&negotiateVersion=1',
                headers={'cookie': COOKIE},
                timeout=(15, 30),
                verify=False # Ignoring SSL verification
            )
            r.raise_for_status()
            token = r.json()['connectionToken']
            logger.info("Successfully obtained connectionToken.")
            return token
        except Exception as e:
            logger.error(f"Failed to get token: {e}. Retrying in 60 seconds...")
            time.sleep(60)

class WSSClient(object):
    """Main class for handling the WebSocket connection."""
    def __init__(self, connectionToken):
        super(WSSClient, self).__init__()
        self.url = f'wss://gzctfweb/hub/user?game={GAME_ID}&id={connectionToken}'
        self.ws = None
        self.status = False

    def on_message(self, ws, message):
        if message.startswith('{"type":6}'): # Keep-alive message
            if not self.status:
                logger.info('WebSocket connection is live and active.')
                self.status = True
            ws.send(message)
            return

        if message.startswith('{}'): # Empty message, ignore
            return

        logger.info(f"Message received: {message.strip()}")
        try:
            status = json.loads(message[:-1]) # Remove trailing separator character '\x1e'
            for arg in status.get('arguments', []):
                msg_type = arg.get('type')

                target_channel = CHANNEL_ANNOUNCEMENTS
                if msg_type in ['FirstBlood', 'SecondBlood', 'ThirdBlood']:
                    target_channel = CHANNEL_SOLVES

                embed_data = format_detailed_message(arg)

                if embed_data:
                    sendMsg(url=target_channel, **embed_data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e} - Original message: {message.strip()}")
        except Exception as e:
            logger.error(f"An error occurred while processing the message: {e}")

    def on_error(self, ws, error):
        if isinstance(error, KeyboardInterrupt):
            global RUNNING
            RUNNING = False
            logger.info("Script stopped by user (Ctrl+C).")
        else:
            logger.error(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        self.status = False
        logger.warning(f"WebSocket connection closed. Code: {close_status_code}, Message: {close_msg}")

    def on_open(self, ws):
        logger.info("Opening WebSocket connection...")
        thread.start_new_thread(self.run, ())

    def run(self, *args):
        time.sleep(1)
        handshake = '{"protocol":"json","version":1}\x1e'
        self.ws.send(handshake)
        logger.info("WebSocket handshake sent.")

    def start(self):
        self.ws = WebSocketApp(self.url,
                               on_open=self.on_open,
                               on_message=self.on_message,
                               on_error=self.on_error,
                               on_close=self.on_close,
                               cookie=COOKIE)
        self.ws.run_forever()


if __name__ == '__main__':
    logger.info("Starting GZCTF Webhook...")
    while RUNNING:
        token = getToken()
        if token:
            client = WSSClient(token)
            client.start()

        if not RUNNING:
            break

        logger.warning("Connection lost. Reconnecting in 60 seconds...")
        time.sleep(60)

    logger.info("GZCTF Webhook has stopped.")