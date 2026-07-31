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

# Вақти нигоҳдории саволу ҷавобҳо: 7 рӯз
CLEANUP_INTERVAL_SECONDS = 7 * 24 * 3600

user_warnings = {}
admin_states = {}

DEFAULT_BAD_WORDS = [
    'кунти', 'бго', 'гандон', 'ксиапа', 'ксиоча', 'кси оча', 'кси апа', 'кси хола', 'модарта мег', 'сука', 'сучка', 'далбаёб', 
    'фуруши дорм', 'фуруши дорам', 'ки мехара', 'апата г', 'апата мег', 'очата г', 'очата мег', 'отата г', 'отата мег', 'suka', 'su4ka',
    'мегом', 'ksti', 'o4ata m', 'apata m', 'керм', 'kerm', 'мехарм', 'мехарам', 'gom', 'гойда' 
]

# ==========================================
# ФАЙЛҲОИ ДИНАМИКИИ КАЛИМАҲОИ НОҶО
# ==========================================
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

# ==========================================
# 3. ТОЗАИ НАВШУДАИ БАЗА (2 ИСТИФОДА Ё 7 РӮЗ)
# ==========================================
def cleanup_old_answers(data):
    current_time = time.time()
    cleaned_data = {}
    
    for key, questions in data.items():
        cleaned_questions = {}
        for q, responses in questions.items():
            valid_responses = []
            if isinstance(responses, list):
                for item in responses:
                    if isinstance(item, dict) and "text" in item and "time" in item:
                        use_count = item.get("use_count", 0)
                        is_expired = (current_time - item["time"]) > CLEANUP_INTERVAL_SECONDS
                        
                        if use_count < 2 and not is_expired:
                            valid_responses.append(item)
                    elif isinstance(item, str):
                        valid_responses.append({"text": item, "time": current_time, "use_count": 0})
            
            cleaned_questions[q] = valid_responses
        
        cleaned_questions = {q: resp for q, resp in cleaned_questions.items() if resp}
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
        can_send_messages=False, can_send_media_messages=False,
        can_send_audios=False, can_send_documents=False,
        can_send_photos=False, can_send_videos=False,
        can_send_video_notes=False, can_send_voice_notes=False,
        can_send_polls=False, can_send_other_messages=False,
        can_add_web_page_previews=False
    )
    bot.restrict_chat_member(chat_id, user_id, until_date=until_date, permissions=permissions)

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
# 4. МЕНЮИ АСОСӢ (БАРОИ ЛС - ЧАТИ БОТ)
# ==========================================
def send_main_menu(chat_id, user_id):
    markup = get_add_to_group_keyboard()

    if user_id == ADMIN_ID:
        btn_admin = telebot.types.InlineKeyboardButton("📊 Гурӯҳҳои васлшуда", callback_data="admin_groups")
        btn_params = telebot.types.InlineKeyboardButton("⚙️ Параметрҳо", callback_data="admin_params")
        markup.add(btn_admin, btn_params)

    welcome_text = (
        "<b>Салом! Хуш омадед ба боти муҳофиз! 👋🤖</b>\n\n"
        "Ман гурӯҳҳои шуморо аз реклама, дашном ва спам муҳофизат карда, "
        "бо шумо дар гурух хамсухбат мешавам!"
    )
    bot.send_message(chat_id, welcome_text, parse_mode="HTML", reply_markup=markup)

