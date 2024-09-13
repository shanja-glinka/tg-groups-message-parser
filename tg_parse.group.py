from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv
import json
import os

load_dotenv()

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_NAME = os.getenv('SESSION_NAME', 'sess_def_acc')
SOURCE_CHAT_ID = int(os.getenv('SOURCE_CHAT_ID'))
TARGET_CHAT_ID = int(os.getenv('TARGET_CHAT_ID'))
TRACKING_FILE = os.getenv('TRACKING_FILE', 'message_tracking.id.json')
MESSAGES_FILE = os.getenv('MESSAGES_FILE', 'messages.json')

app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)


if os.path.exists(TRACKING_FILE):
    with open(TRACKING_FILE, 'r') as file:
        message_mapping = json.load(file)
else:
    message_mapping = {}


with open(TRACKING_FILE, 'r') as file:
    message_mapping = json.load(file)


if os.path.exists(MESSAGES_FILE):
    with open(MESSAGES_FILE, 'r') as file:
        messages = json.load(file)
else:
    print(f"Error: File {MESSAGES_FILE} not found.")
    messages = {}


def save_message_mapping():
    with open(TRACKING_FILE, 'w') as file:
        json.dump(message_mapping, file)

def get_message_by_slug(slug, **kwargs):
    message_template = messages.get(slug, slug)
    return message_template.format(**kwargs)

@app.on_message(filters.chat(SOURCE_CHAT_ID))
def forward_message(client, message: Message):
    if message.forwards and message.forwards.is_hidden:
        # If forwarding is prohibited, create a new message in the target group
        new_message_text = get_message_by_slug("message_redirected", re=f"\n\n{message.text or message.caption}")
        forwarded_message = client.send_message(TARGET_CHAT_ID, new_message_text)

        # If there are media files, send them again
        if message.media:
            client.send_media_group(TARGET_CHAT_ID, [message])
    else:
        # If forwarding is allowed, copy the message to the target group
        forwarded_message = message.copy(TARGET_CHAT_ID)

    message_mapping[message.message_id] = {
        'target_message_id': forwarded_message.message_id,
        'link': forwarded_message.link
    }
    save_message_mapping()

@app.on_edited_message(filters.chat(SOURCE_CHAT_ID))
def edited_message(client, message: Message):
    if message.message_id in message_mapping:
        edit_info = get_message_by_slug("message_edited", link=message.link)
        client.send_message(TARGET_CHAT_ID, edit_info)

@app.on_deleted_messages(filters.chat(SOURCE_CHAT_ID))
def deleted_message(client, messages):
    for message in messages:
        if message.message_id in message_mapping:
            delete_info = get_message_by_slug("message_deleted", link=message_mapping[message.message_id]['link'])
            client.send_message(TARGET_CHAT_ID, delete_info)

app.run()