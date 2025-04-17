import string, random, os, sys
from urllib.parse import quote
from time import time
from urllib3 import disable_warnings
from pyrogram import Client, filters 
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

from cloudscraper import create_scraper
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config, COLLECTION_NAME, VERIFY_EXPIRE, SHORTLINK_API, SHORTLINK_SITE, PREMIUM_USERS, DUAL_PROTECTION

DATABASE_URL = Config.DB_URI

verify_dict = {}
missing=[v for v in ["COLLECTION_NAME", "SHORTLINK_SITE", "SHORTLINK_API"] if not v]; sys.exit(f"Missing: {', '.join(missing)}") if missing else None

async def token_system_filter(_, __, message):
    uid = message.from_user.id
    if not VERIFY_EXPIRE or uid in PREMIUM_USERS:
        return False
    if message.text:
        cmd = message.text.split()
        if len(cmd) == 2:
            data = cmd[1]
            if data.startswith("verify"):
                return True
    isVerified = await is_user_verified(uid)
    if isVerified:
        return False
    return True 
    
@Client.on_message((filters.private|filters.group) & filters.incoming & filters.create(token_system_filter) & ~filters.bot)
async def global_verify_function(client, message):
    if message.text:
        cmd = message.text.split()
        if len(cmd) == 2:
            data = cmd[1]
            if data.startswith("verify"):
                await validate_token(client, message, data)
                return
    await send_verification(client, message)
        
class VerifyDB():
    def __init__(self):
        self._dbclient = AsyncIOMotorClient(DATABASE_URL)
        self._db = self._dbclient['verify-db']
        self._verifydb = self._db[COLLECTION_NAME]  

    async def get_verify_status(self, user_id):
        if status := await self._verifydb.find_one({'id': user_id}):
            return status.get('verify_status', 0)
        return 0

    async def update_verify_status(self, user_id):
        await self._verifydb.update_one({'id': user_id}, {'$set': {'verify_status': time()}}, upsert=True)

verifydb = VerifyDB()

async def is_user_verified(user_id):
    if not VERIFY_EXPIRE:
        return True
    isveri = await verifydb.get_verify_status(user_id)
    if not isveri or (time() - isveri) >= float(VERIFY_EXPIRE):
        return False
    return True    
    
async def send_verification(client, message, text=None, buttons=None):
    username = (await client.get_me()).username
    if done := await is_user_verified(message.from_user.id):
        text = f'<b>Hi 👋 {message.from_user.mention},\nYou Are Already Verified Enjoy 😄</b>'
    else:
        verify_token = await get_verify_token(client, message.from_user.id, f"https://telegram.me/{username}?start=")
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton('Get Token', url=verify_token)]
        ])
    if not text:
        vtext = f"""<b>Hi 👋 {message.from_user.mention}, 
<blockquote expandable>\n𝙺𝚒𝚗𝚍𝚕𝚢 𝚟𝚎𝚛𝚒𝚏𝚢 𝚢𝚘𝚞𝚛𝚜𝚎𝚕𝚏 𝚝𝚘 𝚞𝚜𝚎 𝚖𝚎!! 
𝚃𝚑𝚒𝚜 𝚒𝚜 𝚝𝚘 𝚊𝚟𝚘𝚒𝚍 𝚜𝚙𝚊𝚖 𝚘𝚗 𝚝𝚑𝚎 𝚋𝚘𝚝 𝚊𝚗𝚍 𝚐𝚎𝚝 𝚖𝚘𝚗𝚎𝚢 𝚝𝚘 𝚛𝚞𝚗 𝚝𝚑𝚎 𝚋𝚘𝚝, 𝚠𝚎 𝚑𝚘𝚙𝚎 𝚢𝚘𝚞 𝚝𝚑𝚊𝚝 𝚢𝚘𝚞 𝚠𝚒𝚕𝚕 𝚞𝚗𝚍𝚎𝚛𝚜𝚝𝚊𝚗𝚍 𝚊𝚗𝚍 𝚑𝚎𝚕𝚙 𝚞𝚜! 𝙸𝚝 𝚠𝚒𝚕𝚕 𝚘𝚗𝚕𝚢 𝚝𝚊𝚔𝚎 𝟸 𝚖𝚒𝚗𝚞𝚝𝚎𝚜 𝚝𝚘 𝚌𝚘𝚖𝚙𝚕𝚎𝚝𝚎 𝚒𝚝.
         ㅤㅤㅤㅤㅤ   - Thank You 
\nValidity: {get_readable_time(VERIFY_EXPIRE)}</b>"""
    message = message if isinstance(message, Message) else message.message
    await client.send_message(
        chat_id=message.chat.id,
        text=vtext,
        reply_markup=buttons,
        reply_to_message_id=message.id,
    )
 
