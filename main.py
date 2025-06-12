from flask import Flask, request, jsonify, send_from_directory
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
import asyncio
import os

# Replace with your actual API credentials
api_id = 24914709
api_hash = 'f5e754488031c381047f08edd3f70894'

client = TelegramClient('session', api_id, api_hash)

app = Flask(__name__)

# Path to store downloaded images
IMAGE_FOLDER = os.path.join(os.getcwd(), 'static', 'images')
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# Start Telegram client
async def start_telegram_client():
    await client.start()

# Initialize Telegram client before the Flask server runs
loop = asyncio.get_event_loop()
loop.run_until_complete(start_telegram_client())

@app.route('/channel_best_messages')
def best_messages():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Missing username'}), 400

    async def fetch():
        messages = [m async for m in client.iter_messages(username, limit=100) if m.views]
        top = sorted(messages, key=lambda m: m.views or 0, reverse=True)[:10]
        result = []

        for msg in top:
            image_url = None

            # Download image if photo exists
            if isinstance(msg.media, MessageMediaPhoto):
                filename = f"msg_{msg.id}.jpg"
                filepath = os.path.join(IMAGE_FOLDER, filename)
                await client.download_media(msg.media, file=filepath)
                image_url = f"/static/images/{filename}"

            replies = []
            top_comment = None
            top_reactions = 0

            try:
                async for reply in client.iter_messages(username, reply_to=msg.id):
                    replies.append(reply)
                    if reply.reactions:
                        count = sum(r.count for r in reply.reactions.results)
                        if count > top_reactions:
                            top_reactions = count
                            top_comment = reply.text
            except Exception:
                pass

            result.append({
                'url': f'https://t.me/{username}/{msg.id}',
                'views': msg.views,
                'text': msg.text,
                'image_url': image_url,
                'comments_count': len(replies),
                'top_comment': top_comment
            })

        return result

    data = loop.run_until_complete(fetch())
    return jsonify(data)

# Serve downloaded images manually if needed
@app.route('/static/images/<filename>')
def send_image(filename):
    return send_from_directory(IMAGE_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
