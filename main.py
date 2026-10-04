import asyncio
from pyrogram import Client, filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant

import config
import db

app = Client("art_suggestion_bot", api_id=config.API_ID, api_hash=config.API_HASH, bot_token=config.BOT_TOKEN, workdir=config.STATE_DIR)

processed_albums = set()
pending_rejections = {}

db.init_db()
print("Bot started.")

def build_media_group(media_data, caption=None):
    media_group = []
    for item in media_data:
        if item['type'] == 'photo':
            media_group.append(types.InputMediaPhoto(item['id']))
        elif item['type'] == 'video':
            media_group.append(types.InputMediaVideo(item['id']))
    
    # In Telegram media groups, the caption is attached to the first media item
    if media_group and caption:
        media_group[0].caption = caption
        
    return media_group

async def process_offer(user_id, messages):
    try:
        await app.get_chat_member(config.CHANNEL_ID, user_id)
    except UserNotParticipant:
        await app.send_message(user_id, "❌ You must be a member of our channel to suggest posts!")
        return
    except Exception as e:
        print(f"Membership check error: {e}")
        return

    # Extract file_id and type
    media_list = []
    caption = None
    
    for msg in messages:
        # Capture the first available caption found in the group/single message
        if not caption and msg.caption:
            caption = msg.caption
            
        if msg.photo:
            media_list.append({"id": msg.photo.file_id, "type": "photo"})
        elif msg.video:
            media_list.append({"id": msg.video.file_id, "type": "video"})

    media_group = build_media_group(media_list, caption)

    if db.is_allowed(user_id):
        await app.send_media_group(config.CHANNEL_ID, media_group)
        await app.send_message(user_id, "✅ Your suggestion has been posted to the channel!")
    else:
        offer_id = db.save_pending_offer(user_id, media_list, caption)
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"app_{offer_id}"),
                InlineKeyboardButton("❌ No", callback_data=f"rej_{offer_id}")
            ]
        ])
        
        # Notify owner
        await app.send_message(
            config.OWNER_ID, 
            f"📩 New suggestion #`{offer_id}` from user `{user_id}`. Approve?", 
            reply_markup=keyboard
        )
        # Send the album to the owner
        await app.send_media_group(config.OWNER_ID, media_group)
        await app.send_message(user_id, f"⏳ Your suggestion #`{offer_id}` has been sent to the owner for review.")

@app.on_message((filters.photo | filters.video))
async def handle_media(client, message):
    if message.text and message.text.startswith("/"): return

    if message.media_group_id:
        if message.media_group_id in processed_albums: return
        processed_albums.add(message.media_group_id)
        group = await client.get_media_group(message.chat.id, message.id)
        await process_offer(message.from_user.id, group)
    else:
        await process_offer(message.from_user.id, [message])

@app.on_callback_query()
async def handle_callbacks(client, callback_query):
    data = callback_query.data
    
    if data.startswith("app_"):
        offer_id = int(data.split("_")[1])
        offer = db.get_pending_offer(offer_id)
        if offer:
            media_group = build_media_group(offer["media"], offer["caption"])
            await client.send_media_group(config.CHANNEL_ID, media_group)
            await client.send_message(offer["user_id"], f"✅ Your suggestion #`{offer_id}` was approved and posted!")
            db.delete_pending_offer(offer_id)
            await callback_query.edit_message_text(f"✅ Suggestion {offer_id} approved.")
        else:
            await callback_query.answer("Suggestion not found.", show_alert=True)

    elif data.startswith("rej_"):
        offer_id = int(data.split("_")[1])
        offer = db.get_pending_offer(offer_id)
        if offer:
            user_id = offer["user_id"]
            if config.OWNER_ID not in pending_rejections:
                pending_rejections[config.OWNER_ID] = []
            
            pending_rejections[config.OWNER_ID].append((user_id, offer_id))
            queue_len = len(pending_rejections[config.OWNER_ID])
            
            await callback_query.answer("Added to rejection queue.")
            await client.send_message(
                config.OWNER_ID, 
                f"✍️ Describe why you canceled suggestion #`{offer_id}`:\n(Queue: {queue_len} pending reason(s))"
            )
            await callback_query.edit_message_text(f"❌ Suggestion {offer_id} queued for rejection.")
            db.delete_pending_offer(offer_id)
        else:
            await callback_query.answer("Suggestion not found.", show_alert=True)

@app.on_message(filters.text & filters.user(config.OWNER_ID))
async def handle_owner_text(client, message):
    if message.text.startswith("/allow"):
        try:
            uid = int(message.text.split()[1])
            db.add_user(uid)
            await message.reply(f"✅ User {uid} is now allowed.")
        except: await message.reply("Usage: `/allow 1234567`")
        return

    if message.text.startswith("/disallow"):
        try:
            uid = int(message.text.split()[1])
            db.remove_user(uid)
            await message.reply(f"❌ User {uid} removed.")
        except: await message.reply("Usage: `/disallow 1234567`")
        return

    if config.OWNER_ID in pending_rejections and pending_rejections[config.OWNER_ID]:
        target_user_id, offer_id = pending_rejections[config.OWNER_ID].pop(0)
        try:
            await client.send_message(
                target_user_id, 
                f"❌ Your suggestion #`{offer_id}` was declined.\n\nReason: {message.text}"
            )
            remaining = len(pending_rejections[config.OWNER_ID])
            if remaining > 0:
                await message.reply(f"✅ Reason for #{offer_id} sent. You still have {remaining} reason(s) to provide.")
            else:
                await message.reply(f"✅ Reason for #{offer_id} sent. Queue clear!")
        except Exception as e:
            await message.reply(f"❌ Error: {e}")

app.run()
