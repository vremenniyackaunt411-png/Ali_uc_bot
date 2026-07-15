import os
import time
import random
from threading import Thread
from flask import Flask
import telebot

TOKEN = '8805476577:AAHlJF4UlB-n4bFRpMqKgj7WKqsXQp-LQqA'
# ИД-и телеграми шумо (Супер-Админ)
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
user_badword_warnings = {}  # Огоҳиҳо барои калимаҳои бад (Блоки 8 соат)

# Базаи динамикии админҳо: {chat_id: {"username": "@nick", "last_time": timestamp}}
last_group_admins = {}

# Калимаҳои манъшуда
BAD_WORDS = [
    'кунте', 'кунти', 'гандон', 'сука', 'кс',
    'далбаёб',  'кер', 'гом', 'ks', 'сина'
]

# Функсия барои гузоштани реаксия ба паём
def send_reaction(chat_id, message_id, emoji):
    try:
        # Истифодаи методи расмии Telegram барои реаксияҳо
        bot.set_message_reaction(
            chat_id=chat_id,
            message_id=message_id,
            reaction=[telebot.types.ReactionTypeEmoji(emoji)]
        )
    except Exception as e:
        print(f"Хатогӣ ҳангоми гузоштани реаксия: {e}")

# Функсия барои муайян кардани никнейми админ (бо назардошти лимити 48 соат)
def get_admin_mention(chat_id):
    data = last_group_admins.get(chat_id)
    if data:
        # 48 соат = 172800 сония
        if time.time() - data['last_time'] < 172800:
            return data['username']
    return "АДМИН"

# Саволҳо ва ҷавобҳои динамикии бот
def get_answers(chat_id):
    admin = get_admin_mention(chat_id)
    return {
        'salom': 'Воаллейкум салом !',
        'салом': 'Салом! Хушхолам шуморо мебинам 🫶',
        'ссалом': 'ВОАЛЛЕЙКУМ САЛОМ ! Хуш омадед ❤️',
        'сети': 'МАН ДАР СЕТАМ 24/7 🥰 \nБарои мухофизати гурух сохта шудаам. ',
        'хуби': 'Хубам, раҳмат! 🥰. Шумо чихел?',
        'sozi': 'Хубам, раҳмат! 🥰. Шумо чихел?',
        'сози': 'Хубам, раҳмат! 🥰. Шумо чихел?',
        'юс': f'Барои нарх ба {admin}  муроҷиат кунед.',
        'uc': f'Барои нарх ба {admin}  муроҷиат кунед.',
        'админ': f'ба {admin}  муроҷиат кунед.',
        'admin': f'ба {admin}  муроҷиат кунед.',
        'нарх': f'нархо барои барои харидани юс  {admin} ❤️',
        'narx': f'нархо барои барои харидани юс  {admin} ❤️',
        'рахмат': 'САЛОМАТ БОШЕН 🫶',
        'ки мехара': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'хариданийм': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'фуруши дорм': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'мефурушм': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'мехарм': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'аккаунт': f'аккаунт харидан ё фурухтани бошен лс {admin} ❤️ нависен',
        'акаунт': f'аккаунт харидан ё фурухтани бошен лс {admin} ❤️ нависен',
        'бот': f'СаЛоМ. \nМан зехни сунъи хастам ёрдамчии {admin} ❤️'
    }

