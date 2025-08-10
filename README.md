GZCTF Discord Webhook
==========================


DESCRIPTION
------------

This script acts as a real-time notification bot that forwards events from the GZCTF platform (like new challenges, hints, and First Bloods) to a Discord channel using webhooks.

The script is designed to run continuously inside a Docker container.


CONFIGURATION
-------------

Before running, open and edit the `Webhooks.py` file to fill in the following variables:

  * GAME_ID: The ID of the CTF event you want to monitor.
  * COOKIE: Your session cookie. The format must be 'NAME=VALUE'. DO NOT SHARE THIS.
  * CHANNEL_ANNOUNCEMENTS: The Discord webhook URL for announcements.
  * CHANNEL_SOLVES: The Discord webhook URL for solve notifications.


HOW TO RUN (WITH DOCKER)
------------------------

1. Make sure all files (alert.py, Dockerfile, requirements.txt) are in the same directory.

2. Open a terminal in that directory, then build the Docker image:

       docker build -t gzctf-webhook .

3. After the build is complete, run the container in the background:

       docker run -d --restart always --name gzctf-bot gzctf-webhook

4. Done. The bot is now running.


USEFUL COMMANDS
---------------

* To view the bot's logs:

      docker logs -f gzctf-bot

* To stop the bot:

      docker stop gzctf-bot

* To remove the bot container (do this before rebuilding):

      docker rm gzctf-bot
