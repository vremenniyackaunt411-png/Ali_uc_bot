import telebot  
import re
import json
import os
import time  
from telebot import types

TOKEN = "8805476577:AAHlJF4UlB-n4bFRpMqKgj7WKqsXQp-LQqA"
bot = telebot.TeleBot(TOKEN)

# ==========================================
# ID-И СОЗАНДАИ БОТ
# ==========================================
OWNER_ID = 6871575684  

# ==========================
# Файлҳо барои нигоҳдории маълумот
# ==========================
WARN_FILE = "warnings.json"
GROUPS_FILE = "groups.json"

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Хатогии хондани {filename}: {e}")
            return {}
    return {}

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Хатогии сабти {filename}: {e}")

warnings = load_json(WARN_FILE)
groups_db = load_json(GROUPS_FILE)  

# ==========================
# Ҷавобҳои автоматӣ
# ==========================
ANSWERS = {
    'салом': 'Салом! Хушхолам шуморо мебинам 🫶',
    'ссалом': 'ВОАЛЛЕЙКУМ САЛОМ ! Хуш омадед ❤️',
    'сети': 'МАН ДАР СЕТАМ 24/7 🥰 \nБарои мухофизати гурух сохта шудаам. ',
    'хуби': 'Хубам, раҳмат! 🥰. Шумо чихел?',
    'sozi': 'Хубам, раҳмат! 🥰. Шумо чихел?',
    'сози': 'Хубам, раҳмат! 🥰. Шумо чихел?',
    'юс': 'Барои нарх ба админи гурух муроҷиат кунед.',
    'uc': 'Барои нарх ба админи гурух муроҷиат кунед.',
    'рахмат': 'САЛОМАТ БОШЕН 🫶',
    'бот': 'СаЛоМ. \nМан зехни сунъи хастам ёрдамчии админи гурух ❤️ хастам'
}

# ==========================
# Калимаҳои манъшуда
# ==========================
BAD_WORDS = [
    'кунте', 'кунти', 'гандон', 'сука',
    'далбаёб', 'кери', 'керм', 'мегом', 'бгом', 'гойда', 'сина'
]

def has_bad_words(text):
    if not text:
        return False
    text = text.lower()
    for word in BAD_WORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", text):
            return True
    return False

def has_link(message):
    if message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link"]:
                return True
    if message.text:
        text = message.text.lower()
        links = ["http", "https", "t.me", "telegram.me", "wa.me", "bit.ly"]
        for link in links:
            if link in text:
                return True
    return False

def has_username(text):
    if not text:
        return False
    return bool(re.search(r"@\w+", text))

def is_forward(message):
    return bool(message.forward_date or message.forward_from or message.forward_from_chat)

# ==========================
# САБТИ АВТОМАТИИ ГУРӮҲҲО
# ==========================
def register_group(chat):
    global groups_db
    groups_db = load_json(GROUPS_FILE)
    chat_id = str(chat.id)
    if chat_id not in groups_db:
        groups_db[chat_id] = chat.title
        save_json(GROUPS_FILE, groups_db)

@bot.message_handler(content_types=["new_chat_members"])
def welcome_new_member(message):
    register_group(message.chat)
    
    for new_user in message.new_chat_members:
        if new_user.id == bot.get_me().id:
            continue
            
        user_name = new_user.first_name
        welcome_text = (
            f"👤 **{user_name}**, хуш омадед ба гурӯҳи мо! 🎉\n\n"
            f"ℹ️ **Қоидаҳои гурӯҳ:**\n"
            f"1. Фристодани ҳар гуна Ссылка (Линк) ва Реклама манъ аст! 🚫\n"
            f"2. Истифодаи никнеймҳо (@) ва дашном додан манъ аст! 🤬\n"
            f"3. Переслать (Forward) кардани паёмҳо аз дигар чатҳо манъ аст! 📦\n\n"
            f"Лутфан қоидаҳоро риоя кунед, то аз тарафи бот маҳдуд (блок) нашавед! 🤝"
        )
        bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

