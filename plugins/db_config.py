from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
from helper.database import db
from helper.utils import CANT_CONFIG_GROUP_MSG
from script import Txt
from asyncio.exceptions import TimeoutError


# Default watermark settings (used if no DB entry exists)
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

@Client.on_message((filters.group | filters.private) & filters.command('set_caption'))
async def add_caption(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    if len(message.command) == 1:
        return await message.reply_text("**__Gɪᴠᴇ Tʜᴇ Cᴀᴩᴛɪᴏɴ__\n\nExᴀᴍᴩʟᴇ:- `/set_caption {filename}\n\n💾 Sɪᴢᴇ: {filesize}\n\n⏰ Dᴜʀᴀᴛɪᴏɴ: {duration}`**")

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    caption = message.text.split(" ", 1)[1]
    await db.set_caption(message.from_user.id, caption=caption)
    await message.reply_text("__**✅ Cᴀᴩᴛɪᴏɴ Sᴀᴠᴇᴅ**__")


@Client.on_message((filters.group | filters.private) & filters.command('del_caption'))
async def delete_caption(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return


    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    caption = await db.get_caption(message.from_user.id)
    if not caption:
        return await SnowDev.edit("__**😔 Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Cᴀᴩᴛɪᴏɴ**__")
    await db.set_caption(message.from_user.id, caption=None)
    await SnowDev.edit("__**❌️ Cᴀᴩᴛɪᴏɴ Dᴇʟᴇᴛᴇᴅ**__")


@Client.on_message((filters.group | filters.private) & filters.command(['see_caption', 'view_caption']))
async def see_caption(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    caption = await db.get_caption(message.from_user.id)
    if caption:
        await message.reply_text(f"**Yᴏᴜ'ʀᴇ Cᴀᴩᴛɪᴏɴ:-**\n\n`{caption}`")
    else:
        await message.reply_text("__**😔 Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Cᴀᴩᴛɪᴏɴ**__")


@Client.on_message((filters.group | filters.private) & filters.command(['view_thumb', 'viewthumb']))
async def viewthumb(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    thumb = await db.get_thumbnail(message.from_user.id)
    if thumb:
        await SnowDev.delete()
        await client.send_photo(chat_id=message.chat.id, photo=thumb, reply_to_message_id=message.id)
    else:
        await SnowDev.edit("😔 __**Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Tʜᴜᴍʙɴᴀɪʟ**__")


@Client.on_message((filters.group | filters.private) & filters.command(['del_thumb', 'delthumb']))
async def removethumb(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    await db.set_thumbnail(message.from_user.id, thumbnail=None)
    await SnowDev.edit("❌️ __**Tʜᴜᴍʙɴᴀɪʟ Dᴇʟᴇᴛᴇᴅ**__")


@Client.on_message((filters.group | filters.private) & filters.photo)
async def addthumbs(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    await db.set_thumbnail(message.from_user.id, message.photo.file_id)
    await SnowDev.edit("✅️ __**Tʜᴜᴍʙɴᴀɪʟ Sᴀᴠᴇᴅ**__")
    

@Client.on_message((filters.group | filters.private) & filters.command(['set_ffmpeg', 'setffmpeg']))
async def set_ffmpeg(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return
    try:
        ffmpeg = await client.ask(text=Txt.SEND_FFMPEG_CODE, chat_id=message.chat.id,
                            user_id=message.from_user.id, filters=filters.text, timeout=30, disable_web_page_preview=True)
    except TimeoutError:
        await message.reply_text("Error!!\n\nRequest timed out.\nRestart by using /set_ffmpeg", reply_to_message_id=message.id)
        return
        
    await db.set_ffmpegcode(message.from_user.id, ffmpeg.text)
    await message.reply_text("✅ __**Fғᴍᴘᴇɢ Cᴏᴅᴇ Sᴀᴠᴇᴅ**__", reply_to_message_id=message.id)


@Client.on_message((filters.group | filters.private) & filters.command(['see_ffmpeg', 'seeffmpeg']))
async def see_ffmpeg(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)

    ffmpeg = await db.get_ffmpegcode(message.from_user.id)
    
    if ffmpeg:
        await SnowDev.edit(f"✅ <b>Yᴏᴜʀ Cᴜʀʀᴇɴᴛ Fғᴍᴘᴇɢ Cᴏᴅᴇ ɪs :-</b>\n\n<code>{ffmpeg}</code>")
    else:
        await SnowDev.edit(f"😔 __**Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Fғᴍᴘᴇɢ Cᴏᴅᴇ**__")


@Client.on_message((filters.group | filters.private) & filters.command(['del_ffmpeg', 'delffmpeg']))
async def del_ffmpeg(client, message):

    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    await db.set_ffmpegcode(message.from_user.id, None)
    await SnowDev.edit("❌ __**Fғᴍᴘᴇɢ Cᴏᴅᴇ Dᴇʟᴇᴛᴇᴅ**__")


@Client.on_message((filters.group | filters.private) & filters.command('set_metadata'))
async def set_metadata(client, message):
    
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return
    
    try:
        metadata = await client.ask(text=Txt.SEND_METADATA, chat_id=message.chat.id, user_id=message.from_user.id, filters=filters.text, timeout=30)

    except TimeoutError:
        await message.reply_text("Error!!\n\nRequest timed out.\nRestart by using /set_ffmpeg", reply_to_message_id= metadata.id)
        return
    
    await db.set_metadata(message.from_user.id, metadata=metadata.text)
    await message.reply_text("✅ __**Mᴇᴛᴀᴅᴀᴛᴀ Cᴏᴅᴇ Sᴀᴠᴇᴅ**__", reply_to_message_id=message.id)
    
    
@Client.on_message((filters.group | filters.private) & filters.command('see_metadata'))
async def see_metadata(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return
    
    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)

    metadata = await db.get_metadata(message.from_user.id)
    
    if metadata:
        await SnowDev.edit(f"✅ <b>Yᴏᴜʀ Cᴜʀʀᴇɴᴛ Mᴇᴛᴀᴅᴀᴛᴀ Cᴏᴅᴇ ɪs :-</b>\n\n<code>{metadata}</code>")
    else:
        await SnowDev.edit(f"😔 __**Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Mᴇᴛᴀᴅᴀᴛᴀ Cᴏᴅᴇ**__")

async def get_user_settings(db, user_id):
    # Try to get from DB first
    settings = await db.get_watermark(user_id)
    if settings is None:
        settings = DEFAULT_SETTINGS.copy()
    return settings

async def save_user_settings(db, user_id, settings):
    # Save to MongoDB
    await db.set_watermark(user_id, watermark=settings)

def build_watermark_command(settings):
    return (f"drawtext=text='{settings['text']}':"
            f"fontcolor={settings['font_color']}:"
            f"fontsize={settings['font_size']}:"
            f"alpha={settings['text_opacity']/100:.2f}:"
            f"x={get_position_x(settings['position'])}:"
            f"y={get_position_y(settings['position'])}")

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

def create_main_panel(settings):
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
            InlineKeyboardButton("Opacity", callback_data="wm_opacity")
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
    settings = await get_user_settings(db, user_id)
    text, markup = create_main_panel(settings)
    await message.reply(text, reply_markup=markup)

@Client.on_callback_query(filters.regex("^wm_"))
async def handle_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    settings = await get_user_settings(db, user_id)

    if data == "wm_back":
        text, markup = create_main_panel(settings)
        await callback_query.message.edit(text, reply_markup=markup)
        return

    if data == "wm_text":
        await callback_query.message.edit(
            "Send me a text to add Watermark\nTimeout: 30 seconds",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
        )
        
        async def wait_for_text():
            try:
                response = await client.wait_for_message(
                    user_id=user_id,
                    timeout=30,
                    filters=filters.text & filters.user(user_id)
                )
                settings['text'] = response.text[:50]  # Limit text length
                await save_user_settings(db, user_id, settings)
                text, markup = create_main_panel(settings)
                await callback_query.message.edit(text, reply_markup=markup)
            except asyncio.TimeoutError:
                text, markup = create_main_panel(settings)
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
        
        asyncio.create_task(wait_for_text())
        return

    if data == "wm_position":
        text, markup = create_position_panel()
        await callback_query.message.edit(text, reply_markup=markup)
        return

    if data.startswith("wm_pos_"):
        position = data[7:]
        settings['position'] = position
        await save_user_settings(db, user_id, settings)
        text, markup = create_main_panel(settings)
        await callback_query.message.edit(text, reply_markup=markup)
        return

    if data == "wm_color":
        await callback_query.message.edit(
            "Send me a color name (e.g., red, blue, white)\nTimeout: 30 seconds",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
        )
        
        async def wait_for_color():
            try:
                response = await client.wait_for_message(
                    user_id=user_id,
                    timeout=30,
                    filters=filters.text & filters.user(user_id)
                )
                settings['font_color'] = response.text.lower()
                await save_user_settings(db, user_id, settings)
                text, markup = create_main_panel(settings)
                await callback_query.message.edit(text, reply_markup=markup)
            except asyncio.TimeoutError:
                text, markup = create_main_panel(settings)
                await callback_query.message.edit("Timeout! Back to main panel.", reply_markup=markup)
        
        asyncio.create_task(wait_for_color())
        return

    if data == "wm_size":
        await callback_query.message.edit(
            "Send me a font size (number between 10-100)\nTimeout: 30 seconds",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
        )
        
        async def wait_for_size():
            try:
                response = await client.wait_for_message(
                    user_id=user_id,
                    timeout=30,
                    filters=filters.text & filters.user(user_id)
                )
                size = int(response.text)
                if 10 <= size <= 100:
                    settings['font_size'] = size
                    await save_user_settings(db, user_id, settings)
                text, markup = create_main_panel(settings)
                await callback_query.message.edit(text, reply_markup=markup)
            except (ValueError, asyncio.TimeoutError):
                text, markup = create_main_panel(settings)
                await callback_query.message.edit("Invalid or timeout! Back to main panel.", reply_markup=markup)
        
        asyncio.create_task(wait_for_size())
        return

    if data == "wm_opacity":
        await callback_query.message.edit(
            "Send me opacity (number between 0-100)\nTimeout: 30 seconds",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
        )
        
        async def wait_for_opacity():
            try:
                response = await client.wait_for_message(
                    user_id=user_id,
                    timeout=30,
                    filters=filters.text & filters.user(user_id)
                )
                opacity = int(response.text)
                if 0 <= opacity <= 100:
                    settings['text_opacity'] = opacity
                    await save_user_settings(db, user_id, settings)
                text, markup = create_main_panel(settings)
                await callback_query.message.edit(text, reply_markup=markup)
            except (ValueError, asyncio.TimeoutError):
                text, markup = create_main_panel(settings)
                await callback_query.message.edit("Invalid or timeout! Back to main panel.", reply_markup=markup)
        
        asyncio.create_task(wait_for_opacity())
        return

    if data == "wm_show":
        Watermark = build_watermark_command(settings)
        # Save the generated watermark command to MongoDB
        await db.set_watermark(user_id, watermark=Watermark)
        await callback_query.message.edit(
            f"Watermark Command:\n`{Watermark}`\n\nSaved to database!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="wm_back")]])
        )
        return

    await callback_query.answer()


@Client.on_message((filters.group | filters.private) & filters.command('see_wm'))
async def see_watermark(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    watermark = await db.get_watermark(message.from_user.id)
    if watermark:
        await message.reply_text(f"**Yᴏᴜʀ Wᴀᴛᴇʀᴍᴀʀᴋ:-**\n\n`{watermark}`")
    else:
        await message.reply_text("__**😔 Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Wᴀᴛᴇʀᴍᴀʀᴋ**__")


@Client.on_message((filters.group | filters.private) & filters.command('del_wm'))
async def delete_watermark(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    watermark = await db.get_watermark(message.from_user.id)
    if not watermark:
        return await SnowDev.edit("__**😔 Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Wᴀᴛᴇʀᴍᴀʀᴋ**__")
    await db.delete_watermark(message.from_user.id)
    await SnowDev.edit("__**❌ Wᴀᴛᴇʀᴍᴀʀᴋ Dᴇʟᴇᴛᴇᴅ**__")
