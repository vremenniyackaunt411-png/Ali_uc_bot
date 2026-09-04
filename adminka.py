import os
import re
import json
import time
import random
import threading
from datetime import datetime
from flask import Flask
import telebot

# ==========================================
# 1. ТАНЗИМИ ВЕБ-СЕРВЕР БАРОИ UPTIMEROBOT
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Бот фаъол аст ва 24/7 кор мекунад!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()

# ==========================================
# 2. ТАНЗИМ ВА БОТИ ТЕЛЕГРАМ
# ==========================================
TOKEN = os.environ.get("BOT_TOKEN", "8685830202:AAEulXqhwGLY0p9N-saKSCBgcjfmM0UtWIU")
ADMIN_ID = 6871575684

bot = telebot.TeleBot(TOKEN)
FILE_ANSWERS = "answers.json"
FILE_GROUPS = "groups.json"
FILE_BAD_WORDS = "bad_words.json"
FILE_SETTINGS = "settings.json"
FILE_PM_MESSAGES = "pm_messages.json"  # База барои паёмҳои ЛС

CLEANUP_INTERVAL_SECONDS = 7 * 24 * 3600

user_warnings = {}
admin_states = {}

DEFAULT_BAD_WORDS = [
'кунти', 'бго', 'гандон', 'ксиапа', 'ксиоча', 'кси оча', 'кси апа', 'кси хола', 'модарта мег', 'сука', 'сучка', 'далбаёб', 'апата г', 'апата мег', 'очата г', 'очата мег', 'отата г', 'отата мег', 'suka', 'su4ka', 'мегом', 'ksti', 'o4ata m', 'apata m', 'керм', 'kerm', 'мехарм', 'мехарам', 'gom', 'гойда', 'кси м', 'goyda', 'ксти'
]

