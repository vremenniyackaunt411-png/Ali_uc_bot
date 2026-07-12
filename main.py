import os
from threading import Thread
from flask import Flask
import telebot

TOKEN = '8805476577:AAHlJF4UlB-n4bFRpMqKgj7WKqsXQp-LQqA'
bot = telebot.TeleBot(TOKEN)

# ----------------- ҚИСМИ ВЕБ-СЕРВЕР БАРОИ RENDER -----------------
app = Flask('')

@app.route('/')
def home():
    return "Бот бо муваффақият кор карда истодааст ва порт зинда аст!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
# ---------------- -------------------------------------------------

# Ҷавобҳои бот
ANSWERS = {
    'salom': 'Воаллейкум салом ❤️',
    'асалом': 'Салом! Хуш омадед ❤️',
    'хуби': 'Хубам, раҳмат! 🤖. Шумо чихелен',
    'sozi': 'Хубам, раҳмат! 🤖. Шумо чихелен',
    'сози': 'Хубам, раҳмат! 🤖. Шумо чихелен',
    'юс': 'Барои нарх ба админ @ALI_UC_SHOPP ❤️ муроҷиат кунед.',
    'uc': 'Барои нарх ба админ @ALI_UC_SHOPP ❤️ муроҷиат кунед.',
    'админ': 'админ 👉 @ALI_UC_SHOPP ❤️ ',
    'нарх': 'нархо барои юс харидан дар инчо аст 👇 \n https://t.me/ALI_US_SHOPP/6311 ❤️',
    'narx': 'нархо барои юс харидан дар инчо аст 👇 \n https://t.me/ALI_US_SHOPP/6311 ❤️',  # Вергул ислоҳ шуд
    'рахмат': 'САЛОМАТ БОШЕН 🤝',
    'аккаунт': 'аккаунт харидан ё фурухтани бошен лс @ALI_UC_SHOPP ❤️ нависен',
    'акаунт': 'аккаунт харидан ё фурухтани бошен лс @ALI_UC_SHOPP ❤️ нависен',
    'бот': 'СаЛоМ. \nМан зехни сунъи хастам ёрдамчии @ALI_UC_SHOPP ❤️?'
}

# Калимаҳои манъшуда
BAD_WORDS = [
    'кунте', 'кунти', 'гандон', 'сука', 'кс',
    'далбаёб', 'фуруши дорм', 'мефурушм',
    'ки мехара',
    'кер', 'мехарм', 'гом'
]

# Функсия барои санҷидани админ будани корбар
def is_admin(message):
    # Агар паём дар шабакаи шахсӣ (ЛС) бошад, филтр лозим нест
    if message.chat.type == 'private':
        return False
    
    # Агар аз номи худи канал ё анонимӣ навишта шуда бошад
    if message.sender_chat:
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
            # Илова кардани 'mention' барои никнеймҳо (@username)
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

# Коркарди паёмҳо
@bot.message_handler(func=lambda message: True, content_types=['text'])
def filter_messages(message):
    
    # АГАР АДМИН БОШАД - ҲЕҶ ЧИЗРО ТОЗА НАКУН
    if is_admin(message):
        # Танҳо ба калимаҳои оддии бот ҷавоб медиҳад ва тамом
        text = message.text.lower()
        for word, answer in ANSWERS.items():
            if word in text:
                bot.send_message(message.chat.id, answer)
                break
        return

    # Корбарони оддӣ: Нест кардани ссылка ё никнейм (@)
    if has_link_or_nickname(message):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "⚠️ Ссылка ё никнейм манъ аст!")
        except Exception as e:
            print(e)
        return

    # Корбарони оддӣ: Нест кардани калимаҳои бад
    if has_bad_words(message.text):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "🚫 Реклама ё калимаи манъшуда нест карда шуд.\nАДМИН: @ALI_UC_SHOPP ❤️")
        except Exception as e:
            print(e)
        return

    # Ҷавоб додан ба саволҳои корбарони оддӣ
    text = message.text.lower()
    for word, answer in ANSWERS.items():
        if word in text:
            bot.send_message(message.chat.id, answer)
            break

# Ба кор андохтани сервер ва бот якбора
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    
    print("🤖 Бот кор карда истодааст...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
