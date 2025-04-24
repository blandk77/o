from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helper.database import db
from helper.utils import CANT_CONFIG_GROUP_MSG
from script import Txt
import asyncio
from asyncio.exceptions import TimeoutError
import logging

# Set up logging for debugging (optional)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_settings = {}

# Default settings template
DEFAULT_SETTINGS = {
    "text": "Telegram Guy!!",
    "position": "top-right",
    "font_color": "white",
    "font_size": 20,
    "text_opacity": 100
}

# Valid positions for watermark
POSITIONS = [
    ["top-left", "top-center", "top-right"],
    ["center-left", "center", "center-right"],
    ["bottom-left", "bottom-center", "bottom-right"]
]

def get_user_settings(user_id):
    if user_id not in user_settings:
        user_settings[user_id] = DEFAULT_SETTINGS.copy()
    return user_settings[user_id]

async def build_watermark_command(user_id, settings):
    command = (f"drawtext=text='{settings['text']}':"
               f"fontcolor={settings['font_color']}:"
               f"fontsize={settings['font_size']}:"
               f"alpha={settings['text_opacity']/100:.2f}:"
               f"x={get_position_x(settings['position'])}:"
               f"y={get_position_y(settings['position'])}")
    full_command = f'-vf "{command}"'
    await db.set_watermark(user_id, watermark=full_command)
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

def create_main_panel(user_id):
    settings = get_user_settings(user_id)
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
            InlineKeyboardButton("Custom Full Command", callback_data="wm_full_command")  # NEW: Added Full Command button
        ],
        [InlineKeyboardButton("Show Command", callback_data="wm_show")]
    ]
    
    return text, InlineKeyboardMarkup(buttons)

def create_position_panel():
    text = "Select the position for the text from below 👇"
    buttons = [
        [InlineKeyboardButton(pos.replace('-', ' ').title(), callback_data=f"wm_pos_{pos}") for pos in row]
        for row in POSITIONS
    ]
    buttons.append([InlineKeyboardButton("Back", callback_data="wm_back")])
    return text, InlineKeyboardMarkup(buttons)


@Client.on_message(filters.command("Watermark"))
async def watermark_command(client, message):
    user_id = message.from_user.id
    text, markup = create_main_panel(user_id)
    await message.reply(text, reply_markup=markup)

@Client.on_callback_query(filters.regex("^wm_"))
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    settings = get_user_settings(user_id)

    try:
        logger.info(f"Received callback from user {user_id}: {data}")  # Debug log

        if data == "wm_back":
            text, markup = create_main_panel(user_id)
            await callback_query.message.edit(text, reply_markup=markup)
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
                text = response.text[:50].strip()  # Limit text length
                if text:
                    settings['text'] = text
                    await callback_query.message.edit(f"Text set to: {text}")
                    await asyncio.sleep(1)  # Brief delay for better UX
                    text, markup = create_main_panel(user_id)
                    await callback_query.message.edit(text, reply_markup=markup)
                else:
                    await callback_query.message.edit("Text cannot be empty. Try again.")
                await callback_query.answer()
            except TimeoutError:
                text, markup = create_main_panel(user_id)
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
            text, markup = create_main_panel(user_id)
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
                await asyncio.sleep(1)  # Brief delay for better UX
                text, markup = create_main_panel(user_id)
                await callback_query.message.edit(text, reply_markup=markup)
                await callback_query.answer()
            except TimeoutError:
                text, markup = create_main_panel(user_id)
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
                        await asyncio.sleep(1)  # Brief delay for better UX
                        text, markup = create_main_panel(user_id)
                        await callback_query.message.edit(text, reply_markup=markup)
                    else:
                        await callback_query.message.edit("Font size must be between 10 and 100. Try again.")
                    await callback_query.answer()
                except ValueError:
                    await callback_query.message.edit("Invalid number. Please send a number (e.g., 20).")
                    await callback_query.answer()
            except TimeoutError:
                text, markup = create_main_panel(user_id)
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
                        await asyncio.sleep(1)  # Brief delay for better UX
                        text, markup = create_main_panel(user_id)
                        await callback_query.message.edit(text, reply_markup=markup)
                    else:
                        await callback_query.message.edit("Opacity must be between 0 and 100. Try again.")
                    await callback_query.answer()
                except ValueError:
                    await callback_query.message.edit("Invalid number. Please send a number (e.g., 50).")
                    await callback_query.answer()
            except TimeoutError:
                text, markup = create_main_panel(user_id)
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
                await callback_query.answer()
            return

        
        if data == "wm_full_command":
            await callback_query.message.edit(
                'Send me the full watermark command (e.g., -vf "drawtext=text=\'Your Text\':fontsize=24:fontcolor=white:x=10:y=10")\nTimeout: 30 seconds',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            try:
                response = await callback_query.message.chat.ask(
                    "Waiting for your watermark command input...",
                    filters=filters.text,
                    timeout=30
                )
                command = response.text.strip()
                if command.startswith('-vf "drawtext=') and command.endswith('"'):
                    await db.set_watermark(user_id, watermark=command)
                    await callback_query.message.edit(f"Watermark command set to: {command}")
                    await asyncio.sleep(1)
                    text, markup = create_main_panel(user_id)
                    await callback_query.message.edit(text, reply_markup=markup)
                else:
                    await callback_query.message.edit("Invalid command format. Must start with -vf and contain drawtext.")
                await callback_query.answer()
            except TimeoutError:
                text, markup = create_main_panel(user_id)
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
                await callback_query.answer()
            return

        if data == "wm_show":
            command = await build_watermark_command(user_id, settings)
            await callback_query.message.edit(
                f"Your Watermark Command:\n`{command}`\n\n📌**Use** __/Vwatermark__ **to see your current watermark detail**\n📌 **Use** __/Dwatermark__ **To delete your watermark and encode without watermark**",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            await callback_query.answer()
            return

        await callback_query.answer("Unknown callback data.")  # Fallback for unrecognized data

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

    if wm_code:
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
    await db.set_watermark(message.from_user.id, watermark=None)
    await SnowDev.edit("❌ __**Wᴀᴛᴇʀᴍᴀʀᴋ Dᴇʟᴇᴛᴇᴅ**__")
