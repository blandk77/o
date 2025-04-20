from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
import logging, os, logging.config
from datetime import datetime
from pytz import timezone
from pyrogram.errors import AuthKeyUnregistered

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="EncoderBot",
            in_memory=True,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins={'root': 'plugins'}
        )
        self.UPLOAD_LIMIT = 2 * 1024 * 1024 * 1024  # Default: 2GB in bytes

    async def check_premium_status(self):
        """Check if OWNER_STRING is premium and set UPLOAD_LIMIT."""
        if not Config.OWNER_STRING:
            logging.info("No OWNER_STRING provided. Default upload limit: 2GB")
            self.UPLOAD_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB in bytes
            return

        try:
            # Initialize a temporary client with OWNER_STRING
            app = Client("temp_session", session_string=Config.OWNER_STRING)
            async with app:
                me = await app.get_me()
                is_premium = getattr(me, "is_premium", False)

                if is_premium:
                    self.UPLOAD_LIMIT = 4 * 1024 * 1024 * 1024  # 4GB in bytes
                    logging.info("Premium account detected for OWNER_STRING. Upload limit: 4GB")
                else:
                    self.UPLOAD_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB in bytes
                    logging.info("Non-premium account for OWNER_STRING. Upload limit: 2GB")

        except AuthKeyUnregistered:
            logging.error("Invalid OWNER_STRING. Default upload limit: 2GB")
            self.UPLOAD_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB in bytes
        except Exception as e:
            logging.error(f"Error checking OWNER_STRING premium status: {e}. Default upload limit: 2GB")
            self.UPLOAD_LIMIT = 2 * 1024 * 1024 * 1024  # 2GB in bytes

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username
        logging.info(f"✅ {me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}. ✅")

        # Check premium status and set upload limit
        await self.check_premium_status()

        await self.send_message(Config.ADMIN, f"**__{me.first_name}  Iꜱ Sᴛᴀʀᴛᴇᴅ.....✨️__**")

        if Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date = curr.strftime('%d %B, %Y')
                time = curr.strftime('%I:%M:%S %p')
                await self.send_message(
                    Config.LOG_CHANNEL,
                    f"**__{me.mention} Iꜱ Rᴇsᴛᴀʀᴛᴇᴅ !!**\n\n📅 Dᴀᴛᴇ : `{date}`\n⏰ Tɪᴍᴇ : `{time}`\n🌐 Tɪᴍᴇᴢᴏɴᴇ : `Asia/Kolkata`\n\n🉐 Vᴇʀsɪᴏɴ : `v{__version__} (Layer {layer})`</b>"
                )
            except:
                print("Pʟᴇᴀꜱᴇ Mᴀᴋᴇ Tʜɪꜱ Iꜱ Aᴅᴍɪɴ Iɴ Yᴏᴜʀ Lᴏɢ Cʜᴀɴɴᴇʟ")

    async def stop(self, *args):
        await super().stop()
        logging.info("Bot Stopped ⛔")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