# =====================
# START / MENU
# =====================
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != 'private':
        return

    if message.from_user.id in admin_states:
        admin_states.pop(message.from_user.id)

    user_name = message.from_user.first_name if message.from_user.first_name else "Корбар"
    user_username = f"@{message.from_user.username}" if message.from_user.username else "Никнейм надорад"
    user_id = message.from_user.id

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
    global BAD_WORDS
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if user_id != ADMIN_ID and call.data.startswith("admin_"):
        bot.answer_callback_query(call.id, "❌ Ин бахш танҳо барои соҳиби бот аст!", show_alert=True)
        return

    if call.data == "main_menu":
        if user_id in admin_states:
            admin_states.pop(user_id)
        bot.delete_message(chat_id, call.message.message_id)
        send_main_menu(chat_id, user_id)
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
        
        btn_broadcast = telebot.types.InlineKeyboardButton("📢 Паём ба ҳама", callback_data="admin_send_all")
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

    # --- РӮЙХАТИ КОРБАРОНИ БЛОКШУДА (НАВСОЗИШУДА) ---
    elif call.data == "admin_blocked_users":
        blocked_text = "🚫 <b>Рӯйхати корбарони блокшуда (Mute):</b>\n\n"
        has_blocked = False

        for u_id, data in user_warnings.items():
            if data.get("mute_until", 0) > time.time():
                has_blocked = True
                u_name = escape_html(data.get("name", "Корбар"))
                u_username = data.get("username", "Никнейм надорад")
                g_title = escape_html(data.get("group_title", "Гурӯҳ"))
                g_link = data.get("group_link")

                start_str = datetime.fromtimestamp(data.get("mute_start", time.time())).strftime("%d.%m.%Y %H:%M")
                until_str = datetime.fromtimestamp(data.get("mute_until", time.time())).strftime("%d.%m.%Y %H:%M")

                if g_link:
                    group_str = f"<a href='{g_link}'>{g_title}</a>"
                else:
                    group_str = g_title

                user_str = f"<a href='tg://user?id={u_id}'>{u_name}</a> ({escape_html(u_username)})"

                blocked_text += (
                    f"👤 <b>Корбар:</b> {user_str}\n"
                    f"👥 <b>Аз гурӯҳи:</b> {group_str}\n"
                    f"⏰ <b>Блок шуд:</b> {start_str} то {until_str}\n"
                    f"──────────────────\n"
                )

        if not has_blocked:
            blocked_text += "<i>Дар ҳоли ҳозир корбари блокшуда (Mute) нест.</i>"

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🔙 Ба параметрҳо", callback_data="admin_params"))

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=blocked_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

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
            text="➕ <b>Калимаи нав нависед:</b>\n\n<i>Калимаеро, ки мехоҳед дар гурӯҳҳо манъ карда шавад ва барои он бан дода шавад, равон кунед:</i>",
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
            text="🗑 <b>Калимаро барои нест кардан нависед:</b>\n\n<i>Он калимае, ки мехоҳед дигар блок дода нашавад, равон кунед:</i>",
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
            text="📢 <b>Лутфан матнеро, ки мехоҳед ба ҲАМАИ гурӯҳҳо фиристед, нависед:</b>\n\n<i>Ин паём ба таври автоматикӣ ба тамоми чатҳои васлшуда равон мешавад.</i>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "admin_refresh_groups":
        bot.answer_callback_query(call.id, "Лутфан мунтазир шавед, гурӯҳҳо санҷида мешаванд... 🔄", show_alert=False)
        groups = load_groups()
        updated_groups = {}
        removed_count = 0
        kept_count = 0
        
        try:
            bot_id = bot.get_me().id
        except Exception as e:
            bot.answer_callback_query(call.id, f"Хатогӣ дар пайвастшавӣ: {e}", show_alert=True)
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
                f"❌ Хориҷшуда/Нестшуда: <b>{removed_count}</b>\n\n"
                f"<i>Маълумоти базаи шумо бо муваффақият тоза ва нав карда шуд!</i>"
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
                f"🆔 <b>ID:</b> <code>{group_id}</code>\n\n"
                f"Барои аз номи бот ба ин гурӯҳ равон кардани паём тугмаи зеринро зер кунед:"
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
            text=f"✍️ <b>Лутфан матнеро, ки мехоҳед ба гурӯҳи «{escape_html(group_name)}» фиристед, нависед:</b>\n\n<i>Паёми навбатии шумо мустақим ба ин гурӯҳ равон мешавад.</i>",
            parse_mode="HTML",
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)

