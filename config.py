import os, time, re

id_pattern = re.compile(r'^.\d+$') 


class Config(object):
    # pyro client config
    API_ID    = os.environ.get("API_ID", "27394279")  # ⚠️ Required
    API_HASH  = os.environ.get("API_HASH", "90a9aa4c31afa3750da5fd686c410851") # ⚠️ Required
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "7747196334:AAE6fjbVnVmDpjMcPSFWayIFK3uyNIRBTPM") # ⚠️ Required
    FORCE_SUB = os.environ.get('FORCE_SUB', 'The_TGguy') # ⚠️ Required
    AUTH_CHANNEL = int(FORCE_SUB) if FORCE_SUB and id_pattern.search(
    FORCE_SUB) else None
   
    # database config
    DB_URL  = os.environ.get("DB_URL", "mongodb+srv://telegramguy21:tnkIwvbNkJ5U3fZ7@botsuse.bpgag.mongodb.net/?retryWrites=true&w=majority&appName=Botsuse")  # ⚠️ Required
    DB_NAME  = os.environ.get("DB_NAME","SnowEnc") 

    # ID's
    ADMIN = int(os.environ.get("ADMIN", "7465574522")) # ⚠️ Required
    LOG_CHANNEL = int(os.environ.get('LOG_CHANNEL', '-1002288135729')) # ⚠️ Required
    DUMP_CHANNEL = int(os.environ.get('DUMP_CHANNEL', '-1002288135729'))

    #Nothing to fill in this line
    BOT_UPTIME = BOT_UPTIME  = time.time()

    #Image to show in the Start command 
    START_PIC = os.environ.get("START_PIC", "https://graph.org/file/15e82d7e665eccc8bd9c5.jpg")
    
    #Fill if you want 4gb upload, else leave blank for 2gb upload 
    OWNER_STRING = os.environ.get("OWNER_STRING", "")

    #start command buttons/credits
    UPDATES_BTN = os.environ.get("UPDATES_BTN", "BIDHAANBOTS") 
    DEV_BTN = os.environ.get("DEV_BTN", "BIG_FiiSH")

    # wes response configuration     
    WEBHOOK = bool(os.environ.get("WEBHOOK", True))
    PORT = int(os.environ.get("PORT", "8080"))


    caption = """
🚀 **File Successfully Processed!** 🌟

📂 **File Name:** `{}` 📝✨
📏 **Original Size:** `{}` 📦📏
🗜 **Encoded Size:** `{}` 🔐💾
📉 **Compression:** `{}` 📊🔽

⏬ **Downloaded in:** `{}` ⏳📥
⚙️ **Encoded in:** `{}` ⚡🎛
☁️ **Uploaded in:** `{}` 🚀📤

🔥 **Your file is compressed, optimized, and ready to go!** 😎✨

"""

#Token Verification 
VERIFY_EXPIRE = os.environ.get('VERIFY_EXPIRE', 0) # VERIFY EXPIRE TIME IN SECONDS. LIKE:- 0 (ZERO) TO OFF VERIFICATION 
SHORTLINK_SITE = os.environ.get('SHORTLINK_SITE', 'linkmonetizer.in') # YOUR SHORTLINK URL LIKE:- site.com
SHORTLINK_API = os.environ.get('SHORTLINK_API', 'bf35b33b841943cdce510413393f35a9ff0bb558') # YOUR SHORTLINK API LIKE:- ma82owowjd9hw6_js7
PREMIUM_USERS = list(map(int, os.environ.get('PREMIUM_USERS', '1705634892').split()))
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'Verified') #For Token verification 
