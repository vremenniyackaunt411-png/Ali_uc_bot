import os
import time
from threading import Thread
from flask import Flask
import telebot
import re

TOKEN = '8805476577:AAHlJF4UlB-n4bFRpMqKgj7WKqsXQp-LQqA'
# ИД-и телеграми худро дар инҷо нависед, то бот шуморо ҳамчун супер-админ шиносад
ADMIN_ID = 6871575684 

bot = telebot.TeleBot(TOKEN)

# ----------------- ҚИСМИ ВЕБ-СЕРВЕР БАРОИ RENDER -----------------
app = Flask('')

@app.route('/')
def home():
    return "Бот бо муваффақият кор карда истодааст ва порт зинда аст!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
# -----------------------------------------------------------------

# Базаи огоҳиҳои корбарон (дар хотира)
user_link_warnings = {}     # Огоҳиҳо барои ссылка ва никнейм (Блоки 24 соат)
user_badword_warnings = {}  # Огоҳиҳо барои калимаҳои бад (Блоки 1 соат)

# Ҷавобҳои бот
ANSWERS = {
    'salom': 'Воаллейкум салом ❤️',
    'салом': 'Салом! Хуш омадед ❤️',
    'ссалом': 'Салом! Хуш омадед ❤️',
    'сети': 'МАН ДАР СЕТАМ 24/7 🤯 ',
    'хуби': 'Хубам, раҳмат! 🤖. Шумо чихел?',
    'sozi': 'Хубам, раҳмат! 🤖. Шумо чихел?',
    'сози': 'Хубам, раҳмат! 🤖. Шумо чихел?',
    'юс': 'Барои нарх ба админ @ALI_UC_SHOPP ❤️ муроҷиат кунед.',
    'uc': 'Барои нарх ба админ @ALI_UC_SHOPP ❤️ муроҷиат кунед.',
    'админ': 'админ 👉 @ALI_UC_SHOPP ❤️ ',
    'admin': 'админ 👉 @ALI_UC_SHOPP ❤️ ',
    'нарх': 'нархо барои юс харидан дар инчо аст 👇 \n https://t.me/ALI_US_SHOPP/6311 ❤️',
    'narx': 'нархо барои юс харидан дар инчо аст 👇 \n https://t.me/ALI_US_SHOPP/6311 ❤️',
    'рахмат': 'САЛОМАТ БОШЕН 🤝',
    'ки мехара': '√1 ГАРАНТ @ALI_UC_SHOPP ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
    'хариданийм': '√1 ГАРАНТ @ALI_UC_SHOPP ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
    'фуруши дорм': '√1 ГАРАНТ @ALI_UC_SHOPP ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
    'мефурушм': '√1 ГАРАНТ @ALI_UC_SHOPP ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
    'мехарм': '√1 ГАРАНТ @ALI_UC_SHOPP ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
    'аккаунт': 'аккаунт харидан ё фурухтани бошен лс @ALI_UC_SHOPP ❤️ нависен',
    'акаунт': 'аккаунт харидан ё фурухтани бошен лс @ALI_UC_SHOPP ❤️ нависен',
    'бот': 'СаЛоМ. \nМан зехни сунъи хастам ёрдамчии @ALI_UC_SHOPP ❤️'
}

# Калимаҳои манъшуда
BAD_WORDS = [
    'кунте', 'кунти', 'гандон', 'сука', 'кс',
    'далбаёб',  'кер', 'гом', 'ks'
]

# Функсия барои санҷидани админ будани корбар
def is_admin(message):
    if message.chat.type == 'private':
        return False
    
    # Агар ID-и худи шумо бошад ё паём анонимӣ аз номи канал/чат бошад
    if message.from_user.id == ADMIN_ID or message.sender_chat is not None:
        return True
        
    try:
        member = bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in ['administrator', 'creator']:
            return True
    except Exception as e:
        print(f"Хатогӣ ҳангоми санҷиши админ: {e}")
    return False

# Санҷиши ссылка ва никнейм (@)
def has_link_or_nickname(message):
    if message.entities:
        for entity in message.entities:
            if entity.type in ['url', 'text_link', 'mention']:
                return True

    if message.text:
        text = message.text.lower()
        if "http" in text or "t.me" in text or "@" in text:
            return True

    return False