# --- ИДОРАИ БАЗАИ ПАЁМҲОИ ЛС ---
def load_pm_messages():
    if os.path.exists(FILE_PM_MESSAGES):
        with open(FILE_PM_MESSAGES, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_pm_messages(data):
    with open(FILE_PM_MESSAGES, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

PM_DATA = load_pm_messages()

def load_settings():
    if os.path.exists(FILE_SETTINGS):
        with open(FILE_SETTINGS, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {"min_words_match": 2}
    return {"min_words_match": 2}

def save_settings(settings):
    with open(FILE_SETTINGS, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

SETTINGS = load_settings()

def load_bad_words():
    if os.path.exists(FILE_BAD_WORDS):
        with open(FILE_BAD_WORDS, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return DEFAULT_BAD_WORDS.copy()
    return DEFAULT_BAD_WORDS.copy()

def save_bad_words(words_list):
    with open(FILE_BAD_WORDS, "w", encoding="utf-8") as f:
        json.dump(words_list, f, ensure_ascii=False, indent=4)

BAD_WORDS = load_bad_words()

def cleanup_old_answers(data):
    current_time = time.time()
    cleaned_data = {}
    
    for key, questions in data.items():
        cleaned_questions = {}
        for q, responses in questions.items():
            valid_responses = []
            if isinstance(responses, list):
                for item in responses:
                    if isinstance(item, dict) and "text" in item:
                        max_uses = item.get("max_uses", 2)
                        use_count = item.get("use_count", 0)
                        item_time = item.get("time", current_time)
                        is_expired = (current_time - item_time) > CLEANUP_INTERVAL_SECONDS
                        
                        if use_count < max_uses and not is_expired:
                            valid_responses.append(item)
                    elif isinstance(item, str):
                        valid_responses.append({"text": item, "time": current_time, "use_count": 0, "max_uses": 2})
            
            if valid_responses:
                cleaned_questions[q] = valid_responses
        
        if cleaned_questions:
            cleaned_data[key] = cleaned_questions
            
    return cleaned_data

def load_answers():
    if os.path.exists(FILE_ANSWERS):
        with open(FILE_ANSWERS, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return cleanup_old_answers(data)
            except Exception as e:
                print(f"Хатогӣ ҳангоми боркунии базаи саволҳо: {e}")
                return {}
    return {}

def save_answers():
    with open(FILE_ANSWERS, "w", encoding="utf-8") as f:
        json.dump(ANSWERS, f, ensure_ascii=False, indent=4)

def load_groups():
    if os.path.exists(FILE_GROUPS):
        with open(FILE_GROUPS, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return {}
            except:
                return {}
    return {}

def save_groups(groups_dict):
    with open(FILE_GROUPS, "w", encoding="utf-8") as f:
        json.dump(groups_dict, f, ensure_ascii=False, indent=4)

ANSWERS = load_answers()

BOT_USERNAME = None
try:
    BOT_USERNAME = bot.get_me().username
except Exception as e:
    print(f"Хатогӣ ҳангоми гирифтани номи бот: {e}")

def escape_html(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def send_to_owner(text):
    try:
        bot.send_message(ADMIN_ID, text, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        print(f"⚠️ Хатогӣ ҳангоми фиристодани паём ба соҳиби бот: {e}")

def is_user_admin(chat_id, user_id, sender_chat=None):
    if sender_chat and sender_chat.id == chat_id:
        return True
    if user_id == ADMIN_ID or user_id == 777000:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status in ['administrator', 'creator']:
            return True
    except Exception as e:
        print(f"⚠️ Хатогӣ ҳангоми санҷиши ҳуқуқи админии корбар {user_id}: {e}")
    return False

def has_bad_words(text):
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word == 'кун':
            if re.search(r'\bкун(ӣ|и)?\b', text_lower):
                return True
        elif word == 'кс':
            if re.search(r'\bкс\b', text_lower):
                return True
        else:
            if word in text_lower:
                return True
    return False

def has_link(text):
    link_pattern = r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|\w+\.tj\b|\w+\.ru\b|\w+\.com\b|\w+\.org\b|\w+\.net\b)"
    return bool(re.search(link_pattern, text))

def has_username(text):
    return bool(re.search(r"@\w+", text))

def restrict_user(chat_id, user_id, hours):
    until_date = int(time.time()) + (hours * 3600)
    permissions = telebot.types.ChatPermissions(
        can_send_messages=False, 
        can_send_media_messages=False,
        can_send_polls=False, 
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )
    try:
        bot.restrict_chat_member(chat_id, user_id, until_date=until_date, permissions=permissions)
    except Exception as e:
        print(f"Хатогӣ ҳангоми мут: {e}")

def get_add_to_group_keyboard():
    global BOT_USERNAME
    if not BOT_USERNAME:
        BOT_USERNAME = bot.get_me().username
    markup = telebot.types.InlineKeyboardMarkup()
    btn_add = telebot.types.InlineKeyboardButton(
        "➕ Илова кардан ба гурӯҳ",
        url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
    )
    markup.add(btn_add)
    return markup

def get_group_link(chat_id):
    try:
        chat_obj = bot.get_chat(int(chat_id))
        if chat_obj.invite_link:
            return chat_obj.invite_link
        elif chat_obj.username:
            return f"https://t.me/{chat_obj.username}"
        else:
            try:
                return bot.export_chat_invite_link(int(chat_id))
            except:
                return None
    except:
        return None

# ==========================================
# 4. МЕНЮИ АСОСӢ
# ==========================================
def send_main_menu(chat_id, user_id):
    markup = get_add_to_group_keyboard()

    if user_id == ADMIN_ID:
        btn_admin = telebot.types.InlineKeyboardButton("📊 Гурӯҳҳо", callback_data="admin_groups")
        btn_params = telebot.types.InlineKeyboardButton("⚙️ Параметрҳо", callback_data="admin_params")
        btn_hudomez = telebot.types.InlineKeyboardButton("⚡ Худомезӣ", callback_data="admin_hudomez_menu")
        btn_pm_users = telebot.types.InlineKeyboardButton("📩 Корбарон (ЛС)", callback_data="admin_pm_users")
        
        markup.add(btn_admin, btn_params)
        markup.add(btn_hudomez, btn_pm_users)

    welcome_text = (
        "<b>Салом! Хуш омадед ба боти муҳофиз! 👋🤖</b>\n\n"
        "Ман гурӯҳҳои шуморо аз реклама, дашном ва спам муҳофизат карда, "
        "бо шумо дар гурух хамсухбат мешавам!"
    )
    bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != 'private':
        return

    if message.from_user.id in admin_states:
        admin_states.pop(message.from_user.id)

    user_name = message.from_user.first_name if message.from_user.first_name else "Корбар"
    user_username = f"@{message.from_user.username}" if message.from_user.username else "Никнейм надорад"
    user_id = message.from_user.id

    # Сабти корбар дар базаи ЛС
str_u_id = str(user_id)

if str_u_id not in PM_DATA:
    PM_DATA[str_u_id] = {
        "user_id": user_id,
        "name": user_name,
        "username": user_username,
        "first_name": message.from_user.first_name or "",
        "last_name": message.from_user.last_name or "",
        "messages": [],
        "last_updated": time.time()
    }
else:
    # Агар корбар аллакай сабт шуда бошад,
    # танҳо маълумоти ӯро нав мекунем ва паёмҳояшро нигоҳ медорем.
    PM_DATA[str_u_id]["user_id"] = user_id
    PM_DATA[str_u_id]["name"] = user_name
    PM_DATA[str_u_id]["username"] = user_username
    PM_DATA[str_u_id]["first_name"] = message.from_user.first_name or ""
    PM_DATA[str_u_id]["last_name"] = message.from_user.last_name or ""
    PM_DATA[str_u_id]["last_updated"] = time.time()

# Агар бо ягон сабаб messages вуҷуд надошта бошад
if "messages" not in PM_DATA[str_u_id]:
    PM_DATA[str_u_id]["messages"] = []

save_pm_messages(PM_DATA)

    if user_id != ADMIN_ID:
        notify_owner_msg = (
            f"🚀 <b>Старти Нав!</b>\n\n"
            f"👤 Корбар: {escape_html(user_name)}\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"🏷 Никнейм: {escape_html(user_username)}"
        )
        send_to_owner(notify_owner_msg)

    send_main_menu(message.chat.id, user_id)

# ==========================================
# 5. ИДОРАКУНИИ CALLBACK-ҲО (ТУГМАҲОИ INLINE)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    global BAD_WORDS, SETTINGS, PM_DATA
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if user_id != ADMIN_ID and call.data.startswith("admin_"):
        bot.answer_callback_query(call.id, "❌ Ин бахш танҳо барои соҳиби бот аст!", show_alert=True)
        return

    if call.data == "main_menu":
        if user_id in admin_states:
            admin_states.pop(user_id)
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        send_main_menu(chat_id, user_id)
        bot.answer_callback_query(call.id)

    elif call.data == "admin_pm_users":
        if not PM_DATA:
            bot.answer_callback_query(call.id, "📩 Ҳеҷ паёме аз корбарон дар ЛС сабт нашудааст.", show_alert=True)
            return

        sorted_users = sorted(PM_DATA.items(), key=lambda x: x[1].get("last_updated", 0), reverse=True)

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        counter = 1
        for target_id, u_info in sorted_users:
            msg_count = len(u_info.get("messages", []))
            u_name = u_info.get("name", "Корбар")
            
            btn_text = f"{counter}. {u_name} ({msg_count} паём)"
            btn = telebot.types.InlineKeyboardButton(btn_text, callback_data=f"admin_view_pm_{target_id}")
            markup.add(btn)
            counter += 1

        btn_send_all_pm = telebot.types.InlineKeyboardButton("📢 Паём ба ҳамаи корбарон", callback_data="admin_send_all_pm")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба менюи асосӣ", callback_data="main_menu")
        markup.add(btn_send_all_pm, btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="📩 <b>Рӯйхати корбароне, ки ба бот паём навиштаанд:</b>\n\n<i>Барои дидани паёмҳо ва ҷавоб додан корбарро интихоб кунед:</i>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("admin_view_pm_"):
        target_id = call.data.replace("admin_view_pm_", "")
        u_info = PM_DATA.get(target_id)

        if not u_info:
            bot.answer_callback_query(call.id, "❌ Корбар ёфт нашуд.", show_alert=True)
            return

        u_name = escape_html(u_info.get("name", "Корбар"))
        u_username = escape_html(u_info.get("username", "Никнейм надорад"))
        msgs = u_info.get("messages", [])

        recent_msgs = msgs[-10:]
        formatted_msgs = ""
        for m in recent_msgs:
            sender = "👤 Корбар" if m["sender"] == "user" else "🤖 Админ"
            formatted_msgs += f"<b>{sender}:</b> {escape_html(m['text'])}\n"

        info_text = (
            f"👤 <b>Ном:</b> {u_name}\n"
            f"🏷 <b>Никнейм:</b> {u_username}\n"
            f"🆔 <b>ID:</b> <code>{target_id}</code>\n"
            f"-----------------------------------\n"
            f"💬 <b>Таърихи паёмҳо:</b>\n\n"
            f"{formatted_msgs}\n"
            f"<i>✍️ Барои ҷавоб додан ба ин корбар, тугмаи зерро пахш кунед!</i>"
        )

        admin_states[user_id] = {"action": "reply_to_pm", "target_id": target_id}

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_reply = telebot.types.InlineKeyboardButton("✍️ Ҷавоб додан ба корбар", callback_data=f"admin_reply_pm_{target_id}")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба ақиб", callback_data="admin_pm_users")
        markup.add(btn_reply, btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=info_text,
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("admin_reply_pm_"):
        target_id = call.data.replace("admin_reply_pm_", "")
        admin_states[user_id] = {"action": "reply_to_pm", "target_id": target_id}
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("❌ Бекор кардан", callback_data=f"admin_view_pm_{target_id}"))

        bot.send_message(
            chat_id,
            f"✍️ <b>Матни паёмро нависед:</b>\n\nОн ба корбари ID: <code>{target_id}</code> равон карда мешавад.",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_send_all_pm":
        admin_states[user_id] = {"action": "wait_broadcast_pm"}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("❌ Бекор кардан", callback_data="admin_pm_users"))

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="📢 <b>Лутфан матнеро, ки мехоҳед ба ҲАМАИ корбарони ЛС фиристед, нависед:</b>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_groups":
        groups = load_groups()
        if not groups:
            bot.answer_callback_query(call.id, "📊 Рӯйхати гурӯҳҳо холӣ аст.", show_alert=True)
            return

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        for g_id, g_name in groups.items():
            btn = telebot.types.InlineKeyboardButton(f"👥 {g_name}", callback_data=f"admin_view_group_{g_id}")
            markup.add(btn)
        
        btn_broadcast = telebot.types.InlineKeyboardButton("📢 Паём ба ҳама гурӯҳҳо", callback_data="admin_send_all")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба менюи асосӣ", callback_data="main_menu")
        markup.add(btn_broadcast, btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="📋 <b>Гурӯҳҳое, ки бот дар онҳо васл аст:</b>\n<i>Якеро барои идоракунӣ интихоб кунед ё ба ҳама паём фиристед:</i>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_params":
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_blocked = telebot.types.InlineKeyboardButton("🚫 Корбарони блокшуда", callback_data="admin_blocked_users")
        btn_badwords = telebot.types.InlineKeyboardButton("🤬 Калимаҳои ноҷо", callback_data="admin_bad_words_menu")
        btn_refresh = telebot.types.InlineKeyboardButton("🔄 Навсозии гурӯҳҳо", callback_data="admin_refresh_groups")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба менюи асосӣ", callback_data="main_menu")
        markup.add(btn_blocked, btn_badwords, btn_refresh, btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="⚙️ <b>Параметрҳои танзими бот:</b>\n\nБахши дилхоҳро интихоб кунед:",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_hudomez_menu":
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_add_qa = telebot.types.InlineKeyboardButton("1. Илова кардани ҳозиру ҷавоб ➕", callback_data="admin_add_qa")
        btn_control_qa = telebot.types.InlineKeyboardButton("2. Идораи ҳозиру ҷавоб ⚙️", callback_data="admin_control_qa")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба менюи асосӣ", callback_data="main_menu")
        markup.add(btn_add_qa, btn_control_qa, btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="⚡ <b>Бахши «Худомезӣ»:</b>\n\nБахши заруриро интихоб кунед:",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_add_qa":
        admin_states[user_id] = {"action": "wait_qa_question"}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("❌ Бекор кардан", callback_data="admin_hudomez_menu"))

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="❓ <b>Саволро нависед:</b>\n\n<i>Саволеро, ки корбарон дар гурӯҳ менависанд, равон кунед:</i>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_control_qa":
        admin_states[user_id] = {"action": "wait_match_limit"}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("❌ Бекор кардан", callback_data="admin_hudomez_menu"))

        curr_limit = SETTINGS.get("min_words_match", 2)
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=(
                f"⚙️ <b>Идораи ҳозиру ҷавоб:</b>\n\n"
                f"Ҳозир бот ба паёмҳое ҷавоб медиҳад, ки камаш <b>{curr_limit}</b> калимаи мувофиқ доранд.\n\n"
                f"Рақами нав нависед (масалан: <code>1</code>, <code>2</code>, <code>3</code> ва ғ.):"
            ),
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_blocked_users":
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        has_blocked = False
        counter = 1

        for u_id, data in list(user_warnings.items()):
            if data.get("mute_until", 0) > time.time():
                has_blocked = True
                u_name = data.get("name", "Корбар")
                
                btn_text = f"{counter}. {u_name}"
                btn = telebot.types.InlineKeyboardButton(btn_text, callback_data=f"admin_view_blocked_{u_id}")
                markup.add(btn)
                counter += 1

        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба параметрҳо", callback_data="admin_params")
        markup.add(btn_back)

        if has_blocked:
            msg_text = "🚫 <b>Рӯйхати корбарони блокшуда (Mute):</b>\n\n<i>Барои дидани маълумоти пурра ва аз блок гирифтан, корбарро интихоб кунед:</i>"
        else:
            msg_text = "🚫 <b>Рӯйхати корбарони блокшуда (Mute):</b>\n\n<i>Дар ҳоли ҳозир ҳеҷ корбари блокшуда нест.</i>"

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=msg_text,
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("admin_view_blocked_"):
        target_id = int(call.data.replace("admin_view_blocked_", ""))
        data = user_warnings.get(target_id, {})

        if not data or data.get("mute_until", 0) <= time.time():
            bot.answer_callback_query(call.id, "❌ Ин корбар аллакай аз блок баромадааст ё ёфт нашуд.", show_alert=True)
            return

        u_name = escape_html(data.get("name", "Корбар"))
        u_username = escape_html(data.get("username", "Никнейм надорад"))
        g_title = escape_html(data.get("group_title", "Гурӯҳ"))
        g_link = data.get("group_link")

        start_str = datetime.fromtimestamp(data.get("mute_start", time.time())).strftime("%d.%m.%Y %H:%M")
        until_str = datetime.fromtimestamp(data.get("mute_until", time.time())).strftime("%d.%m.%Y %H:%M")

        if g_link:
            group_str = f"<a href='{g_link}'>{g_title}</a>"
        else:
            group_str = g_title

        user_str = f"<a href='tg://user?id={target_id}'>{u_name}</a> ({u_username})"

        info_text = (
            f"👤 <b>Ном:</b> {user_str}\n"
            f"🏷 <b>Никнейм:</b> {u_username}\n"
            f"🆔 <b>ID:</b> <code>{target_id}</code>\n"
            f"👥 <b>Гурӯҳ:</b> {group_str}\n"
            f"⏰ <b>Вақти блок:</b> аз {start_str} то {until_str}"
        )

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_unmute = telebot.types.InlineKeyboardButton("🔓 Аз блок гирифтан", callback_data=f"admin_unmute_{target_id}")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба ақиб", callback_data="admin_blocked_users")
        markup.add(btn_unmute, btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=info_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("admin_unmute_"):
        target_id = int(call.data.replace("admin_unmute_", ""))
        data = user_warnings.get(target_id, {})
        
        group_id = None
        for g_id, g_name in load_groups().items():
            if g_name == data.get("group_title"):
                group_id = int(g_id)
                break

        if group_id:
            try:
                bot.restrict_chat_member(
                    group_id, 
                    target_id, 
                    permissions=telebot.types.ChatPermissions(
                        can_send_messages=True, can_send_media_messages=True,
                        can_send_polls=True, can_send_other_messages=True,
                        can_add_web_page_previews=True
                    )
                )
            except Exception as e:
                print(f"Хатогӣ ҳангоми озод кардани корбар: {e}")

        if target_id in user_warnings:
            user_warnings[target_id]["mute_until"] = 0
            user_warnings[target_id]["mute_start"] = 0

        bot.answer_callback_query(call.id, "✅ Корбар бомуваффақият аз блок гирифта шуд!", show_alert=True)
        call.data = "admin_blocked_users"
        callback_inline(call)

    elif call.data == "admin_bad_words_menu":
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        btn_add = telebot.types.InlineKeyboardButton("➕ Илова кардан", callback_data="admin_add_bad_word")
        btn_del = telebot.types.InlineKeyboardButton("🗑 Нест кардан", callback_data="admin_del_bad_word")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба параметрҳо", callback_data="admin_params")
        markup.add(btn_add, btn_del)
        markup.add(btn_back)

        words_formatted = ", ".join([f"<code>{w}</code>" for w in BAD_WORDS])
        text_msg = (
            f"🤬 <b>Калимаҳои ноҷо ва манъшуда:</b>\n\n"
            f"{words_formatted}\n\n"
            f"<i>Амалро интихоб кунед:</i>"
        )

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=text_msg,
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_add_bad_word":
        admin_states[user_id] = {"action": "wait_add_bad_word"}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("❌ Бекор кардан", callback_data="admin_bad_words_menu"))

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="➕ <b>Калимаи нав нависед:</b>\n\n<i>Калимаеро, ки мехоҳед дар гурӯҳҳо манъ карда шавад, равон кунед:</i>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_del_bad_word":
        admin_states[user_id] = {"action": "wait_del_bad_word"}
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("❌ Бекор кардан", callback_data="admin_bad_words_menu"))

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="🗑 <b>Калимаро барои нест кардан нависед:</b>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_send_all":
        admin_states[user_id] = {"action": "wait_broadcast"}
        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_back = telebot.types.InlineKeyboardButton("❌ Бекор кардан", callback_data="admin_groups")
        markup.add(btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="📢 <b>Лутфан матнеро, ки мехоҳед ба ҲАМАИ гурӯҳҳо фиристед, нависед:</b>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_refresh_groups":
        bot.answer_callback_query(call.id, "Лутфан мунтазир шавед... 🔄", show_alert=False)
        groups = load_groups()
        updated_groups = {}
        removed_count = 0
        kept_count = 0
        
        try:
            bot_id = bot.get_me().id
        except Exception as e:
            bot.answer_callback_query(call.id, f"Хатогӣ: {e}", show_alert=True)
            return

        for g_id, g_name in list(groups.items()):
            try:
                member = bot.get_chat_member(int(g_id), bot_id)
                if member.status in ['left', 'kicked']:
                    removed_count += 1
                else:
                    chat_info = bot.get_chat(int(g_id))
                    updated_groups[str(g_id)] = chat_info.title if chat_info.title else g_name
                    kept_count += 1
            except Exception:
                removed_count += 1

        save_groups(updated_groups)
        
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔙 Ба параметрҳо", callback_data="admin_params"))
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=(
                f"🔄 <b>Навсозии гурӯҳҳо ба охир расид!</b>\n\n"
                f"✅ Гурӯҳҳои фаъол: <b>{kept_count}</b>\n"
                f"❌ Хориҷшуда/Нестшуда: <b>{removed_count}</b>"
            ),
            parse_mode="HTML",
            reply_markup=markup
        )

    elif call.data.startswith("admin_view_group_"):
        group_id = call.data.replace("admin_view_group_", "")
        groups = load_groups()
        group_name = groups.get(group_id, "Номаълум")
        group_link = get_group_link(group_id) or "Дастрас нест"

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_send = telebot.types.InlineKeyboardButton("✍️ Фиристодани паём", callback_data=f"admin_send_msg_{group_id}")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба рӯйхат", callback_data="admin_groups")
        markup.add(btn_send, btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=(
                f"<b>Гурӯҳи Интихобшуда:</b>\n\n"
                f"👥 <b>Ном:</b> {escape_html(group_name)}\n"
                f"🔗 <b>Ссылка:</b> {group_link}\n"
                f"🆔 <b>ID:</b> <code>{group_id}</code>\n"
            ),
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data.startswith("admin_send_msg_"):
        group_id = call.data.replace("admin_send_msg_", "")
        groups = load_groups()
        group_name = groups.get(group_id, "Номаълум")

        admin_states[user_id] = {"action": "wait_message", "group_id": group_id}

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_back = telebot.types.InlineKeyboardButton("❌ Бекор кардан", callback_data=f"admin_view_group_{group_id}")
        markup.add(btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"✍️ <b>Лутфан матнеро, ки мехоҳед ба гурӯҳи «{escape_html(group_name)}» фиристед, нависед:</b>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

# ==========================================
# 6. НЕСТ КАРДАНИ ПАЁМИ СИСТЕМАВӢ ВА ТАБРИК
# ==========================================
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    chat_id = message.chat.id
    chat_title = message.chat.title

    groups = load_groups()
    is_new_group = str(chat_id) not in groups

    if is_new_group:
        groups[str(chat_id)] = chat_title
        save_groups(groups)

    try:
        bot.delete_message(chat_id, message.message_id)
    except Exception as e:
        print(f"Хатогӣ: {e}")

    for new_user in message.new_chat_members:
        if new_user.id == bot.get_me().id:
            notify_group_msg = (
                f"🎉 <b>Боти шуморо ба гурӯҳи нав илова карданд!</b>\n\n"
                f"👥 Номи Гурӯҳ: {escape_html(chat_title)}\n"
                f"🆔 ID-и Гурӯҳ: <code>{chat_id}</code>"
            )
            send_to_owner(notify_group_msg)
            continue
        
        user_name = new_user.first_name if new_user.first_name else "Корбар"
        welcome_text = f"Хуш омадед ба чати мо, {user_name}! 🫶"
        bot.send_message(chat_id, welcome_text)

@bot.message_handler(content_types=['left_chat_member'])
def delete_left_member_message(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Хатогӣ: {e}")

def get_message_text(message):
    if message.text:
        return message.text.lower()
    elif message.caption:
        return message.caption.lower()
    return ""

# ==========================================
# 7. ГУФТУГӮ ВА МОДЕРАТСИЯ
# ==========================================
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def chat(message):
    global ANSWERS, BAD_WORDS, BOT_USERNAME, SETTINGS, PM_DATA
    if not BOT_USERNAME:
        BOT_USERNAME = bot.get_me().username

    chat_id = str(message.chat.id)
    user_id = message.from_user.id if message.from_user else None
    chat_title = message.chat.title or "Гурӯҳ"
    sender_chat = message.sender_chat

    if message.from_user:
        user_name = message.from_user.first_name if message.from_user.first_name else "Корбар"
        user_username = f"@{message.from_user.username}" if message.from_user.username else "Никнейм надорад"
    else:
        user_name = "Канал / Чат"
        user_username = "Аноним"

    # --- ИДОРАКУНИИ ПАЁМҲОИ ЛС (ЧАТИ ШАХСӢ БО БОТ) ---
    if message.chat.type == 'private':
        # 1. Агар паёмро АДМИН равон кунад
        if user_id == ADMIN_ID:
            if user_id in admin_states:
                action = admin_states[user_id].get("action")

                if action == "reply_to_pm":
                    target_id = admin_states[user_id]["target_id"]
                    msg_text = message.text.strip() if message.text else ""

                    try:
                        # ТАНҲО ХУДИ МАТНИ ПАЁМ БА КОРБАР МЕРАВАД (БЕ ХАБАРҲОИ ИЛОВАГӢ)
                        bot.send_message(target_id, msg_text)
                        
                        # Сабт дар база
                        if target_id in PM_DATA:
                            PM_DATA[target_id]["messages"].append({"sender": "admin", "text": msg_text, "time": time.time()})
                            PM_DATA[target_id]["last_updated"] = time.time()
                            save_pm_messages(PM_DATA)

                        admin_states.pop(user_id)
                        bot.send_message(chat_id, f"✅ Паём ба корбари ID: <code>{target_id}</code> равон шуд!", parse_mode="HTML")
                    except Exception as e:
                        bot.send_message(chat_id, f"❌ Хатогӣ ҳангоми фиристодани паём: {e}")
                    return

                elif action == "wait_broadcast_pm":
                    admin_states.pop(user_id)
                    success_count = 0
                    fail_count = 0
                    
                    bot.send_message(chat_id, "⏳ Раванди фиристодани паём ба ҳамаи корбарон оғоз шуд...")

                    for u_id in list(PM_DATA.keys()):
                        try:
                            bot.send_message(int(u_id), message.text)
                            success_count += 1
                            time.sleep(0.05)
                        except:
                            fail_count += 1

                    bot.send_message(
                        chat_id,
                        f"📢 <b>Рассылка ба корбарон ба охир расид!</b>\n\n✅ Муваффақона: <b>{success_count}</b>\n❌ Хатогӣ: <b>{fail_count}</b>",
                        parse_mode="HTML"
                    )
                    return

                elif action == "wait_qa_question":
                    q_text = message.text.strip().lower()
                    admin_states[user_id] = {"action": "wait_qa_answer", "question": q_text}
                    bot.send_message(chat_id, f"✅ Савол қабул шуд: «<b>{escape_html(q_text)}</b>»\n\n💬 Акнун **ҶАВОБ**-ро равон кунед:", parse_mode="HTML")
                    return

                elif action == "wait_qa_answer":
                    a_text = message.text.strip()
                    q_text = admin_states[user_id]["question"]
                    admin_states[user_id] = {"action": "wait_qa_limit", "question": q_text, "answer": a_text}
                    bot.send_message(chat_id, f"✅ Ҷавоб қабул шуд: «<b>{escape_html(a_text)}</b>»\n\n🔢 Акнун рақамеро нависед, ки ин саволу ҷавоб **ЧАНД БОР** дар гурӯҳ такрор шавад:", parse_mode="HTML")
                    return

                elif action == "wait_qa_limit":
                    try:
                        limit_count = int(message.text.strip())
                        q_text = admin_states[user_id]["question"]
                        a_text = admin_states[user_id]["answer"]

                        global_key = "GLOBAL"
                        if global_key not in ANSWERS:
                            ANSWERS[global_key] = {}

                        if q_text not in ANSWERS[global_key]:
                            ANSWERS[global_key][q_text] = []

                        ANSWERS[global_key][q_text].append({
                            "text": a_text,
                            "time": time.time(),
                            "use_count": 0,
                            "max_uses": limit_count
                        })
                        save_answers()

                        admin_states.pop(user_id)
                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.add(telebot.types.InlineKeyboardButton("⚡ Ба менюи Худомезӣ", callback_data="admin_hudomez_menu"))

                        bot.send_message(
                            chat_id,
                            (
                                f"🎉 <b>Ҳозиру ҷавоб муваффақона илова шуд!</b>\n\n"
                                f"❓ Савол: <code>{escape_html(q_text)}</code>\n"
                                f"💬 Ҷавоб: <code>{escape_html(a_text)}</code>\n"
                                f"🔢 Лимити такрор: <b>{limit_count} маротиба</b>"
                            ),
                            parse_mode="HTML",
                            reply_markup=markup
                        )
                    except ValueError:
                        bot.send_message(chat_id, "⚠️ Лутфан танҳо РАҚАМ нависед (масалан: 3):")
                    return

                elif action == "wait_match_limit":
                    try:
                        match_val = int(message.text.strip())
                        if match_val < 1:
                            match_val = 1
                        SETTINGS["min_words_match"] = match_val
                        save_settings(SETTINGS)

                        admin_states.pop(user_id)
                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.add(telebot.types.InlineKeyboardButton("⚡ Ба менюи Худомезӣ", callback_data="admin_hudomez_menu"))

                        bot.send_message(
                            chat_id,
                            f"✅ Танзимот қабул шуд!\n\nАкнун бот танҳо ҳангоми пайдо шудани камаш <b>{match_val}</b> калимаи мувофиқ дар паём ҷавоб медиҳад.",
                            parse_mode="HTML",
                            reply_markup=markup
                        )
                    except ValueError:
                        bot.send_message(chat_id, "⚠️ Лутфан танҳо РАҚАМ нависед (масалан: 1, 2 ё 3):")
                    return

                elif action == "wait_add_bad_word":
                    new_word = message.text.strip().lower()
                    if new_word and new_word not in BAD_WORDS:
                        BAD_WORDS.append(new_word)
                        save_bad_words(BAD_WORDS)
                        bot.send_message(chat_id, f"✅ Калимаи «<b>{escape_html(new_word)}</b>» илова шуд!", parse_mode="HTML")
                    else:
                        bot.send_message(chat_id, "⚠️ Ин калима аллакай мавҷуд аст.")
                    admin_states.pop(user_id)
                    return

                elif action == "wait_del_bad_word":
                    word_to_del = message.text.strip().lower()
                    if word_to_del in BAD_WORDS:
                        BAD_WORDS.remove(word_to_del)
                        save_bad_words(BAD_WORDS)
                        bot.send_message(chat_id, f"✅ Калимаи «<b>{escape_html(word_to_del)}</b>» нест карда шуд!", parse_mode="HTML")
                    else:
                        bot.send_message(chat_id, "⚠️ Ин калима ёфт нашуд.")
                    admin_states.pop(user_id)
                    return

                elif action == "wait_message":
                    group_id = admin_states[user_id]["group_id"]
                    groups = load_groups()
                    group_name = groups.get(group_id, "Номаълум")
                    
                    try:
                        bot.send_message(group_id, message.text)
                        admin_states.pop(user_id)
                        
                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.add(telebot.types.InlineKeyboardButton("🔙 Ба менюи асосӣ", callback_data="main_menu"))
                        
                        bot.send_message(
                            chat_id, 
                            f"✅ Паёми шумо бомуваффақият ба гурӯҳи «<b>{escape_html(group_name)}</b>» фиристода шуд!", 
                            parse_mode="HTML",
                            reply_markup=markup
                        )
                    except Exception as e:
                        bot.send_message(chat_id, f"❌ Хатогӣ ҳангоми фиристодани паём: {e}")
                    return

                elif action == "wait_broadcast":
                    groups = load_groups()
                    admin_states.pop(user_id)
                    
                    if not groups:
                        bot.send_message(chat_id, "❌ Ҳеҷ гурӯҳе дар база ёфт нашуд!")
                        return

                    success_count = 0
                    fail_count = 0
                    
                    bot.send_message(chat_id, "⏳ Раванди фиристодани паём ба ҳамаи гурӯҳҳо оғоз шуд...")
                    
                    for g_id in list(groups.keys()):
                        try:
                            bot.send_message(int(g_id), message.text)
                            success_count += 1
                            time.sleep(0.1)
                        except Exception as e:
                            print(f"Хатогӣ: {e}")
                            fail_count += 1

                    markup = telebot.types.InlineKeyboardMarkup()
                    markup.add(telebot.types.InlineKeyboardButton("🔙 Ба менюи асосӣ", callback_data="main_menu"))

                    report_text = (
                        f"📢 <b>Рассылка ба охир расид!</b>\n\n"
                        f"✅ Ба <b>{success_count}</b> гурӯҳ расонида шуд.\n"
                        f"❌ Ба <b>{fail_count}</b> гурӯҳ фиристода нашуд."
                    )
                    bot.send_message(chat_id, report_text, parse_mode="HTML", reply_markup=markup)
                    return

        # 2. Агар паёмро КОРБАРИ ОДДӢ ба ЛС-и бот равон кунад
        else:
            str_u_id = str(user_id)
            msg_text = message.text.strip() if message.text else "Паёми медиа"

            if str_u_id not in PM_DATA:
                PM_DATA[str_u_id] = {
                    "name": user_name,
                    "username": user_username,
                    "messages": [],
                    "last_updated": time.time()
                }

            PM_DATA[str_u_id]["name"] = user_name
            PM_DATA[str_u_id]["username"] = user_username
            PM_DATA[str_u_id]["messages"].append({"sender": "user", "text": msg_text, "time": time.time()})
            PM_DATA[str_u_id]["last_updated"] = time.time()
            save_pm_messages(PM_DATA)

            # ОГОҲИИ ФАВРӢ БА АДМИН
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("💬 Ҷавоб додан", callback_data=f"admin_view_pm_{str_u_id}"))

            notify_text = (
                f"📩 <b>Паёми нав дар ЛС!</b>\n\n"
                f"👤 Корбар: <b>{escape_html(user_name)}</b> ({escape_html(user_username)})\n"
                f"🆔 ID: <code>{str_u_id}</code>\n"
                f"💬 Паём: <i>{escape_html(msg_text)}</i>"
            )
            try:
                bot.send_message(ADMIN_ID, notify_text, parse_mode="HTML", reply_markup=markup)
            except Exception as e:
                print(f"Хатогӣ: {e}")

            # БОТ БА КОРБАР ҲЕҶ ПАЁМ НАМЕФИРИСТАД (БА МОНАНДИ ЧАТИ ОДДӢ)
            return

    # --- МАЗМУНИ МУҲОФИЗАТИ ГУРӮҲ ВА ЧАТ ---
    if message.chat.type in ['group', 'supergroup']:
        groups = load_groups()
        if chat_id not in groups:
            groups[chat_id] = chat_title
            save_groups(groups)

    msg_text = get_message_text(message)
    is_admin = is_user_admin(message.chat.id, user_id, sender_chat)

    if not is_admin and user_id:
        if user_id not in user_warnings:
            user_warnings[user_id] = {
                "bad_words": 0, 
                "spam": 0, 
                "name": user_name, 
                "username": user_username, 
                "group_title": chat_title, 
                "group_link": get_group_link(message.chat.id),
                "mute_start": 0, 
                "mute_until": 0
            }

        if user_warnings[user_id].get("mute_until", 0) > time.time():
            try:
                bot.delete_message(message.chat.id, message.message_id)
                return
            except:
                pass

        # КАЛИМАҲОИ НОҶО
        if has_bad_words(msg_text):
            if message.chat.type in ['group', 'supergroup']:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                    user_warnings[user_id]["bad_words"] += 1
                    warnings_count = user_warnings[user_id]["bad_words"]

                    owner_alert = (
                        f"🤬 <b>Сухани Ноҷо Ошкор Шуд!</b>\n\n"
                        f"👤 Корбар: {escape_html(user_name)} ({escape_html(user_username)})\n"
                        f"🆔 ID: <code>{user_id}</code>\n"
                        f"👥 Гурӯҳ: {escape_html(chat_title)}\n"
                        f"💬 Навишт: <code>{escape_html(msg_text)}</code>\n"
                        f"⚠️ Огоҳӣ: {warnings_count}/3"
                    )
                    send_to_owner(owner_alert)

                    add_btn_markup = get_add_to_group_keyboard()

                    if warnings_count < 3:
                        bot.send_message(
                            message.chat.id, 
                            f"⚠️ {user_name}, навиштани калимаҳои ноҷо ва дашном қатъиян манъ аст!\nОгоҳӣ: ({warnings_count}/3)",
                            reply_markup=add_btn_markup
                        )
                    else:
                        restrict_user(message.chat.id, user_id, 8)
                        
                        now_ts = time.time()
                        until_ts = now_ts + (8 * 3600)
                        user_warnings[user_id]["mute_start"] = now_ts
                        user_warnings[user_id]["mute_until"] = until_ts

                        bot.send_message(
                            message.chat.id, 
                            f"🚫 {user_name} барои истифодаи мунтазами калимаҳои ноҷо ба муҳлати <b>8 соат</b> бесадо (Mute) карда шуд!",
                            parse_mode="HTML",
                            reply_markup=add_btn_markup
                        )
                        send_to_owner(f"🚫 Корбар {escape_html(user_name)} (<code>{user_id}</code>) ба муҳлати <b>8 соат бан (Mute)</b> шуд!")
                        user_warnings[user_id]["bad_words"] = 0
                except Exception as e:
                    print(f"❌ Хатогӣ: {e}")
            return

        # РЕКЛАМА / СПАМ
        is_forwarded = message.forward_from or message.forward_from_chat or message.forward_sender_name
        if has_link(msg_text) or has_username(msg_text) or is_forwarded:
            if message.chat.type in ['group', 'supergroup']:
                try:
                    bot.delete_message(message.chat.id, message.message_id)
                    user_warnings[user_id]["spam"] += 1
                    warnings_count = user_warnings[user_id]["spam"]
                    reason = "переслать (forward)" if is_forwarded else "ссылка/никнейм"

                    owner_alert = (
                        f"📢 <b>Реклама / Спам Ошкор Шуд!</b>\n\n"
                        f"👤 Корбар: {escape_html(user_name)} ({escape_html(user_username)})\n"
                        f"🆔 ID: <code>{user_id}</code>\n"
                        f"👥 Гурӯҳ: {escape_html(chat_title)}\n"
                        f"📂 Навъ: {reason}\n"
                        f"💬 Навишт: <code>{escape_html(msg_text)}</code>\n"
                        f"⚠️ Огоҳӣ: {warnings_count}/3"
                    )
                    send_to_owner(owner_alert)

                    add_btn_markup = get_add_to_group_keyboard()

                    if warnings_count < 3:
                        bot.send_message(
                            message.chat.id, 
                            f"⚠️ {user_name}, фиристодани {reason} реклама ҳисоб шуда, манъ аст!\nОгоҳӣ: ({warnings_count}/3)",
                            reply_markup=add_btn_markup
                        )
                    else:
                        restrict_user(message.chat.id, user_id, 24)

                        now_ts = time.time()
                        until_ts = now_ts + (24 * 3600)
                        user_warnings[user_id]["mute_start"] = now_ts
                        user_warnings[user_id]["mute_until"] = until_ts

                        bot.send_message(
                            message.chat.id, 
                            f"🚫 {user_name} барои паҳн кардани реклама ва спам ба муҳлати <b>24 соат</b> бесадо (Mute) карда шуд!",
                            parse_mode="HTML",
                            reply_markup=add_btn_markup
                        )
                        send_to_owner(f"🚫 Корбар {escape_html(user_name)} (<code>{user_id}</code>) ба муҳлати <b>24 соат бан (Mute)</b> шуд!")
                        user_warnings[user_id]["spam"] = 0
                except Exception as e:
                    print(f"❌ Хатогӣ: {e}")
            return

    # АВТО-ОМӮЗИШ ВА ҶАВОБДИҲӢ (ХУДОМЕЗӢ)
    if message.chat.type in ['group', 'supergroup'] and message.content_type == 'text':
        text_clean = message.text.strip().lower()
        now = time.time()

        ANSWERS = cleanup_old_answers(ANSWERS)

        if message.reply_to_message and message.reply_to_message.text:
            savol = message.reply_to_message.text.strip().lower()
            javob = message.text.strip()

            if len(savol) > 1 and javob and not has_bad_words(javob) and not has_link(javob):
                global_key = "GLOBAL"
                if global_key not in ANSWERS:
                    ANSWERS[global_key] = {}

                if savol not in ANSWERS[global_key]:
                    ANSWERS[global_key][savol] = []

                existing_texts = [item["text"] for item in ANSWERS[global_key][savol] if isinstance(item, dict)]
                if javob not in existing_texts:
                    ANSWERS[global_key][savol].append({"text": javob, "time": now, "use_count": 0, "max_uses": 2})
                    save_answers()

        if "GLOBAL" in ANSWERS and ANSWERS["GLOBAL"]:
            matched_question = None
            user_words = [w for w in re.findall(r'\b\w+\b', text_clean) if len(w) > 0]
            
            min_match = SETTINGS.get("min_words_match", 2)

            if len(user_words) >= min_match:
                if text_clean in ANSWERS["GLOBAL"]:
                    matched_question = text_clean
                else:
                    for q in ANSWERS["GLOBAL"].keys():
                        q_words = set(re.findall(r'\b\w+\b', q))
                        matching_count = sum(1 for w in user_words if w in q_words)
                        
                        if matching_count >= min_match:
                            matched_question = q
                            break

            if matched_question and ANSWERS["GLOBAL"][matched_question]:
                responses = ANSWERS["GLOBAL"][matched_question]
                
                chosen_item = random.choice(responses)
                chosen_reply = chosen_item["text"]

                bot.reply_to(message, chosen_reply)

                chosen_item["use_count"] = chosen_item.get("use_count", 0) + 1
                max_allowed = chosen_item.get("max_uses", 2)

                if chosen_item["use_count"] >= max_allowed:
                    responses.remove(chosen_item)
                    if not responses:
                        del ANSWERS["GLOBAL"][matched_question]

                save_answers()
                return

# ==========================================
# 8. ОҒОЗИ КОР ВА БОТ ПОЛЛИНГ
# ==========================================
if __name__ == '__main__':
    keep_alive()
    print("Веб-сервер бомуваффақият фаъол шуд!")
    
    while True:
        try:
            print("Бот фаъол шуд ва ба кор омода аст...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠️ Хатогии корӣ: {e}")
            time.sleep(5)