# Функсия барои санҷидани админ будани корбар
def is_admin(message):
    if message.chat.type == 'private':
        return False
    
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
def find_bad_word(text):
    if not text:
        return None
    text = text.lower()
    for word in BAD_WORDS:
        if word in text:
            return word
    return None

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
    username = f"@{message.from_user.username}" if message.from_user.username else "Никнейм надорад"

    admin_status = is_admin(message)

    # 1. Агар паём аз ҷониби АДМИН бошад:
    if admin_status:
        # Никнейми ӯ ва вақти паёмро барои ин гурӯҳ сабт мекунем (барои 48 соат)
        if message.from_user.username:
            last_group_admins[chat_id] = {
                "username": f"@{message.from_user.username}",
                "last_time": time.time()
            }
        
        # Санҷиши дашномҳои худи админ (танҳо реаксияи ҳайрат мегузорем, паёмро тоза намекунем)
        if message.content_type == 'text':
            detected_bad_word = find_bad_word(message.text)
            if detected_bad_word:
                send_reaction(chat_id, message.message_id, "😱")
                return

        # Ҷавоб додан ба калимаҳои калидии админ ва гузоштани реаксияи мувофиқ
        if message.content_type == 'text':
            text = message.text.lower()
            answers = get_answers(chat_id)
            for word, answer in answers.items():
                if word in text:
                    # Вобаста ба калима реаксия мегузорем
                    if 'салом' in word or 'salom' in word:
                        send_reaction(chat_id, message.message_id, random.choice(["❤️", "🔥", "👍"]))
                    elif 'рахмат' in word:
                        send_reaction(chat_id, message.message_id, "🤝")
                    
                    bot.reply_to(message, answer)
                    break
        return

    # 2. Агар паём аз ҷониби КОРБАРИ ОДДӢ бошад:

    # А) Санҷиши антиспам (ссылка ва никнеймҳо)
    if has_link_or_nickname(message):
        try:
            bot.delete_message(chat_id, message.message_id)
            
            if user_id not in user_link_warnings:
                user_link_warnings[user_id] = 0
            
            user_link_warnings[user_id] += 1
            
            if user_link_warnings[user_id] == 1:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, Ссылка ё реклама манъ аст! Нагузоред, вагарна блок мешавед. Огоҳӣ: (1/3)"
                )
            elif user_link_warnings[user_id] == 2:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, бори дуюм аст ки огохи гирифтед! Огоҳии охирин: (2/3)"
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

    # Б) Санҷиши калимаҳои ноҷо (Дашномҳо)
    if message.content_type == 'text':
        detected_bad_word = find_bad_word(message.text)
        if detected_bad_word:
            try:
                bot.delete_message(chat_id, message.message_id)
                
                # Фиристодани отчёт ба личкаи супер-админ
                group_title = message.chat.title if message.chat.title else "Гурӯҳи хусусӣ"
                report_message = (
                    f"🚨 **Дашном ошкор шуд!**\n\n"
                    f"👥 **Гурӯҳ:** {group_title} (ID: `{chat_id}`)\n"
                    f"👤 **Нависанда:** {user_name} ({username}) (ID: `{user_id}`)\n"
                    f"🤬 **Калимаи ёфтшуда:** `{detected_bad_word}`\n"
                    f"📝 **Паёми пурра:**\n_\"{message.text}\"_"
                )
                
                try:
                    bot.send_message(ADMIN_ID, report_message, parse_mode="Markdown")
                except Exception as send_err:
                    print(f"Хатогӣ ҳангоми фиристодани отчёт ба админ: {send_err}")

                if user_id not in user_badword_warnings:
                    user_badword_warnings[user_id] = 0
                    
                user_badword_warnings[user_id] += 1
                
                current_admin = get_admin_mention(chat_id)
                if user_badword_warnings[user_id] == 1:
                    bot.send_message(
                        chat_id,
                        f"⚠️ Корбар {user_name}, \n Дар гурух суханхои кабех ва дашном манъ аст! Огоҳӣ: (1/3)\nАДМИН: {current_admin} ❤️"
                    )
                elif user_badword_warnings[user_id] == 2:
                    bot.send_message(
                        chat_id,
                        f"⚠️ Корбар {user_name}, \n Бори дуюм аст! Огоҳии охирин барои калимаҳои ноҷо: (2/3)"
                    )
                elif user_badword_warnings[user_id] >= 3:
                    restrict_user(chat_id, user_id, 28800) # 8 соат блок
                    bot.send_message(
                        chat_id,
                        f"🚫 Корбар {user_name} \n барои истифодаи суханхои кабех ё дашном ба муҳлати 8 соат блок шуд!"
                    )
                    user_badword_warnings[user_id] = 0
            except Exception as e:
                print(f"Хатогӣ дар тозакунии калимаҳо: {e}")
            return

    # В) Ҷавоб додан ба саволҳои оддӣ ва гузоштани реаксияҳо
    if message.content_type == 'text':
        text = message.text.lower()
        answers = get_answers(chat_id)
        
        for word, answer in answers.items():
            if word in text:
                # Гузоштани реаксия ба паёми корбар пеш аз ҷавоб додан
                if 'салом' in word or 'salom' in word:
                    send_reaction(chat_id, message.message_id, random.choice(["❤️", "🔥", "👍"]))
                elif 'рахмат' in word:
                    send_reaction(chat_id, message.message_id, "🤝")
                elif 'юс' in word or 'uc' in word or 'нарх' in word:
                    send_reaction(chat_id, message.message_id, "⚡")
                
                bot.reply_to(message, answer)
                return  # Корро ба охир мерасонем, то ба бахши рандом нагузарад

        # Г) Баъзан ба таври тасодуфӣ (рандом - 10% имконият) ба паёмҳои оддӣ реаксияи хуб мегузорад
        if random.random() < 0.10:
            random_emoji = random.choice(["👍", "❤️", "🔥", "🥰", "🫶", "😂", "🤯", "🩵", "🎉", "😎"])
            send_reaction(chat_id, message.message_id, random_emoji)

# Ба кор андохтани сервер ва бот якбора
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    
    print("🤖 Бот бомуваффақият кор карда истодааст...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
