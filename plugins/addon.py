from pyrogram import Client, filters, enums
from helper.database import db
from helper.utils import CANT_CONFIG_GROUP_MSG
from script import Txt
from asyncio.exceptions import TimeoutError

@Client.on_message((filters.group | filters.private) & filters.command('set_wm'))
async def set_wm(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    if len(message.command) == 1:
        return await message.reply_text("**__Gɪᴠᴇ Tʜᴇ Wᴀᴛᴇʀᴍᴀʀᴋ Cᴏᴅᴇ__\n\nExᴀᴍᴩʟᴇ:- `/set_wm -vf \"drawtext=text='Heloo':fontcolor=white:fontsize=24:x=10:y=10\"`**")

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    wm_code = message.text.split(" ", 1)[1]
    await db.set_watermark(message.from_user.id, watermark=wm_code)
    await SnowDev.edit("✅ __**Wᴀᴛᴇʀᴍᴀʀᴋ Cᴏᴅᴇ Sᴀᴠᴇᴅ**__")


@Client.on_message((filters.group | filters.private) & filters.command('view_wm'))
async def view_wm(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)

    wm_code = await db.get_watermark(message.from_user.id)

    if wm_code:
        await SnowDev.edit(f"✅ <b>Yᴏᴜʀ Cᴜʀʀᴇɴᴛ Wᴀᴛᴇʀᴍᴀʀᴋ Cᴏᴅᴇ ɪs :-</b>\n\n<code>{wm_code}</code>")
    else:
        await SnowDev.edit(f"😔 __**Yᴏᴜ Dᴏɴ'ᴛ Hᴀᴠᴇ Aɴy Wᴀᴛᴇʀᴍᴀʀᴋ**__")


@Client.on_message((filters.group | filters.private) & filters.command('delete_wm'))
async def delete_wm(client, message):
    if not await db.is_user_exist(message.from_user.id):
        await CANT_CONFIG_GROUP_MSG(client, message)
        return

    SnowDev = await message.reply_text(text="**Please Wait...**", reply_to_message_id=message.id)
    await db.set_watermark(message.from_user.id, watermark=None)
    await SnowDev.edit("❌ __**Wᴀᴛᴇʀᴍᴀʀᴋ Dᴇʟᴇᴛᴇᴅ**__")
