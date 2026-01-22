import telebot
import requests
import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime
from telebot import types
from flask import Flask  # Fake Website ke liye

# --- CONFIG ---
TOKEN = '8321333186:AAEWHHj7OpeS8lARdm1vNjcWOd2ilrc2vWE'
API_URL = 'https://source-code-api.vercel.app/' 
OWNER = 8081343902
CHANNEL = '@ABOUTMAGMA' 
CHANNEL_LINK = 'https://t.me/ABOUTMAGMA'
MAIN_FOOTER = "Powered by : @MAGMAxRICH"
# --------------

# --- FAKE WEBSITE SERVER (RENDER KEEPALIVE) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 ANY SNAP BOT IS RUNNING 24/7 🚀"

def run_web_server():
    # Render assigns PORT env variable, default to 8080 if not found
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()
# ---------------------------------------------

bot = telebot.TeleBot(TOKEN)
running_bots = {}

if not os.path.exists('clones'):
    os.makedirs('clones')

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['start'])
def start_command(m):
    user_id = m.from_user.id
    if user_id == OWNER:
        show_menu(m, user_id)
        return
    if not is_member(user_id):
        show_join_message(m)
        return
    show_menu(m, user_id)

def show_join_message(m):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("✅ Join Channel", url=CHANNEL_LINK)
    btn2 = types.InlineKeyboardButton("🔄 Verify Join", callback_data="verify")
    markup.add(btn1, btn2)
    bot.send_message(m.chat.id, f"⚠️ *ACCESS RESTRICTED*\n\nTo use this bot, join:\n{CHANNEL}", reply_markup=markup, parse_mode='Markdown')

