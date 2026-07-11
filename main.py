import telebot

TOKEN = '8805476577:AAH4RbU4bMuAJlHT7RtuP6E6Kyb5Aj3Rcqg'

bot = telebot.TeleBot(TOKEN)

# Ҷавобҳои бот
ANSWERS = {
'salom': 'Воаллейкум салом ❤️',
    'салом': 'Салом! Хуш омадед 😊',
    'хуби': 'Хубам, раҳмат! 🤖. Шумо чихелен',
       'sozi': 'Хубам, раҳмат! 🤖. Шумо чихелен',
    'юс': 'Барои нарх ба админ @ALI_UC_SHOPP ❤️  муроҷиат кунед.',
    'админ': 'админ @ALI_UC_SHOPP ❤️ ',
    'рахмат': 'саломат бошен 😊',
    'аккаунт': 'аккаунт харидани ё фурухтани бошен лс @ALI_UC_SHOPP ❤️ нависен',
    'бот': 'СаЛоМ. манро @ALI_UC_SHOPP ❤️ сохтааст. Ягон гуфтани доштед?'
}

# Калимаҳои манъшуда
BAD_WORDS = [
    'кун', 'гандон', 'сука', 'кс',
    'далбаёб', 'фуруши дорм',
    'ки мехара', 'мегом',
    'кер', 'керм', 'мехарм', 'гом'
]


# Санҷиши ссылка
def has_link(message):
    if message.entities:
        for entity in message.entities:
            if entity.type in ['url', 'text_link']:
                return True

    if message.text:
        text = message.text.lower()
        if "http" in text or "t.me" in text:
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

    # Нест кардани ссылка
    if has_link(message):
        try:
            bot.delete_message(
                message.chat.id,
                message.message_id
            )

            bot.send_message(
                message.chat.id,
                "⚠️ Ссылка манъ аст!"
            )

        except Exception as e:
            print(e)

        return


    # Нест кардани калимаҳои бад
    if has_bad_words(message.text):
        try:
            bot.delete_message(
                message.chat.id,
                message.message_id
            )

            bot.send_message(
                message.chat.id,
                "🚫 Реклама ё калимаи манъшуда нест карда шуд.\nАДМИН: @ALI_UC_SHOPP ❤️"
            )

        except Exception as e:
            print(e)

        return


    # Ҷавоб додан ба саволҳо
    text = message.text.lower()

    for word, answer in ANSWERS.items():
        if word in text:
            bot.send_message(
                message.chat.id,
                answer
            )
            break



print("🤖 Бот кор карда истодааст...")

bot.infinity_polling()