async def get_verify_token(bot, userid, link):
    vdict = verify_dict.setdefault(userid, {})
    short_url = vdict.get('short_url')
    if not short_url:
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=9))
        long_link = f"{link}verify-{userid}-{token}"
        short_url = await get_short_url(long_link)
        if DUAL_PROTECTION:
            short_url = await Protection_url(short_url)
        vdict.update({'token': token, 'short_url': short_url})
    return short_url

async def get_short_url(longurl, shortener_site = SHORTLINK_SITE, shortener_api = SHORTLINK_API):
    cget = create_scraper().request
    disable_warnings()
    try:
        url = f'https://{shortener_site}/api'
        params = {'api': shortener_api,
                  'url': longurl,
                  'format': 'text',
                 }
        res = cget('GET', url, params=params)
        if res.status_code == 200 and res.text:
            return res.text
        else:
            params['format'] = 'json'
            res = cget('GET', url, params=params)
            res = res.json()
            if res.status_code == 200:
                return res.get('shortenedUrl', long_url)
    except Exception as e:
        print(e)
        return long_link

async def Protection_url(short_url):
    encoded_url = "".join(chr((ord(char) + 5) % 256) for char in short_url)
    placeholder_link = "https://black-dot-redirect.vercel.app/decode?url="
    return f"{placeholder_link}{quote(encoded_url)}"

async def validate_token(client, message, data):
    user_id = message.from_user.id
    vdict = verify_dict.setdefault(user_id, {})
    dict_token = vdict.get('token', None)
    if await is_user_verified(user_id):
        return await message.reply("<b>Sɪʀ, Yᴏᴜ Aʀᴇ Aʟʀᴇᴀᴅʏ Vᴇʀɪғɪᴇᴅ 🤓...</b>")
    if not dict_token:
        return await send_verification(client, message, text="<b>Tʜᴀᴛ's Nᴏᴛ Yᴏᴜʀ Vᴇʀɪғʏ Tᴏᴋᴇɴ 🥲...\n\n\nTᴀᴘ Oɴ Vᴇʀɪғʏ Tᴏ Gᴇɴᴇʀᴀᴛᴇ Yᴏᴜʀs...</b>")  
    _, uid, token = data.split("-")
    if uid != str(user_id):
        return await send_verification(client, message, text="<b>Vᴇʀɪғʏ Tᴏᴋᴇɴ Dɪᴅ Nᴏᴛ Mᴀᴛᴄʜᴇᴅ 😕...\n\n\nTᴀᴘ Oɴ Vᴇʀɪғʏ Tᴏ Gᴇɴᴇʀᴀᴛᴇ Aɢᴀɪɴ...</b>")
    elif dict_token != token:
        return await send_verification(client, message, text="<b>Iɴᴠᴀʟɪᴅ Oʀ Exᴘɪʀᴇᴅ Tᴏᴋᴇɴ 🔗...</b>")
    verify_dict.pop(user_id, None)
    await verifydb.update_verify_status(user_id)
    await client.send_message(chat_id=message.from_user.id,
                            text=f'<b>Wᴇʟᴄᴏᴍᴇ Bᴀᴄᴋ 😁, Nᴏᴡ Yᴏᴜ Cᴀɴ Usᴇ Mᴇ Fᴏʀ {get_readable_time(VERIFY_EXPIRE)}.\n\n\nEɴᴊᴏʏʏʏ...❤️</b>',
                            reply_to_message_id=message.id,
                            )

def get_readable_time(seconds):
    periods = [('ᴅ', 86400), ('ʜ', 3600), ('ᴍ', 60), ('s', 1)]
    result = ''
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result += f'{int(period_value)}{period_name}'
    return result
