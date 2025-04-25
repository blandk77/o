from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helper.database import db
from helper.utils import CANT_CONFIG_GROUP_MSG
from script import Txt
import asyncio
from asyncio.exceptions import TimeoutError
import logging
import requests
import os
import re
from urllib.parse import urlparse

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_settings = {}
TELEGRAM_GUY_DIR = "/bot/Telegram-Guy"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

# Default settings template
DEFAULT_SETTINGS = {
    "text": "Telegram Guy!!",
    "position": "top-right",
    "font_color": "white",
    "font_size": 20,
    "text_opacity": 100,
    "is_custom": False
}

# Valid positions for watermark
POSITIONS = [
    ["top-left", "top-center", "top-right"],
    ["center-left", "center", "center-right"],
    ["bottom-left", "bottom-center", "bottom-right"]
]

def get_user_settings(user_id):
    logger.info(f"Fetching settings for user {user_id}")
    if user_id not in user_settings:
        user_settings[user_id] = DEFAULT_SETTINGS.copy()
        logger.info(f"Initialized default settings for user {user_id}")
    return user_settings[user_id]

async def build_watermark_command(user_id, settings):
    logger.info(f"Building watermark command for user {user_id}")
    command = (f"drawtext=text='{settings['text']}':"
               f"fontcolor={settings['font_color']}:"
               f"fontsize={settings['font_size']}:"
               f"alpha={settings['text_opacity']/100:.2f}:"
               f"x={get_position_x(settings['position'])}:"
               f"y={get_position_y(settings['position'])}")
    full_command = f'-vf "{command}"'
    await db.set_watermark(user_id, watermark=full_command)
    logger.info(f"Watermark command set for user {user_id}: {full_command}")
    return full_command

def get_position_x(position):
    if "left" in position:
        return "10"
    elif "right" in position:
        return "(w-tw-10)"
    else:
        return "(w-tw)/2"

def get_position_y(position):
    if "top" in position:
        return "10"
    elif "bottom" in position:
        return "(h-th-10)"
    else:
        return "(h-th)/2"

def create_position_panel():
    text = "Select the position for the text from below 👇"
    buttons = [
        [InlineKeyboardButton(pos.replace('-', ' ').title(), callback_data=f"wm_pos_{pos}") for pos in row]
        for row in POSITIONS
    ]
    buttons.append([InlineKeyboardButton("Back", callback_data="wm_back")])
    return text, InlineKeyboardMarkup(buttons)
    
async def create_main_panel(user_id):
    logger.info(f"Creating main panel for user {user_id}")
    settings = get_user_settings(user_id)
    watermark = await db.get_watermark(user_id)
    logger.info(f"Watermark from DB for user {user_id}: {watermark}")

    if settings['is_custom'] or (watermark and not watermark.startswith('-vf "drawtext=text=')):
        text = "Custom Watermark Command is set.\nUse /Dwatermark or the button below to reset."
        buttons = [
            [InlineKeyboardButton("Custom Full Command", callback_data="wm_full_command")],
            [InlineKeyboardButton("Delete Watermark", callback_data="wm_delete")],
            [InlineKeyboardButton("Show Command", callback_data="wm_show")]
        ]
    else:
        text = (f"User Watermark Settings:\n"
                f"Text: {settings['text']}\n"
                f"Position: {settings['position'].replace('-', ' ').title()}\n"
                f"Font Colour: {settings['font_color'].title()}\n"
                f"Font Size: {settings['font_size']}\n"
                f"Text Opacity: {settings['text_opacity']}%")
        buttons = [
            [
                InlineKeyboardButton("Text", callback_data="wm_text"),
                InlineKeyboardButton("Position", callback_data="wm_position"),
                InlineKeyboardButton("Colour", callback_data="wm_color")
            ],
            [
                InlineKeyboardButton("Size", callback_data="wm_size"),
                InlineKeyboardButton("Opacity", callback_data="wm_opacity"),
                InlineKeyboardButton("Custom Full Command", callback_data="wm_full_command")
            ],
            [InlineKeyboardButton("Show Command", callback_data="wm_show")]
        ]
    
    logger.info(f"Main panel created for user {user_id}: {text}")
    return text, InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command("Watermark"))
async def watermark_command(client, message):
    user_id = message.from_user.id
    logger.info(f"Watermark command triggered by user {user_id}")
    try:
        text, markup = await create_main_panel(user_id)
        await message.reply(text, reply_markup=markup)
        logger.info(f"Watermark command reply sent to user {user_id}")
    except Exception as e:
        logger.error(f"Error in watermark_command for user {user_id}: {str(e)}")
        await message.reply("An error occurred. Please try again.")
        raise

