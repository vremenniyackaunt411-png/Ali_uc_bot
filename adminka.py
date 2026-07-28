import os
import re
import json
import time
import random
import threading
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

# Вақти нигоҳдории саволу ҷавобҳо: 7 рӯз (бо сония)
CLEANUP_INTERVAL_SECONDS = 7 * 24 * 3600

user_warnings = {}
admin_states = {}

BAD_WORDS = [
    'кунти', 'бго', 'гандон', 'ксиапа', 'ксиоча', 'кси оча', 'кси апа', 'кси хола', 'модарта мег', 'сука', 'сучка', 'далбаёб', 
    'фуруши дорм', 'фуруши дорам', 'ки мехара', 'апата г', 'апата мег', 'очата г', 'очата мег', 'отата г', 'отата мег', 'suka', 'su4ka',
    'мегом', 'ksti', 'o4ata m', 'apata m', 'керм', 'kerm', 'мехарм', 'мехарам', 'gom', 'гойда' 
]

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
                        
                        # Агар камтар аз 2 бор истифода шуда бошад ва аз 7 рӯз кӯҳна нашуда бошад
                        if use_count < 2 and not is_expired:
                            valid_responses.append(item)
                    elif isinstance(item, str):
                        # Барои поддежкаи формати кӯҳна
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
        bot.send_message(ADMIN_ID, text, parse_mode="HTML")
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

# ==========================================
# 4. МЕНЮИ АСОСӢ (БАРОИ ЛС - ЧАТИ БОТ)
# ==========================================
def send_main_menu(chat_id, user_id):
    global BOT_USERNAME
    if not BOT_USERNAME:
        BOT_USERNAME = bot.get_me().username

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    
    btn_add = telebot.types.InlineKeyboardButton(
        "➕ Илова кардан ба гурӯҳ",
        url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
    )
    markup.add(btn_add)

    if user_id == ADMIN_ID:
        btn_admin = telebot.types.InlineKeyboardButton("📊 Гурӯҳҳои васлшуда", callback_data="admin_groups")
        btn_refresh = telebot.types.InlineKeyboardButton("🔄 Навсозии гурӯҳҳо", callback_data="admin_refresh_groups")
        markup.add(btn_admin, btn_refresh)

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
        
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба менюи асосӣ", callback_data="main_menu")
        markup.add(btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="📋 <b>Гурӯҳҳое, ки бот дар онҳо васл аст:</b>\n<i>Якеро барои идоракунӣ ва фиристодани паём интихоб кунед:</i>",
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
        markup.add(telebot.types.InlineKeyboardButton("🔙 Ба менюи асосӣ", callback_data="main_menu"))
        
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

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        btn_send = telebot.types.InlineKeyboardButton("✍️ Фиристодани паём", callback_data=f"admin_send_msg_{group_id}")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Ба рӯйхат", callback_data="admin_groups")
        markup.add(btn_send, btn_back)

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"<b>Гурӯҳи Интихобшуда:</b>\n\n👥 Ном: {escape_html(group_name)}\n🆔 ID: <code>{group_id}</code>\n\nБарои аз номи бот ба ин гурӯҳ равон кардани паём тугмаи зеринро зер кунед:",
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
        welcome_text = f"Хуш омадед ба чати мо, {user_name}! 😊✨"
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
    global ANSWERS
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

    # 1. ПАЁМИ АДМИН АЗ ЛС
    if message.chat.type == 'private' and user_id == ADMIN_ID:
        if user_id in admin_states and admin_states[user_id].get("action") == "wait_message":
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
            user_warnings[user_id] = {"bad_words": 0, "spam": 0}

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

                    if warnings_count < 3:
                        bot.send_message(
                            message.chat.id, 
                            f"⚠️ {user_name}, навиштани калимаҳои ноҷо ва дашном қатъиян манъ аст!\nОгоҳӣ: ({warnings_count}/3)"
                        )
                    else:
                        restrict_user(message.chat.id, user_id, 8)
                        bot.send_message(
                            message.chat.id, 
                            f"🚫 {user_name} барои истифодаи мунтазами калимаҳои ноҷо ба муҳлати <b>8 соат</b> бесадо (Mute) карда шуд!",
                            parse_mode="HTML"
                        )
                        send_to_owner(f"🚫 Корбар {escape_html(user_name)} (<code>{user_id}</code>) барои сухани ноҷо дар гурӯҳи {escape_html(chat_title)} <b>8 соат бан (Mute)</b> шуд!")
                        user_warnings[user_id]["bad_words"] = 0
                except Exception as e:
                    print(f"❌ Хатогӣ ҳангоми ҷаримаи калимаи ноҷо: {e}")
            return

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

                    if warnings_count < 3:
                        bot.send_message(
                            message.chat.id, 
                            f"⚠️ {user_name}, фиристодани {reason} реклама ҳисоб шуда, манъ аст!\nОгоҳӣ: ({warnings_count}/3)"
                        )
                    else:
                        restrict_user(message.chat.id, user_id, 24)
                        bot.send_message(
                            message.chat.id, 
                            f"🚫 {user_name} барои паҳн кардани реклама ва спам ба муҳлати <b>24 соат</b> бесадо (Mute) карда шуд!",
                            parse_mode="HTML"
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

        # Тоза кардани саволу ҷавобҳои кӯҳна ё 2-бор истифодашуда
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

                # Санҷиши такрор нашудани як ҷавоб
                existing_texts = [item["text"] for item in ANSWERS[global_key][savol] if isinstance(item, dict)]
                if javob not in existing_texts:
                    ANSWERS[global_key][savol].append({"text": javob, "time": now, "use_count": 0})
                    save_answers()
                    print(f"[Базаи Умумӣ] Сабт шуд: '{savol}' -> '{javob}'")

        # Б) ҶАВОБДИҲИИ АВТОМАТӢ
        if "GLOBAL" in ANSWERS and ANSWERS["GLOBAL"]:
            matched_question = None

            # 1. Мувофиқати дақиқи ҷумла
            if text_clean in ANSWERS["GLOBAL"]:
                matched_question = text_clean

            # 2. Ҷӯстуҷӯ аз рӯи калимаҳои асосӣ
            if not matched_question:
                for q in ANSWERS["GLOBAL"].keys():
                    words = q.split()
                    if any(w in text_clean for w in words if len(w) > 2) or text_clean in q:
                        matched_question = q
                        break

            # 3. Интихоб ва истифодаи ҷавоб
            if matched_question and ANSWERS["GLOBAL"][matched_question]:
                responses = ANSWERS["GLOBAL"][matched_question]
                
                # Интихоби тасодуфии як ҷавоб
                chosen_item = random.choice(responses)
                chosen_reply = chosen_item["text"]

                # Фиристодани ҷавоб
                bot.reply_to(message, chosen_reply)

                # Шавзонидани ҳисобкунак (use_count)
                chosen_item["use_count"] = chosen_item.get("use_count", 0) + 1

                # Агар 2 маротиба истифода шуда бошад -> нест мекунем
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
