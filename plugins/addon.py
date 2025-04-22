from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helper.database import db
from helper.utils import CANT_CONFIG_GROUP_MSG
from script import Txt
import asyncio
from asyncio.exceptions import TimeoutError
import logging
import re

# Set up logging for debugging
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
    # Check if a custom command is set
    custom_command = await db.get_watermark(user_id)
    if custom_command:
        return custom_command  # Return custom command if set

    # Check if logo URL is set
    logo_url = await db.get_logo_url(user_id)
    if logo_url:
        # Logo + Text command
        logo_x = get_position_x(settings['position'])
        logo_y = get_position_y(settings['position'])
        text_x = f"({logo_x}+40)"  # Offset text by 40 pixels to the right
        text_y = logo_y  # Same y-coordinate as logo
        command = (
            f"[1:v]scale=-1:{settings['font_size']}[logo];"
            f"[0:v][logo]overlay={logo_x}:{logo_y}[v1];"
            f"[v1]drawtext=text='{settings['text']}':"
            f"fontcolor={settings['font_color']}:"
            f"fontsize={settings['font_size']}:"
            f"alpha={settings['text_opacity']/100:.2f}:"
            f"x={text_x}:"
            f"y={text_y}[v]"
        )
        full_command = f'-i {logo_url} -filter_complex "{command}" -map "[v]"'
    else:
        # Text-only command
        command = (
            f"drawtext=text='{settings['text']}':"
            f"fontcolor={settings['font_color']}:"
            f"fontsize={settings['font_size']}:"
            f"alpha={settings['text_opacity']/100:.2f}:"
            f"x={get_position_x(settings['position'])}:"
            f"y={get_position_y(settings['position'])}"
        )
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

