import os
import asyncio
import json
import logging
import re
from threading import Thread
from flask import Flask
from pyrogram import Client, filters, enums, idle
from pyrogram.errors import UserNotParticipant, PeerIdInvalid, ChannelInvalid

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FAKE WEBSITE FOR RENDER ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "⚡ ANYSNAP Bot is Running Successfully!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- CONFIGURATION ---
API_ID = 37314366
API_HASH = "bd4c934697e7e91942ac911a5a287b46"

# --- 🔐 SESSION STRING ---
SESSION_STRING = "BQI5Xz4ASfzypOgrMRV3KOAURi3vOstv3Lsgw2OCyTVS1OUxF288qtA55BP6oiRZ60Dp43i1TIDGXZXVJ71__uGWDhLf9Ic21YoxYASSlUavNlfezamNRrNNdcEr6gcU9oxy2YUNUgK3r1ugR_gv0VSvlKn39nehnw5BKQ-mnVAhVbcayb_8YW8o5NpGA7jIEalfnH3-aUmFYk2mvEwOnx8WWixpPOfkVb8gWx7F2DVcGCgTq-jejGlv5aopkqb-QrFIFDM2Y4z-qrA6GoTpv1oQJ_KTjX3NKb-i36Uw1zgBMY_JPi2qjK8_iVTaepFTFhBDVnZ2jAUbGMcjh9BJW1oAAKcLRgAAAAH99e3RAA"

TARGET_BOT = "Random_insight69_bot"
NEW_FOOTER = "⚡ Designed & Powered by @Xldaredevil"

# --- 🔐 SECURITY SETTINGS ---
ALLOWED_GROUPS = [-1003797378635] 

FSUB_CONFIG = [
    {"chat_id": -1003797378635, "link": "https://t.me/+GOPNq4E5vONlN2Jl"},  # Group
    {"chat_id": "Daredevilxlhub", "link": "https://t.me/Daredevilxlhub"}    # Channel
]

