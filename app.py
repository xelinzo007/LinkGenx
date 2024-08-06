import httpx
from telethon import TelegramClient, events
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import urllib.parse
import re
from asyncio import Queue
import logging

# Replace these values with your own
api_id = 20870301
api_hash = 'ea27e2de02e64bd057473f07031b30f0'
bot_token = '7321648492:AAHCCydX4EEJXgbKRJVEpzEOdiKoTHtulV4'

# Configure logging
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize the Telethon client for the bot
bot_client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)
# Initialize the Telethon client for the userbot
userbot_client = TelegramClient('userbot', api_id, api_hash)

# Queue for message processing
message_queue = Queue()

# async def get_extra_pe_bot_response(url):
#     try:
#         #await userbot_client.start()
#         #bot = await userbot_client.get_entity('@ExtraPeBot')
#         async with userbot_client.conversation(2015117555) as conv:
#             await conv.send_message(url)
#             response_message = await conv.get_response()
#             return response_message.text
#     except Exception as e:
#         logger.error(f"Error while getting response from ExtraPeBot: {e}")
#         return None
    
async def get_extra_pe_bot_response(url):
    try:
        # Send the message to the bot
        await userbot_client.send_message(2015117555, url)
        
        messages = await userbot_client.get_messages(2015117555, limit=1)
        if messages:
            return messages[0].text
    except Exception as e:
        logger.error(f"Error while getting response from ExtraPeBot: {e}")
        return None

def encode_url(url):
    try:
        return urllib.parse.quote_plus(url).replace("'", "%27").replace('"', "%22")
    except Exception as e:
        logger.error(f"Error while encoding URL {url}: {e}")
        return url

def is_amazon_url(url):
    try:
        return "amazon.in" in url
    except Exception as e:
        print(str(e))
        logger.error(f"Error while checking if URL is Amazon: {e}")
        return False

def get_short_url(long_url):
    try:
        # parsed_url = urllib.parse.urlparse(long_url)
        # query_params = urllib.parse.parse_qs(parsed_url.query)
        # query_params['tag'] = 'prolooterzz-21'
        # new_query = urllib.parse.urlencode(query_params, doseq=True)
        # new_url = parsed_url._replace(query=new_query).geturl()
        # Parse the URL
        parsed_url = urlparse(long_url)

        # Parse query parameters
        query_params = parse_qs(parsed_url.query)

        # Update the query parameters
        query_params['tag'] = 'prolooterzz-21'

        # Rebuild the URL with updated query parameters
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse(parsed_url._replace(query=new_query))
        encoded_url = encode_url(new_url)
        response = httpx.get(f'https://www.amazon.in/associates/sitestripe/getShortUrl?longUrl={encoded_url}&marketplaceId=44571')
        if response:
            data = response.json()
            #print(data)
            return data.get('longUrl', None)
    except Exception as e:
        logger.error(f"Error while getting short URL for {long_url}: {e}")
    return None

async def process_message(event):
    try:
        original_message = event.message
        message = original_message.message
        urls = []

        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(message)

        processing_message = await event.reply('Processing your request... 🕒')

        for url in urls:
            try:
                response = httpx.get(url,follow_redirects=True)
                #print(type(response.url))
                #print(is_amazon_url(response.url))
                if is_amazon_url(str(response.url)):
                    short_url = get_short_url(str(response.url))
                    print(short_url)
                    if short_url:
                        message = message.replace(url, f'<a href="{short_url}">🛒 Buy Now</a>')
                else:
                    extra_pe_bot_response = await get_extra_pe_bot_response(url)
                    if extra_pe_bot_response:
                        message = message.replace(url, f'<a href="{extra_pe_bot_response}">🛒 Buy Now </a>')
            except Exception as e:
                logger.error(f"Error while processing URL {url}: {e}")

        bold_message = f'<b>{message}</b>'
        await processing_message.edit(bold_message, parse_mode='html')

    except Exception as e:
        logger.error(f"Error while processing message {event.message.id}: {e}")

@bot_client.on(events.NewMessage())
async def handler(event):
    if event.is_group:
        try:
            await message_queue.put(event)
        except Exception as e:
            logger.error(f"Error while adding message to queue: {e}")

async def message_processor():
    while True:
        try:
            event = await message_queue.get()
            if event.message.fwd_from:
                logger.info(f"Processing forwarded message from {event.message.fwd_from.from_id}")
            await process_message(event)
        except Exception as e:
            logger.error(f"Error while processing message from queue: {e}")
        finally:
            message_queue.task_done()

# Start the background task for processing messages
bot_client.loop.create_task(message_processor())

# Run the clients
logger.info("Starting bot clients")
try:
    bot_client.start()
    userbot_client.start()
    bot_client.run_until_disconnected()
except Exception as e:
    logger.error(f"Error while running bot clients: {e}")
