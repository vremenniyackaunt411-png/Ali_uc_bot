import telebot
import re
import json
import os
from telebot import types
from datetime import datetime, timedelta

TOKEN = "8805476577:AAHlJF4UlB-n4bFRpMqKgj7WKqsXQp-LQqA"

bot = telebot.TeleBot(TOKEN)


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
        'uc': f'Барои нарх ба админи гурух муроҷиат кунед.',
        'рахмат': 'САЛОМАТ БОШЕН 🫶',
        'бот': f'СаЛоМ. \nМан зехни сунъи хастам ёрдамчии админи гурух ❤️ хастам'
}


# ==========================
# Калимаҳои манъшуда
# ==========================

BAD_WORDS = [
'кунте', 'кунти', 'гандон', 'сука',
    'далбаёб', 'кери', 'керм', 'мегом', 'бгом', 'гойда', 'сина'
]


# ==========================
# Файл барои нигоҳ доштани огоҳӣ
# ==========================

WARN_FILE = "warnings.json"


def load_warns():
    if os.path.exists(WARN_FILE):
        with open(WARN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}


def save_warns(data):
    with open(WARN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


warnings = load_warns()


# ==========================
# Санҷиши калимаҳои бад
# ==========================

def has_bad_words(text):

    if not text:
        return False

    text = text.lower()

    for word in BAD_WORDS:
        if re.search(r"\b" + word + r"\b", text):
            return True

    return False


# ==========================
# Санҷиши ссылка
# ==========================

def has_link(message):

    if message.entities:
        for entity in message.entities:
            if entity.type in ["url", "text_link"]:
                return True

    if message.text:
        text = message.text.lower()

        links = [
            "http",
            "https",
            "t.me",
            "telegram.me",
            "wa.me",
            "bit.ly"
        ]

        for link in links:
            if link in text:
                return True

    return False


# ==========================
# Санҷиши никнейм
# ==========================

def has_username(text):

    if not text:
        return False

    return bool(re.search(r"@\w+", text))


# ==========================
# Санҷиши пересланный паём
# ==========================

def is_forward(message):

    if message.forward_date:
        return True

    return False


# ==========================
# START
# ==========================

@bot.message_handler(commands=["start"])
def start(message):

    markup = types.InlineKeyboardMarkup()

    btn = types.InlineKeyboardButton(
        "➕ Илова ба гурӯҳ",
        url=f"https://t.me/{bot.get_me().username}?startgroup=true"
    )

    markup.add(btn)

    bot.send_message(
        message.chat.id,
        "🤖 Салом! Ман боти муҳофизати гурӯҳ ҳастам.\n\n"
        "Ман ссылка, никнейм, пересланный паём ва суханҳои манъшударо назорат мекунам.",
        reply_markup=markup
    )


print("Қисми 1 тайёр шуд...")
# ==========================
# Илова кардани огоҳӣ
# ==========================

def add_warning(message, reason):

    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    key = f"{chat_id}_{user_id}"

    if key not in warnings:
        warnings[key] = 0

    warnings[key] += 1

    save_warns(warnings)

    count = warnings[key]

    # Огоҳии 1 ва 2
    if count < 3:

        bot.reply_to(
            message,
            f"⚠️ Огоҳӣ {count}/3\n"
            f"Сабаб: {reason}\n"
            f"Бори дигар такрор шавад, маҳдуд мешавед."
        )

    else:

        # Муайян кардани вақт
        if reason == "Сухани манъшуда":
            mute_time = timedelta(hours=8)
        else:
            mute_time = timedelta(hours=24)


        until = datetime.now() + mute_time


        try:
            bot.restrict_chat_member(
                message.chat.id,
                message.from_user.id,
                until_date=until,
                can_send_messages=False
            )


            bot.send_message(
                message.chat.id,
                f"🚫 Корбар {message.from_user.first_name} "
                f"ба муддати {int(mute_time.total_seconds()/3600)} соат маҳдуд шуд."
            )


            warnings[key] = 0
            save_warns(warnings)


        except Exception as e:
            print(e)



# ==========================
# Коркарди ҳамаи паёмҳо
# ==========================

@bot.message_handler(
    func=lambda message: True,
    content_types=["text"]
)
def check_messages(message):

    # Агар админ бошад - санҷиш намекунем
    try:
        member = bot.get_chat_member(
            message.chat.id,
            message.from_user.id
        )

        if member.status in ["administrator", "creator"]:
            return

    except:
        pass


    # Ссылка
    if has_link(message):

        try:
            bot.delete_message(
                message.chat.id,
                message.message_id
            )
        except:
            pass


        add_warning(
            message,
            "Ссылка"
        )

        return



    # Никнейм
    if has_username(message.text):

        try:
            bot.delete_message(
                message.chat.id,
                message.message_id
            )
        except:
            pass


        add_warning(
            message,
            "Никнейм"
        )

        return



    # Пересланный паём
    if is_forward(message):

        try:
            bot.delete_message(
                message.chat.id,
                message.message_id
            )
        except:
            pass


        add_warning(
            message,
            "Пересланный паём"
        )

        return



    # Калимаҳои бад
    if has_bad_words(message.text):

        try:
            bot.delete_message(
                message.chat.id,
                message.message_id
            )
        except:
            pass


        add_warning(
            message,
            "Сухани манъшуда"
        )

        return



    # Ҷавобҳои бот
    text = message.text.lower()


    for word, answer in ANSWERS.items():

        if word in text:

            bot.reply_to(
                message,
                answer
            )

            break



# ==========================
# Запуск
# ==========================

print("🤖 Бот 24/7 фаъол аст...")

bot.infinity_polling()