async def create_main_panel(user_id):  # MODIFIED: Made async
    settings = get_user_settings(user_id)
    text = (
        f"User Watermark Settings:\n"
        f"Text: {settings['text']}\n"
        f"Position: {settings['position'].replace('-', ' ').title()}\n"
        f"Font Colour: {settings['font_color'].title()}\n"
        f"Font Size: {settings['font_size']}\n"
        f"Text Opacity: {settings['text_opacity']}%\n"
    )
    # Show logo status
    logo_url = await db.get_logo_url(user_id)  # MODIFIED: Awaited
    text += f"Logo: {'Set' if logo_url else 'Not Set'}\n"

    # Disable settings if custom command is set
    custom_command = await db.get_watermark(user_id)  # MODIFIED: Awaited
    if custom_command:
        text += "\n⚠️ Custom command is set. Manual settings are disabled."
        buttons = [
            [InlineKeyboardButton("Custom Full Command", callback_data="wm_full_command")],
            [InlineKeyboardButton("Show Command", callback_data="wm_show")]
        ]
    else:
        buttons = [
            [
                InlineKeyboardButton("Text", callback_data="wm_text"),
                InlineKeyboardButton("Position", callback_data="wm_position"),
                InlineKeyboardButton("Colour", callback_data="wm_color")
            ],
            [
                InlineKeyboardButton("Size", callback_data="wm_size"),
                InlineKeyboardButton("Opacity", callback_data="wm_opacity"),
                InlineKeyboardButton("Logo", callback_data="wm_logo")
            ],
            [
                InlineKeyboardButton("Custom Full Command", callback_data="wm_full_command"),
                InlineKeyboardButton("Show Command", callback_data="wm_show")
            ]
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
    text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
    await message.reply(text, reply_markup=markup)

@Client.on_callback_query(filters.regex("^wm_"))
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    settings = get_user_settings(user_id)

    try:
        logger.info(f"Received callback from user {user_id}: {data}")

        # Check if custom command is set to disable manual settings
        custom_command = await db.get_watermark(user_id)
        if custom_command and data in ["wm_text", "wm_position", "wm_color", "wm_size", "wm_opacity", "wm_logo"] or data.startswith("wm_pos_"):
            await callback_query.message.edit(
                "⚠️ Custom command is set. Manual settings are disabled.\nUse 'Custom Full Command' to update or /Dwatermark to reset.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            await callback_query.answer()
            return

        if data == "wm_back":
            text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
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
                text = response.text[:50].strip()
                if text:
                    settings['text'] = text
                    await callback_query.message.edit(f"Text set to: {text}")
                    await asyncio.sleep(1)
                    text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
                    await callback_query.message.edit(text, reply_markup=markup)
                else:
                    await callback_query.message.edit("Text cannot be empty. Try again.")
                await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
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
            text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
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
                await asyncio.sleep(1)
                text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
                await callback_query.message.edit(text, reply_markup=markup)
                await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
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
                        await asyncio.sleep(1)
                        text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
                        await callback_query.message.edit(text, reply_markup=markup)
                    else:
                        await callback_query.message.edit("Font size must be between 10 and 100. Try again.")
                    await callback_query.answer()
                except ValueError:
                    await callback_query.message.edit("Invalid number. Please send a number (e.g., 20).")
                    await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
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
                        await asyncio.sleep(1)
                        text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
                        await callback_query.message.edit(text, reply_markup=markup)
                    else:
                        await callback_query.message.edit("Opacity must be between 0 and 100. Try again.")
                    await callback_query.answer()
                except ValueError:
                    await callback_query.message.edit("Invalid number. Please send a number (e.g., 50).")
                    await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
                await callback_query.answer()
            return

        if data == "wm_logo":
            await callback_query.message.edit(
                "Send me a PNG logo URL (e.g., https://example.com/logo.png)\nMust start with 'https' and end with '.png'\nTimeout: 30 seconds",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            try:
                response = await callback_query.message.chat.ask(
                    "Waiting for your logo URL input...",
                    filters=filters.text,
                    timeout=30
                )
                url = response.text.strip()
                if re.match(r'^https://.*\.png$', url):
                    await db.set_logo_url(user_id, url)
                    await callback_query.message.edit(f"Logo URL set to: {url}")
                    await asyncio.sleep(1)
                    text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
                    await callback_query.message.edit(text, reply_markup=markup)
                else:
                    await callback_query.message.edit("Invalid URL. Must start with 'https' and end with '.png'. Try again.")
                await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
                await callback_query.answer()
            return

        if data == "wm_full_command":
            await callback_query.message.edit(
                'Send me the full watermark command (e.g., -vf "drawtext=text=\'Your Text\':fontsize=24:fontcolor=white:x=10:y=10" or any FFmpeg filter)\nTimeout: 30 seconds',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
            )
            try:
                response = await callback_query.message.chat.ask(
                    "Waiting for your watermark command input...",
                    filters=filters.text,
                    timeout=30
                )
                command = response.text.strip()
                if command:
                    await db.set_watermark(user_id, watermark=command)
                    await callback_query.message.edit(f"Watermark command set to: {command}")
                    await asyncio.sleep(1)
                    text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
                    await callback_query.message.edit(text, reply_markup=markup)
                else:
                    await callback_query.message.edit("Command cannot be empty. Try again.")
                await callback_query.answer()
            except TimeoutError:
                text, markup = await create_main_panel(user_id)  # MODIFIED: Awaited
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

    if wm_code:
        if wm_code.startswith('-vf "drawtext=') or wm_code.startswith('-i '):
            await SnowDev.edit(
                f"Custom Watermark Command:\n`{wm_code}`\n\n"
                f"⚠️ Manual settings are disabled.\n"
                f"**Use** __/Dwatermark__ **To delete Watermark and encode without Watermark**"
            )
        else:
            logo_url = await db.get_logo_url(user_id)
            await SnowDev.edit(
                f"User Watermark Settings:\n"
                f"Text: {settings['text']}\n"
                f"Position: {settings['position'].replace('-', ' ').title()}\n"
                f"Font Colour: {settings['font_color'].title()}\n"
                f"Font Size: {settings['font_size']}\n"
                f"Text Opacity: {settings['text_opacity']}%\n"
                f"Logo: {'Set' if logo_url else 'Not Set'}\n"
                f"**Use** __/Dwatermark__ **To delete Watermark and encode without Watermark**"
            )
    else:
        await SnowDev.edit(f"😔 __**Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Wᴀᴛᴇʀᴍᴀʀᴋ**__")

@Client.on_message((filters.group | filters.private) & filters.command('Dwatermark'))
async def delete_wm(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    user_id = message.from_user.id
    await db.set_watermark(user_id, watermark=None)
    await db.delete_logo_url(user_id)
    user_settings[user_id] = DEFAULT_SETTINGS.copy()
    await SnowDev.edit("❌ __**Wᴀᴛᴇʀᴍᴀʀᴋ Dᴇʟᴇᴛᴇᴅ**__")
