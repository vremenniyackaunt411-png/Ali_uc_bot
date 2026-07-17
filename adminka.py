import os
import re
import json
import time
import random
import threading  # Илова шуд барои Flask
from flask import Flask  # Илова шуд барои Flask
import telebot

# ==========================================
# 1. ТАНЗИМИ ВЕБ-СЕРВЕР БАРОИ UPTIMEROBOT
# ==========================================
app = Flask('')

@app.route('/')
def home():
    return "Бот фаъол аст ва 24/7 кор мекунад!", 200

def run_web_server():
    # Render ба таври худкор тағйирёбандаи PORT-ро медиҳад, агар набошад 8080-ро мегирад
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()

# ==========================================
# 2. ТАНЗИМ ВА БОТИ ТЕЛЕГРАМ
# ==========================================
TOKEN = "8685830202:AAEulXqhwGLY0p9N-saKSCBgcjfmM0UtWIU"

# ИД-И ТЕЛЕГРАМИ ХУДАТОН (Соҳиби бот)
ADMIN_ID = 6871575684

bot = telebot.TeleBot(TOKEN)
FILE_ANSWERS = "answers.json"
FILE_GROUPS = "groups.json"

# Махзани огоҳиҳо (Алоҳида барои дашном ва спам)
user_warnings = {}

# Барои муваққатӣ нигоҳ доштани ҳолати фиристодани паём аз ҷониби админ
admin_states = {}

# РӮЙХАТИ КАЛИМАҲОИ НОҶО ВА СПАМӢ БАРОИ ТОЗА КАРДАН
BAD_WORDS = [
    'кун', 'гандон', 'сука', 'кс', 'далбаёб', 
    'фуруши дорм', 'фуруши дорам', 'ки мехара', 'ки мехарад', 
    'мегом', 'кер', 'керм', 'мехарм', 'мехарам', 'гом'
]

# Боргузории базаи саволу ҷавобҳои автоматӣ
def load_answers():
    if os.path.exists(FILE_ANSWERS):
        with open(FILE_ANSWERS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}  # Базаи холӣ, ки худаш бо усули Reply пур мешавад

# Сабти базаи саволу ҷавобҳо
def save_answers():
    with open(FILE_ANSWERS, "w", encoding="utf-8") as f:
        json.dump(ANSWERS, f, ensure_ascii=False, indent=4)