# ==========================================
# 6. НЕСТ КАРДАНИ ПАЁМИ СИСТЕМАВӢ ВА ТАБРИКИ НАВ
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
        print(f"Хатогӣ ҳангоми нест кардани паёми омадан: {e}")

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

# ==========================================
# НЕСТ КАРДАНИ НАВИШТАҶОТИ ОДАМИ БАРОМАДА
# ==========================================
@bot.message_handler(content_types=['left_chat_member'])
def delete_left_member_message(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Хатогӣ ҳангоми нест кардани паёми баромад: {e}")

def get_message_text(message):
    if message.text:
        return message.text.lower()
    elif message.caption:
        return message.caption.lower()
    return ""

# ==========================================
# 7. ГУФТУГӮ, АВТО-ОМӮЗИШ ВА МОДЕРАТСИЯ
# ==========================================
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def chat(message):
    global ANSWERS, BAD_WORDS, BOT_USERNAME
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

    # 1. ПАЁМИ АДМИН АЗ ЛС (ИДОРАКУНӢ ВА КАЛИМАҲОИ НОҶО)
    if message.chat.type == 'private' and user_id == ADMIN_ID:
        if user_id in admin_states:
            action = admin_states[user_id].get("action")
            
            if action == "wait_add_bad_word":
                new_word = message.text.strip().lower()
                if new_word and new_word not in BAD_WORDS:
                    BAD_WORDS.append(new_word)
                    save_bad_words(BAD_WORDS)
                    bot.send_message(chat_id, f"✅ Калимаи «<b>{escape_html(new_word)}</b>» ба рӯйхати калимаҳои манъшуда илова шуд ва аз ин пас барои он бан дода мешавад!", parse_mode="HTML")
                else:
                    bot.send_message(chat_id, "⚠️ Ин калима аллакай дар рӯйхат мавҷуд аст ё нодуруст навишта шуд.")
                admin_states.pop(user_id)
                return

            elif action == "wait_del_bad_word":
                word_to_del = message.text.strip().lower()
                if word_to_del in BAD_WORDS:
                    BAD_WORDS.remove(word_to_del)
                    save_bad_words(BAD_WORDS)
                    bot.send_message(chat_id, f"✅ Калимаи «<b>{escape_html(word_to_del)}</b>» аз рӯйхат нест карда шуд ва акнун барои он блок дода намешавад!", parse_mode="HTML")
                else:
                    bot.send_message(chat_id, "⚠️ Ин калима дар рӯйхати калимаҳои ноҷо ёфт шумод.")
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
                    bot.send_message(chat_id, f"❌ Хатогӣ ҳангоми фиристодани паём ба гурӯҳ: {e}")
                return

            elif action == "wait_broadcast":
                groups = load_groups()
                admin_states.pop(user_id)
                
                if not groups:
                    bot.send_message(chat_id, "❌ Ҳеҷ гурӯҳе дар база ёфт نشуд!")
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
                        print(f"Хатогӣ ҳангоми рассылка ба гурӯҳи {g_id}: {e}")
                        fail_count += 1

                markup = telebot.types.InlineKeyboardMarkup()
                markup.add(telebot.types.InlineKeyboardButton("🔙 Ба менюи асосӣ", callback_data="main_menu"))

                report_text = (
                    f"📢 <b>Рассылка ба охир расид!</b>\n\n"
                    f"✅ Ба <b>{success_count}</b> гурӯҳ муваффақона расонида шуд.\n"
                    f"❌ Ба <b>{fail_count}</b> гурӯҳ фиристода нашуд (шояд бот баромад ё бан шуд)."
                )
                bot.send_message(chat_id, report_text, parse_mode="HTML", reply_markup=markup)
                return

    # САБТИ ГУРӮҲ
    if message.chat.type in ['group', 'supergroup']:
        groups = load_groups()
        if chat_id not in groups:
            groups[chat_id] = chat_title
            save_groups(groups)

    msg_text = get_message_text(message)
    is_admin = is_user_admin(message.chat.id, user_id, sender_chat)

    # 2. АНТИСПАМ ВА АНТИДАШНОМ
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
        else:
            user_warnings[user_id]["name"] = user_name
            user_warnings[user_id]["username"] = user_username
            user_warnings[user_id]["group_title"] = chat_title
            if not user_warnings[user_id].get("group_link"):
                user_warnings[user_id]["group_link"] = get_group_link(message.chat.id)

        # --- КАЛИМАҲОИ НОҶО ---
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
                        send_to_owner(f"🚫 Корбар {escape_html(user_name)} (<code>{user_id}</code>) барои сухани ноҷо дар гурӯҳи {escape_html(chat_title)} <b>8 соат бан (Mute)</b> шуд!")
                        user_warnings[user_id]["bad_words"] = 0
                except Exception as e:
                    print(f"❌ Хатогӣ ҳангоми ҷаримаи калимаи ноҷо: {e}")
            return

        # --- ССЫЛКА, НИКНЕЙМ ВА ПЕРЕСЛАТЬ (СПАМ/РЕКЛАМА) ---
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
                        send_to_owner(f"🚫 Корбар {escape_html(user_name)} (<code>{user_id}</code>) барои спам/реклама дар гурӯҳи {escape_html(chat_title)} <b>24 соат бан (Mute)</b> шуд!")
                        user_warnings[user_id]["spam"] = 0
                except Exception as e:
                    print(f"❌ Хатогӣ ҳангоми ҷаримаи спам: {e}")
            return

    # ==========================================
    # СИСТЕМАИ АВТО-ОМӮЗИШ ВА ҲАМСӮҲБАТӢ
    # ==========================================
    if message.chat.type in ['group', 'supergroup'] and message.content_type == 'text':
        text_clean = message.text.strip().lower()
        now = time.time()

        ANSWERS = cleanup_old_answers(ANSWERS)

        # А) Агар паём ҷавоб (Reply) бошад -> САБТ КАРДАН
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
                    ANSWERS[global_key][savol].append({"text": javob, "time": now, "use_count": 0})
                    save_answers()
                    print(f"[Базаи Умумӣ] Сабт шуд: '{savol}' -> '{javob}'")

        # Б) ҶАВОБДИҲИИ АВТОМАТӢ (2 КАЛИМА ВА БЕШ АЗ 2 КАЛИМА)
        if "GLOBAL" in ANSWERS and ANSWERS["GLOBAL"]:
            matched_question = None

            user_words = [w for w in re.findall(r'\b\w+\b', text_clean) if len(w) > 1]

            # Агар корбар 2 ё бештар калима нависад
            if len(user_words) >= 2:
                # 1. Мувофиқати дақиқ
                if text_clean in ANSWERS["GLOBAL"]:
                    matched_question = text_clean
                else:
                    # 2. Санҷиши мувофиқати 2 ё беш аз 2 калима бо саволҳои база
                    for q in ANSWERS["GLOBAL"].keys():
                        q_words = set(re.findall(r'\b\w+\b', q))
                        matching_count = sum(1 for w in user_words if w in q_words)
                        
                        if matching_count >= 2:
                            matched_question = q
                            break

            if matched_question and ANSWERS["GLOBAL"][matched_question]:
                responses = ANSWERS["GLOBAL"][matched_question]
                
                chosen_item = random.choice(responses)
                chosen_reply = chosen_item["text"]

                bot.reply_to(message, chosen_reply)

                chosen_item["use_count"] = chosen_item.get("use_count", 0) + 1

                if chosen_item["use_count"] >= 2:
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