@bot.message_handler(content_types=["left_chat_member"])
def delete_left_member_message(message):
    try:
        if message.left_chat_member.id == bot.get_me().id:
            global groups_db
            groups_db = load_json(GROUPS_FILE)
            chat_id = str(message.chat.id)
            if chat_id in groups_db:
                del groups_db[chat_id]
                save_json(GROUPS_FILE, groups_db)
            return
            
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Хатогии нест кардани паёми баромадан: {e}")

# ==========================================
# МЕНЮИ ЛИЧКАИ БОТ (ИДОРАКУНИИ ТУГМАҲО)
# ==========================================
@bot.message_handler(commands=["start"])
def start(message):
    if message.chat.type != "private":
        return

    # Ислоҳ шуд: Акнун тугмаҳои изофӣ нест карда шуданд
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_add = types.KeyboardButton("➕ Илова ба гурӯҳ")
    markup.add(btn_add)

    if message.from_user.id == OWNER_ID:
        btn_groups = types.KeyboardButton("👑 Гурӯҳҳои пайвастшуда")
        markup.add(btn_groups)

    bot.send_message(
        message.chat.id,
        f"Салом, {message.from_user.first_name}! 🤖\n\n"
        "Ман боти назоратчии гурӯҳ ҳастам. Лутфан тугмаи дилхоҳро пахш кунед 👇",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "➕ Илова ба гурӯҳ" and message.chat.type == "private")
def add_to_group_info(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(
        "➕ Илова ба гурӯҳ",
        url=f"https://t.me/{bot.get_me().username}?startgroup=true"
    )
    markup.add(btn)
    bot.send_message(
        message.chat.id,
        "Барои илова кардани бот ба гурӯҳи худ, тугмаи зеринро пахш кунед:",
        reply_markup=markup
    )

# ==========================================
# ИДОРАКУНИИ ГУРӮҲҲО БАРОИ СОЗАНДА
# ==========================================
@bot.message_handler(func=lambda message: message.text == "👑 Гурӯҳҳои пайвастшуда" and message.chat.type == "private")
def show_owner_groups(message):
    if message.from_user.id != OWNER_ID:
        return

    global groups_db
    groups_db = load_json(GROUPS_FILE)

    if not groups_db:
        bot.send_message(message.chat.id, "❌ Ҳоло бот ба ягон гурӯҳ илова нашудааст.")
        return

    markup = types.InlineKeyboardMarkup()
    for gid, title in groups_db.items():
        btn = types.InlineKeyboardButton(f"📁 {title}", callback_data=f"manage_{gid}")
        markup.add(btn)

    bot.send_message(message.chat.id, "📋 Як гурӯҳро барои идоракунӣ интихоб кунед:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != OWNER_ID:
        return

    data = call.data

    if data.startswith("manage_"):
        gid = data.split("_")[1]
        group_name = groups_db.get(gid, "Гурӯҳи номаълум")

        markup = types.InlineKeyboardMarkup()
        btn_write = types.InlineKeyboardButton("✍️ Паём навиштан", callback_data=f"write_{gid}")
        btn_leave = types.InlineKeyboardButton("🚶‍♂️ Покинул группу", callback_data=f"leave_{gid}")
        btn_back = types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="back_to_list")
        markup.add(btn_write, btn_leave)
        markup.add(btn_back)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⚙️ Идоракунии гурӯҳи: **{group_name}**\nID: `{gid}`\n\nЧи кор кардан мехоҳед?",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif data == "back_to_list":
        global groups_db
        groups_db = load_json(GROUPS_FILE)
        markup = types.InlineKeyboardMarkup()
        for gid, title in groups_db.items():
            btn = types.InlineKeyboardButton(f"📁 {title}", callback_data=f"manage_{gid}")
            markup.add(btn)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📋 Як гурӯҳро барои идоракунӣ интихоб кунед:",
            reply_markup=markup
        )

    elif data.startswith("leave_"):
        gid = int(data.split("_")[1])
        group_name = groups_db.get(str(gid), "Гурӯҳ")
        try:
            bot.leave_chat(gid)
            bot.answer_callback_query(call.id, f"Бот гурӯҳи {group_name}-ро тарк кард.")
            
            groups_db = load_json(GROUPS_FILE)
            if str(gid) in groups_db:
                del groups_db[str(gid)]
                save_json(GROUPS_FILE, groups_db)
                
            callback_handler(types.CallbackQuery(call.id, call.from_user, call.message, "back_to_list", call.chat_instance))
        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ Хатогӣ ҳангоми баромадан аз гурӯҳ: {e}")

    elif data.startswith("write_"):
        gid = data.split("_")[1]
        msg = bot.send_message(call.message.chat.id, "✍️ Паёмеро, ки ба ин гурӯҳ фиристодан мехоҳед, нависед:")
        bot.register_next_step_handler(msg, send_msg_to_group, gid)