def load_groups():
    if os.path.exists(FILE_GROUPS):
        with open(FILE_GROUPS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_groups(groups_dict):
    with open(FILE_GROUPS, "w", encoding="utf-8") as f:
        json.dump(groups_dict, f, ensure_ascii=False, indent=4)

# Боркунии база (сохтор: {"chat_id": {"савол": "ҷавоб"}})
ANSWERS = load_answers()

BOT_USERNAME = None
try:
    BOT_USERNAME = bot.get_me().username
except Exception as e:
    print(f"Хатогӣ ҳангоми гирифтани номи бот: {e}")

# Функсияи тоза кардани аломатҳои HTML
def escape_html(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# Фиристодани паём ба соҳиби бот
def send_to_owner(text):
    try:
        bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except Exception as e:
        print(f"⚠️ Хатогӣ ҳангоми фиристодани паём ба соҳиби бот: {e}")

# Санҷидани админ будани корбар
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

# Санҷиши калимаҳои ноҷо
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

# Санҷиши линкҳо
def has_link(text):
    link_pattern = r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|\w+\.tj\b|\w+\.ru\b|\w+\.com\b|\w+\.org\b|\w+\.net\b)"
    return bool(re.search(link_pattern, text))

# Санҷиши никнеймҳо
def has_username(text):
    return bool(re.search(r"@\w+", text))

# Маҳдудсозӣ (Mute)
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
# МЕНЮИ АСОСӢ (БАРОИ ЛС - ЧАТИ БОТ)
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
        markup.add(btn_admin)

    welcome_text = (
        "<b>Салом! Хуш омадед ба боти муҳофиз! 👋🤖</b>\n\n"
        "Ман гурӯҳҳои шуморо аз реклама, дашном ва спам муҳофизат карда, "
        "худ ба худ аз сӯҳбатҳо саволу ҷавоб меомӯзам!"
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
# ИДОРАКУНИИ CALLBACK-ҲО (ТУГМАҲОИ INLINE)
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
# НЕСТ КАРДАНИ ПАЁМИ СИСТЕМАВӢ ВА ТАБРИКИ НАВ
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

# Сӯҳбат ва матни ошкоршуда
def get_message_text(message):
    if message.text:
        return message.text.lower()
    elif message.caption:
        return message.caption.lower()
    return ""

# ==========================================
# ГУФТУГӮ, АВТО-ОМӮЗИШ ВА МОДЕРАТСИЯ
# ==========================================
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def chat(message):
    chat_id = str(message.chat.id)  # ID-и гурӯҳро ба намуди сатр истифода мебарем
    user_id = message.from_user.id if message.from_user else None
    chat_title = message.chat.title or "Гурӯҳ"
    sender_chat = message.sender_chat

    # Муайян кардани номи корбар
    if message.from_user:
        user_name = message.from_user.first_name if message.from_user.first_name else "Корбар"
        user_username = f"@{message.from_user.username}" if message.from_user.username else "Никнейм надорад"
    else:
        user_name = "Канал / Чат"
        user_username = "Аноним"

    # ==========================================
    # КОР КАРДАН БО ФИРИСТОДАНИ ПАЁМИ АДМИН (ЛС)
    # ==========================================
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

    if message.chat.type in ['group', 'supergroup']:
        groups = load_groups()
        if chat_id not in groups:
            groups[chat_id] = chat_title
            save_groups(groups)

    msg_text = get_message_text(message)

    # 1. САНҶИШИ АДМИН БУДАН
    is_admin = is_user_admin(message.chat.id, user_id, sender_chat)

    # ==========================================
    # КОРҲОИ АНТИСПАМ ВА АНТИДАШНОМ (БАРОИ КОРБАРОНИ ОДДӢ)
    # ==========================================
    if not is_admin and user_id:
        if user_id not in user_warnings:
            user_warnings[user_id] = {"bad_words": 0, "spam": 0}

        # А) САНҶИШИ КАЛИМАҲОИ НОҶО
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

        # Б) САНҶИШИ РЕКЛАМА ВА ССЫЛКАҲО
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
    # СИСТЕМАИ НАВИ АВТО-ОМӮЗИШ (REPLY LEARN)
    # ==========================================
    if message.chat.type in ['group', 'supergroup'] and message.content_type == 'text':
        text_clean = message.text.strip().lower()

        # А) ЁДГИРӢ: Агар паём ҷавоб (Reply) ба паёми дигар бошад
        if message.reply_to_message and message.reply_to_message.text:
            savol = message.reply_to_message.text.strip().lower()  # Паёми аввала (савол)
            javob = message.text.strip()  # Паёми навиштаи ҳозира (ҷавоб)

            # Шартҳо барои пешгирӣ аз сабти линк ё дашном ҳамчун ҷавоб
            if len(savol) > 1 and javob and not has_bad_words(javob) and not has_link(javob):
                if chat_id not in ANSWERS:
                    ANSWERS[chat_id] = {}
                
                # Сабти худкор ба базаи ҳамин чат
                ANSWERS[chat_id][savol] = javob
                save_answers()
                print(f"[Умумии Чат {chat_id}] Омӯхта шуд: {savol} -> {javob}")
                return

        # Б) ҶАВОБДИҲИИ АВТОМАТӢ: Агар касе паёме нависад, ки дар базаи ин чат ҳаст
        if chat_id in ANSWERS:
            # Аввал ҷустуҷӯ мекунем, ки оё ин паём дақиқ ҳамчун калиди савол сабт шудааст
            if text_clean in ANSWERS[chat_id]:
                auto_reply_text = ANSWERS[chat_id][text_clean]
                bot.reply_to(message, auto_reply_text)
                return
            
            # Агар дақиқ мувофиқат накунад, санҷиши калима ба калима дар матни саволҳо
            words = text_clean.split()
            for question, answer in ANSWERS[chat_id].items():
                if question in words:
                    bot.reply_to(message, answer)
                    break

# ==========================================
# 8. ОҒОЗИ КОР ВА БОТ ПОЛЛИНГ
# ==========================================
if __name__ == '__main__':
    # Flask-ро дар замина фаъол мекунем
    keep_alive()
    print("Веб-сервер бомуваффақият фаъол шуд!")
    
    # Корро оғоз кардани худи бот
    while True:
        try:
            print("Бот фаъол шуд ва ба кор омода аст...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠️ Хатогии корӣ: {e}")
            time.sleep(5)