@Client.on_message(filters.command("i") & (filters.reply & filters.private))
async def image_download_command(client, message):
    user_id = message.from_user.id
    logger.info(f"Image download command triggered by user {user_id}")
    
    if not message.reply_to_message:
        await message.reply("Please reply to a photo or a link starting with https://")
        return

    status_msg = await message.reply("Downloading the image.....")
    
    try:
        # Check if replied to a photo
        if message.reply_to_message.photo:
            logger.info(f"Downloading photo for user {user_id}")
            file_path = await client.download_media(message.reply_to_message.photo)
            image_data = open(file_path, "rb").read()
            os.remove(file_path)  # Clean up temporary file
        # Check if replied to a message with a link
        elif message.reply_to_message.text:
            url = message.reply_to_message.text.strip()
            if not url.startswith("https://"):
                await status_msg.edit("Invalid link. Must start with https://")
                return
            logger.info(f"Downloading image from URL for user {user_id}: {url}")
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                await status_msg.edit("Failed to download image. Invalid URL or server error.")
                return
            if int(response.headers.get("content-length", 0)) > MAX_FILE_SIZE:
                await status_msg.edit("Image size exceeds 10MB limit.")
                return
            # Validate content type
            content_type = response.headers.get("content-type", "").lower()
            if not content_type.startswith("image/"):
                await status_msg.edit("URL does not point to a valid image.")
                return
            image_data = response.content
        else:
            await status_msg.edit("Please reply to a photo or a valid https:// link.")
            return

        # Update status
        await status_msg.edit("Uploading to the Server.....")

        # Generate unique filename
        base_name = f"image_{user_id}"
        extension = ".png"  # Default extension (can be adjusted based on content-type)
        counter = 0
        filename = base_name + extension
        while os.path.exists(os.path.join(TELEGRAM_GUY_DIR, filename)):
            counter += 1
            filename = f"image{counter}_{user_id}{extension}"
        
        # Save image to Telegram-Guy folder
        file_path = os.path.join(TELEGRAM_GUY_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(image_data)
        logger.info(f"Image saved for user {user_id}: {file_path}")

        # Store filename in MongoDB
        await db.add_image(user_id, filename)
        logger.info(f"Image filename stored in DB for user {user_id}: {filename}")

        # Update status with location
        await status_msg.edit(f"Your image Location: {filename}")

    except Exception as e:
        logger.error(f"Error in image_download_command for user {user_id}: {str(e)}")
        await status_msg.edit("An error occurred while processing the image.")
        raise

@Client.on_callback_query(filters.regex("^wm_"))
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    settings = get_user_settings(user_id)
    logger.info(f"Callback received from user {user_id}: {data}")

    try:
        if data == "wm_back":
            text, markup = await create_main_panel(user_id)
            await callback_query.message.edit(text, reply_markup=markup)
            await callback_query.answer()
            return

        if data == "wm_delete":
            await db.delete_watermark(user_id)
            settings['is_custom'] = False
            text, markup = await create_main_panel(user_id)
            await callback_query.message.edit("Watermark deleted. Manual settings restored.", reply_markup=markup)
            await callback_query.answer()
            return

        if settings['is_custom'] and data in ["wm_text", "wm_position", "wm_color", "wm_size", "wm_opacity"]:
            await callback_query.message.edit(
                "Manual settings are disabled. Use /Dwatermark or 'Delete Watermark' to reset.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            await callback_query.answer()
            return

        if data == "wm_text":
            await callback_query.message.edit(
                "Send me a text to add Watermark\nTimeout: 30 seconds",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            try:
                response = await callback_query.message.chat.ask(
                    "Waiting for your text input...",
                    filters=filters.text,
                    timeout=30
                )
                text = response.text[:50].strip()
                if text:
                    settings['text'] = text
                    await callback_query.message.edit(f"Text set to: {text}")
                    await response.delete()
                    await asyncio.sleep(1)
                    text, markup = await create_main_panel(user_id)
                    await callback_query.message.edit(text, reply_markup=markup)
                else:
                    await callback_query.message.edit("Text cannot be empty. Try again.")
                await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
                await callback_query.answer()
            return

        if data == "wm_position":
            text, markup = create_position_panel()
            await callback_query.message.edit(text, reply_markup=markup)
            await callback_query.answer()
            return

        if data.startswith("wm_pos_"):
            position = data[7:]
            settings['position'] = position
            text, markup = await create_main_panel(user_id)
            await callback_query.message.edit(text, reply_markup=markup)
            await callback_query.answer()
            return

        if data == "wm_color":
            await callback_query.message.edit(
                "Send me a color name (e.g., red, blue, white)\nTimeout: 30 seconds",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            try:
                response = await callback_query.message.chat.ask(
                    "Waiting for your color input...",
                    filters=filters.text,
                    timeout=30
                )
                color = response.text.strip().lower()
                settings['font_color'] = color
                await callback_query.message.edit(f"Color set to: {color}")
                await response.delete()
                await asyncio.sleep(1)
                text, markup = await create_main_panel(user_id)
                await callback_query.message.edit(text, reply_markup=markup)
                await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
                await callback_query.answer()
            return

        if data == "wm_size":
            await callback_query.message.edit(
                "Send me a font size (number between 10-100)\nTimeout: 30 seconds",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            try:
                response = await callback_query.message.chat.ask(
                    "Waiting for your font size input...",
                    filters=filters.text,
                    timeout=30
                )
                try:
                    size = int(response.text.strip())
                    if 10 <= size <= 100:
                        settings['font_size'] = size
                        await callback_query.message.edit(f"Font size set to: {size}")
                        await response.delete()
                        await asyncio.sleep(1)
                        text, markup = await create_main_panel(user_id)
                        await callback_query.message.edit(text, reply_markup=markup)
                    else:
                        await callback_query.message.edit("Font size must be between 10 and 100. Try again.")
                    await callback_query.answer()
                except ValueError:
                    await callback_query.message.edit("Invalid number. Please send a number (e.g., 20).")
                    await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
                await callback_query.answer()
            return

        if data == "wm_opacity":
            await callback_query.message.edit(
                "Send me opacity (number between 0-100)\nTimeout: 30 seconds",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            try:
                response = await callback_query.message.chat.ask(
                    "Waiting for your opacity input...",
                    filters=filters.text,
                    timeout=30
                )
                try:
                    opacity = int(response.text.strip())
                    if 0 <= opacity <= 100:
                        settings['text_opacity'] = opacity
                        await callback_query.message.edit(f"Opacity set to: {opacity}%")
                        await response.delete()
                        await asyncio.sleep(1)
                        text, markup = await create_main_panel(user_id)
                        await callback_query.message.edit(text, reply_markup=markup)
                    else:
                        await callback_query.message.edit("Opacity must be between 0 and 100. Try again.")
                    await callback_query.answer()
                except ValueError:
                    await callback_query.message.edit("Invalid number. Please send a number (e.g., 50).")
                    await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
                await callback_query.answer()
            return

        if data == "wm_full_command":
            images = await db.get_images(user_id)
            image_list = "\n".join([f"- {img}" for img in images]) if images else "None"
            await callback_query.message.edit(
                f'Send me the full watermark command (e.g., -vf "drawtext=text=\'Your Text\':fontsize=24:fontcolor=white:x=10:y=10" or overlay/filter_complex)\n'
                f'Available images: \n{image_list}\nTimeout: 30 seconds',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            try:
                response = await callback_query.message.chat.ask(
                    "Waiting for your watermark command input...",
                    filters=filters.text,
                    timeout=30
                )
                command = response.text.strip()
                if command.startswith('-vf "') and command.endswith('"'):
                    await db.set_watermark(user_id, watermark=command)
                    settings['is_custom'] = True
                    await response.delete()
                    await callback_query.message.edit(f"Custom watermark command set.")
                    await asyncio.sleep(1)
                    text, markup = await create_main_panel(user_id)
                    await callback_query.message.edit(text, reply_markup=markup)
                else:
                    await callback_query.message.edit("Invalid command format. Must start with -vf and be enclosed in quotes.")
                await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
                await callback_query.answer()
            return

        if data == "wm_show":
            watermark = await db.get_watermark(user_id)
            if watermark:
                await callback_query.message.edit(
                    f"Your Watermark Command:\n`{watermark}`\n\n📌**Use** __/Vwatermark__ **to see your current watermark detail**\n📌 **Use** __/Dwatermark__ **To delete your watermark and encode without watermark**",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
                )
            else:
                await callback_query.message.edit(
                    "No watermark set.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
                )
            await callback_query.answer()
            return

        await callback_query.answer("Unknown callback data.")

    except Exception as e:
        logger.error(f"Error in callback handler for user {user_id}: {str(e)}")
        await callback_query.message.edit("An error occurred. Please try again.")
        await callback_query.answer("Error occurred.")


@Client.on_message((filters.group | filters.private) & filters.command('Vwatermark'))
async def view_wm(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    wm_code = await db.get_watermark(user_id)
    logger.info(f"Vwatermark command for user {user_id}: {wm_code}")

    if wm_code:
        if settings['is_custom'] or not wm_code.startswith('-vf "drawtext=text='):
            await SnowDev.edit(f"Custom Watermark Command:\n`{wm_code}`\n\n**Use** __/Dwatermark__ **To delete Watermark and encode without Watermark**")
        else:
            await SnowDev.edit(f"User Watermark Settings:\n"
                              f"Text: {settings['text']}\n"
                              f"Position: {settings['position'].replace('-', ' ').title()}\n"
                              f"Font Colour: {settings['font_color'].title()}\n"
                              f"Font Size: {settings['font_size']}\n"
                              f"Text Opacity: {settings['text_opacity']}%\n"
                              f"**Use** __/Dwatermark__ **To delete Watermark and encode without Watermark**")
    else:
        await SnowDev.edit(f"😔 __**Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Wᴀᴛᴇʀᴍᴀʀᴋ**__")

@Client.on_message((filters.group | filters.private) & filters.command('Dwatermark'))
async def delete_wm(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    user_id = message.from_user.id
    await db.delete_watermark(user_id)
    user_settings[user_id]['is_custom'] = False
    logger.info(f"Watermark deleted for user {user_id}")
    await SnowDev.edit("❌ __**Wᴀᴛᴇʀᴍᴀʀᴋ Dᴇʟᴇᴛᴇᴅ**__")