def send_msg_to_group(message, gid):
    try:
        bot.send_message(int(gid), message.text)
        bot.send_message(message.chat.id, "✅ Паёми шумо бомуваффақият ба гурӯҳ фиристода шуд!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Хатогӣ дар фиристодани паём: {e}")

# ==========================
# ОГОҲИИ СУХАНИ НОҶО БА ШУМО (OWNER)
# ==========================
def add_warning(message, reason):
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)
    key = f"{chat_id}_{user_id}"

    global warnings
    warnings = load_json(WARN_FILE)

    if key not in warnings:
        warnings[key] = 0

    warnings[key] += 1
    save_json(WARN_FILE, warnings)

    count = warnings[key]

    if reason == "Сухани манъшуда":
        try:
            notification_text = (
                f"🚨 **СУХАНИ НОҶО ДАР ГУРӮҲ!**\n\n"
                f"📍 Гурӯҳ: {message.chat.title} (ID: `{message.chat.id}`)\n"
                f"👤 Корбар: {message.from_user.first_name} (@{message.from_user.username if message.from_user.username else 'бе_никнейм'})\n"
                f"📝 Паёми навишташуда: `{message.text}`"
            )
            bot.send_message(OWNER_ID, notification_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Хатогии фиристодани огоҳинома ба созанда: {e}")

    if count < 3:
        bot.reply_to(
            message,
            f"⚠️ Огоҳӣ {count}/3\n"
            f"Сабаб: {reason}\n"
            f"Бори дигар такрор шавад, маҳдуд мешавед."
        )
    else:
        if reason == "Сухани манъшуда":
            seconds_to_mute = 8 * 3600  
        else:
            seconds_to_mute = 24 * 3600  

        until_timestamp = int(time.time() + seconds_to_mute)

        try:
            permissions = types.ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            )
            
            bot.restrict_chat_member(
                message.chat.id,
                message.from_user.id,
                until_date=until_timestamp,
                permissions=permissions
            )

            bot.send_message(
                message.chat.id,
                f"🚫 Корбар {message.from_user.first_name} "
                f"ба муддати {int(seconds_to_mute/3600)} соат маҳдуд шуд."
            )

            warnings[key] = 0
            save_json(WARN_FILE, warnings)

        except Exception as e:
            print(f"Хатогӣ дар иҷрои restrict_chat_member: {e}")

# ==========================
# Коркарди ҳамаи паёмҳо
# ==========================
@bot.message_handler(
    func=lambda message: True,
    content_types=["text"]
)
def check_messages(message):
    if message.chat.type == "private":
        text = message.text.lower()
        for word, answer in ANSWERS.items():
            if word in text:
                bot.reply_to(message, answer)
                return
        return

    register_group(message.chat)

    try:
        member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in ["administrator", "creator"]:
            return
    except Exception as e:
        print(f"Хатогӣ ҳангоми санҷиши ҳуқуқи admin: {e}")

    if has_link(message):
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        add_warning(message, "Ссылка")
        return

    if has_username(message.text):
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        add_warning(message, "Никнейм")
        return

    if is_forward(message):
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        add_warning(message, "Пересланный паём")
        return

    if has_bad_words(message.text):
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        add_warning(message, "Сухани манъшуда")
        return

    text = message.text.lower()
    for word, answer in ANSWERS.items():
        if word in text:
            bot.reply_to(message, answer)
            break

# ==========================
# Запуск
# ==========================
if __name__ == "__main__":
    print("🤖 Бот бомуваффақият оғоз ёфт ва фаъол аст...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