app = Client("anysnap_secure_bot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

# --- HELPER: CHECK IF USER JOINED ---
async def check_user_joined(client, user_id):
    missing = False
    for ch in FSUB_CONFIG:
        try:
            member = await client.get_chat_member(ch["chat_id"], user_id)
            if member.status in [enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.BANNED]:
                missing = True
                break
        except UserNotParticipant:
            missing = True
            break
        except (PeerIdInvalid, ChannelInvalid, KeyError):
            pass
        except Exception:
            pass 
    return not missing 

# --- DASHBOARD ---
@app.on_message(filters.command(["start", "help", "menu"], prefixes="/") & (filters.private | filters.chat(ALLOWED_GROUPS)))
async def show_dashboard(client, message):
    try:
        if not await check_user_joined(client, message.from_user.id):
            buttons_text = ""
            for ch in FSUB_CONFIG:
                buttons_text += f"➡️ **[Join Channel]({ch['link']})**\n"

            return await message.reply_text(
                "🚫 **Access Denied!**\n\n"
                "Bot use karne ke liye pehle niche diye gaye channels join karein:\n\n"
                f"{buttons_text}\n"
                "__Join karne ke baad dubara /start dabayein.__",
                disable_web_page_preview=True
            )

        text = (
            "📖 **ANYSNAP BOT DASHBOARD**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "📢 **Channel:** [Join Here](https://t.me/Daredevilxlhub)\n"
            "👥 **Group:** [Join Here](https://t.me/+GOPNq4E5vONlN2Jl)\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 **Lookup Services:**\n"
            "📱 `/num [number]`\n🚗 `/vehicle [plate]`\n🆔 `/aadhar [uid]`\n"
            "👨‍👩‍👧‍👦 `/familyinfo [uid]`\n🔗 `/vnum [plate]`\n💸 `/fam [id]`\n📨 `/sms [number]`\n\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚡ **Designed & Powered by @Xldaredevil**"
        )
        await message.reply_text(text, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")

# --- MAIN LOGIC ---
@app.on_message(filters.command(["num", "vehicle", "aadhar", "familyinfo", "vnum", "fam", "sms"], prefixes="/") & (filters.private | filters.chat(ALLOWED_GROUPS)))
async def process_request(client, message):

    try:
        if not await check_user_joined(client, message.from_user.id):
            buttons_text = ""
            for ch in FSUB_CONFIG:
                buttons_text += f"➡️ **[Join Channel]({ch['link']})**\n"

            return await message.reply_text(
                "🚫 **Access Denied!**\n\n"
                "Result dekhne ke liye pehle join karein:\n\n"
                f"{buttons_text}\n"
                f"__Join karne ke baad wapas `/{message.command[0]}` bhejein.__",
                disable_web_page_preview=True
            )

        if len(message.command) < 2:
            return await message.reply_text(f"❌ **Data Missing!**\nUsage: `/{message.command[0]} <value>`")

        status_msg = await message.reply_text(f"🔍 **Searching via ANYSNAP...**")

        try:
            sent_req = await client.send_message(TARGET_BOT, message.text)
        except PeerIdInvalid:
             await status_msg.edit("❌ **Error:** Target Bot ID invalid. Userbot must start @Random_insight69_bot first.")
             return
        except Exception as e:
            await status_msg.edit(f"❌ **Request Error:** {e}")
            return

        target_response = None

        # --- SMART WAIT LOOP ---
        for attempt in range(30): 
            await asyncio.sleep(2) 
            try:
                async for log in client.get_chat_history(TARGET_BOT, limit=1):
                    if log.id == sent_req.id: continue

                    text_content = (log.text or log.caption or "").lower()

                    ignore_words = [
                        "wait", "processing", "searching", "scanning", 
                        "generating", "loading", "checking", 
                        "looking up", "uploading", "sending file", 
                        "attaching", "sending"
                    ]

                    if any(word in text_content for word in ignore_words) and not log.document:
                        if f"Attempt {attempt+1}" not in status_msg.text:
                            await status_msg.edit(f"⏳ **Fetching Data... (Attempt {attempt+1})**")
                        continue 

                    if log.document or "{" in text_content or "success" in text_content:
                        target_response = log
                        break

                    target_response = log
                    break

            except Exception as e:
                logger.error(f"Error fetching history: {e}")

            if target_response: break

        if not target_response:
            await status_msg.edit("❌ **No Data Found**")
            return

        # --- DATA HANDLING ---
        raw_text = ""
        if target_response.document:
            await status_msg.edit("📂 **Downloading Result File...**")
            try:
                file_path = await client.download_media(target_response)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_text = f.read()
                os.remove(file_path)
            except Exception as e:
                await status_msg.edit(f"❌ **File Error:** {e}")
                return
        elif target_response.text:
            raw_text = target_response.text
        elif target_response.caption:
            raw_text = target_response.caption

        if not raw_text or len(raw_text.strip()) < 2:
            await status_msg.edit("❌ **No Data Found**")
            return

        # --- 🔥 AGGRESSIVE CLEANING ---
        # 1. Remove escaped version (Slash wala)
        raw_text = raw_text.replace(r"⚡ Designed & Powered by @DuXxZx\_info", "")
        # 2. Remove normal version
        raw_text = raw_text.replace("⚡ Designed & Powered by @DuXxZx_info", "")
        # 3. Remove just the username (Backup)
        raw_text = raw_text.replace(r"@DuXxZx\_info", "").replace("@DuXxZx_info", "")
        # 4. Remove empty separator lines if left behind
        raw_text = raw_text.replace("====================\n\n", "====================\n")

        # JSON Parsing
        final_output = raw_text 
        try:
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)

            if json_match:
                parsed_data = json.loads(json_match.group(0))
                results = []
                if "data" in parsed_data:
                    data_part = parsed_data["data"]
                    if isinstance(data_part, list) and len(data_part) > 0:
                        if "results" in data_part[0]:
                            results = data_part[0]["results"]
                        else:
                            results = data_part
                    elif isinstance(data_part, dict):
                        if "results" in data_part:
                            results = data_part["results"]
                        else:
                            results = [data_part]
                elif "results" in parsed_data:
                    results = parsed_data["results"]
                else:
                    results = parsed_data

                final_output = json.dumps(results, indent=4, ensure_ascii=False)
        except Exception:
            pass

        # --- SENDING RESULT & AUTO DELETE ---
        formatted_msg = f"```json\n{final_output}\n```\n\n{NEW_FOOTER}"
        await status_msg.delete()

        sent_messages_list = [] 

        if len(formatted_msg) > 4000:
            chunks = [formatted_msg[i:i+4000] for i in range(0, len(formatted_msg), 4000)]
            for chunk in chunks:
                msg = await message.reply_text(chunk)
                sent_messages_list.append(msg)
                await asyncio.sleep(1) 
        else:
            msg = await message.reply_text(formatted_msg)
            sent_messages_list.append(msg)

        # ⏳ AUTO DELETE (60s)
        await asyncio.sleep(60)
        for m in sent_messages_list:
            try:
                await m.delete()
            except Exception:
                pass

    except Exception as e:
        try:
            await status_msg.edit(f"❌ **Error:** {str(e)}")
        except:
            pass

# --- START SERVER & BOT ---
async def start_bot():
    print("🚀 Starting Web Server...")
    keep_alive() 
    print("🚀 Starting Pyrogram Client...")
    await app.start()
    print("✅ Bot is Online!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    # --- FIX FOR PYTHON 3.10+ AND RENDER ---
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_until_complete(start_bot())