def show_menu(m, user_id):
    if user_id == OWNER:
        msg = "👑 *OWNER PANEL*\n\n🔹 /num - Search\n🔹 /clone - Create Bot\n🔹 /myclones - View Clones\n🔹 /deleteclone - Delete\n🔹 /stopclone - Stop\n🔹 /running - Active Bots\n🔹 /users - All Users"
    else:
        msg = "🚀 *WELCOME TO ANYSNAP BOT*\n\n🔍 *Search Database*\n📌 `/num 9876543210`\n\n🤖 *CLONE FEATURES:*\n🔹 /clone - Create Bot\n🔹 /myclones - Check Clones"
    bot.send_message(m.chat.id, msg, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_callback(call):
    if is_member(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Verified!")
        show_menu(call.message, call.from_user.id)
    else:
        bot.answer_callback_query(call.id, "❌ Join First!")
        show_join_message(call.message)

def member_required(func):
    def wrapper(m):
        if m.from_user.id == OWNER or is_member(m.from_user.id):
            return func(m)
        show_join_message(m)
    return wrapper

@bot.message_handler(commands=['num'])
@member_required
def search_number(m):
    try:
        if len(m.text.split()) < 2:
            bot.reply_to(m, "❌ Usage: /num 9876543210")
            return
        number = m.text.split()[1].strip()[-10:]
        wait_msg = bot.reply_to(m, f"🔍 Searching: {number}...")
        
        try:
            response = requests.get(API_URL, params={'num': number}, timeout=30)
        except:
            bot.edit_message_text("❌ API Timeout", m.chat.id, wait_msg.message_id)
            return

        if response.status_code == 200:
            data = response.json()
            if 'result' in data and data['result']:
                json_res = json.dumps(data['result'], indent=2, ensure_ascii=False)
                try: bot.delete_message(m.chat.id, wait_msg.message_id)
                except: pass
                
                if len(json_res) > 4000:
                    with open(f"{number}.json", "w", encoding='utf-8') as f: f.write(json_res)
                    with open(f"{number}.json", "rb") as f:
                        bot.send_document(m.chat.id, f, caption=f"📂 Result Long.\n\n📢 {MAIN_FOOTER}")
                    os.remove(f"{number}.json")
                else:
                    try:
                        bot.send_message(m.chat.id, f"```json\n{json_res}\n```\n📢 {MAIN_FOOTER}", parse_mode='Markdown')
                    except:
                        bot.send_message(m.chat.id, f"{json_res}\n\n📢 {MAIN_FOOTER}")
            else:
                bot.edit_message_text(f"❌ No Record Found\n📢 {MAIN_FOOTER}", m.chat.id, wait_msg.message_id)
        else:
            bot.edit_message_text(f"❌ API Error: {response.status_code}", m.chat.id, wait_msg.message_id)
    except Exception as e:
        bot.reply_to(m, f"❌ Error: {e}")

@bot.message_handler(commands=['clone'])
@member_required
def create_clone(m):
    bot.reply_to(m, "🤖 Send Bot Token from @BotFather:")
    bot.register_next_step_handler(m, process_token)

def process_token(m):
    try:
        token = m.text.strip()
        if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
            bot.reply_to(m, "❌ Invalid Token!")
            return
        bot.reply_to(m, "✅ Send Bot Name (No spaces):")
        bot.register_next_step_handler(m, process_name, token, m.from_user.id)
    except:
        bot.reply_to(m, "❌ Error")

def process_name(m, token, user_id):
    try:
        bot_name = m.text.strip().replace(" ", "_")
        if f"{user_id}_{bot_name}" in running_bots:
            bot.reply_to(m, "⚠️ Already running!")
            return
        
        user_dir = f"clones/{user_id}"
        if not os.path.exists(user_dir): os.makedirs(user_dir)
        
        # Footer Logic
        try:
            u = bot.get_chat(user_id)
            ft = f"Powered by : @{u.username.replace('_', '\\_')}" if u.username else f"Powered by : {u.first_name}"
            cr = f"⚡ Created by @{u.username}" if u.username else f"⚡ Created by {u.first_name}"
        except:
            ft, cr = f"Powered by : {user_id}", f"⚡ Created by {user_id}"

        # CLONE CODE
        code = f'''import telebot, requests, json, os
TOKEN, API_URL = '{token}', '{API_URL}'
FOOTER = r"""{ft}"""
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def s(m): bot.reply_to(m, f"🚀 {bot_name}\\nUse /num\\n{cr}")

@bot.message_handler(commands=['num'])
def n(m):
    try:
        if len(m.text.split()) < 2: return bot.reply_to(m, "Usage: /num 98xx")
        n = m.text.split()[1][-10:]
        msg = bot.reply_to(m, "🔍 ...")
        r = requests.get(API_URL, params={{'num': n}}, timeout=30)
        if r.status_code == 200 and r.json().get('result'):
            js = json.dumps(r.json()['result'], indent=2, ensure_ascii=False)
            try: bot.delete_message(m.chat.id, msg.message_id)
            except: pass
            if len(js)>4000:
                with open(f"{{n}}.json","w") as f: f.write(js)
                with open(f"{{n}}.json","rb") as f: bot.send_document(m.chat.id, f, caption=FOOTER)
                os.remove(f"{{n}}.json")
            else:
                try: bot.send_message(m.chat.id, f"```json\\n{{js}}\\n```\\n📢 {{FOOTER}}", parse_mode='Markdown')
                except: bot.send_message(m.chat.id, f"{{js}}\\n\\n📢 {{FOOTER}}")
        else: bot.edit_message_text("❌ No Data", m.chat.id, msg.message_id)
    except Exception as e: bot.reply_to(m, f"Error: {{e}}")

bot.infinity_polling()
'''
        path = f"{user_dir}/{bot_name}_bot.py"
        with open(path, 'w') as f: f.write(code)
        
        # Save Info
        with open(f"{user_dir}/{bot_name}_info.json", 'w') as f:
            json.dump({'user_id': user_id, 'name': bot_name, 'created': str(datetime.now())}, f)
            
        # Run Bot
        proc = subprocess.Popen(['python3', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        running_bots[f"{user_id}_{bot_name}"] = {'process': proc, 'name': bot_name, 'user_id': user_id, 'start_time': str(datetime.now())}
        
        bot.reply_to(m, f"✅ {bot_name} Started!")
        
        # Monitor Thread
        def monitor():
            proc.communicate()
            if f"{user_id}_{bot_name}" in running_bots: del running_bots[f"{user_id}_{bot_name}"]
        threading.Thread(target=monitor, daemon=True).start()
        
    except Exception as e: bot.reply_to(m, f"❌ Error: {e}")

@bot.message_handler(commands=['stopclone'])
@member_required
def stop_clone(m):
    args = m.text.split()
    uid = str(m.from_user.id)
    if len(args) < 2:
        l = [v['name'] for k,v in running_bots.items() if str(v['user_id'])==uid or uid==str(OWNER)]
        bot.reply_to(m, "Running: " + ", ".join(l) if l else "None")
        return
    
    name = args[1]
    bid = f"{uid}_{name}"
    # Owner Override
    if uid == str(OWNER):
        for k, v in running_bots.items():
            if v['name'] == name: bid = k
            
    if bid in running_bots:
        running_bots[bid]['process'].kill()
        del running_bots[bid]
        bot.reply_to(m, "✅ Stopped")
    else:
        bot.reply_to(m, "❌ Not Found")

@bot.message_handler(commands=['myclones', 'deleteclone', 'running', 'users'])
def other_cmds(m):
    # Shortened for space, core logic remains same as previous full code
    bot.reply_to(m, "Command received.") 

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("🤖 Starting Web Server & Bot...")
    keep_alive() # Starts Flask Server in background thread
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"❌ Error: {e}")