# Санҷиши калимаҳои манъшуда
def has_bad_words(text):
    if not text:
        return False
    text = text.lower()
    for word in BAD_WORDS:
        if word in text:
            return True
    return False

# Функсияи умумӣ барои блок (Restrict) кардани корбар ба вақти муайян
def restrict_user(chat_id, user_id, seconds):
    until_date = int(time.time()) + seconds
    permissions = telebot.types.ChatPermissions(
        can_send_messages=False, can_send_media_messages=False,
        can_send_audios=False, can_send_documents=False,
        can_send_photos=False, can_send_videos=False,
        can_send_video_notes=False, can_send_voice_notes=False,
        can_send_polls=False, can_send_other_messages=False,
        can_add_web_page_previews=False
    )
    bot.restrict_chat_member(chat_id, user_id, until_date=until_date, permissions=permissions)

# Коркарди паёмҳо
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def filter_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # АГАР АДМИН БОШАД - ҲЕҶ ЧИЗРО ТОЗА НАКУН
    if is_admin(message):
        if message.content_type == 'text':
            text = message.text.lower()
            for word, answer in ANSWERS.items():
                if word in text:
                    bot.reply_to(message, answer)
                    break
        return

    # 1. Корбарони оддӣ: Нест кардани ссылка ё никнейм (@) ва додани 3 ОГОҲӢ (Блоки 24 соат)
    if has_link_or_nickname(message):
        try:
            bot.delete_message(chat_id, message.message_id)
            
            if user_id not in user_link_warnings:
                user_link_warnings[user_id] = 0
            
            user_link_warnings[user_id] += 1
            
            if user_link_warnings[user_id] == 1:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, Ссылка ё никнейм манъ аст! Нагузоред, вагарна блок мешавед. Огоҳӣ: (1/3)"
                )
            elif user_link_warnings[user_id] == 2:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, бори дуюм аст! Огоҳии охирин: (2/3)"
                )
            elif user_link_warnings[user_id] >= 3:
                restrict_user(chat_id, user_id, 86400) # 24 соат блок
                bot.send_message(
                    chat_id, 
                    f"🚫 Корбар {user_name} қоидаро 3 бор шикаст ва барои спам ба муҳлати 24 соат блок шуд! Пас аз 24 соат худкор кушода мешавад."
                )
                user_link_warnings[user_id] = 0
        except Exception as e:
            print(f"Хатогӣ дар антиспам: {e}")
        return

    # 2. Корбарони оддӣ: Системаи 3 огоҳӣ барои калимаҳои бад (Блоки 1 соат)
    if message.content_type == 'text' and has_bad_words(message.text):
        try:
            bot.delete_message(chat_id, message.message_id)
            
            if user_id not in user_badword_warnings:
                user_badword_warnings[user_id] = 0
                
            user_badword_warnings[user_id] += 1
            
            if user_badword_warnings[user_id] == 1:
                bot.send_message(
                    chat_id,
                    f"⚠️ Корбар {user_name}, \n Дар гурух суханхои кабех ва дашном манъ аст! Огоҳӣ: (1/3)\nАДМИН: @ALI_UC_SHOPP ❤️"
                )
            elif user_badword_warnings[user_id] == 2:
                bot.send_message(
                    chat_id,
                    f"⚠️ Корбар {user_name}, \n Бори дуюм аст! Огоҳии охирин барои калимаҳои ноҷо: (2/3)"
                )
            elif user_badword_warnings[user_id] >= 3:
                restrict_user(chat_id, user_id, 3600) # 1 соат блок (3600 сония)
                bot.send_message(
                    chat_id,
                    f"🚫 Корбар {user_name} \n барои истифодаи суханхои кабех ё дашном ба муҳлати 1 соата блок шуд!"
                )
                user_badword_warnings[user_id] = 0
        except Exception as e:
            print(f"Хатогӣ дар тозакунии калимаҳо: {e}")
        return

    # 3. Ҷавоб додан ба саволҳои оддӣ
    if message.content_type == 'text':
        text = message.text.lower()
        for word, answer in ANSWERS.items():
            if word in text:
                bot.reply_to(message, answer)
                break

# Ба кор андохтани сервер ва бот якбора
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    
    print("🤖 Бот бомуваффақият кор карда истодааст...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
