import telebot
from telebot import types

# Айдии админии шумо
ADMIN_ID = 6871575684  
# Токени боти шумо
TOKEN = "8660164143:AAGL13-xIC2pln1JKKYiPQagb2dzn6N9hhQ"

bot = telebot.TeleBot(TOKEN)

# Махзани маълумоти муваққатӣ
user_data = {}
user_review_attempts = {}

UC_PACKAGES = {
    "60": "10 сомонӣ", "120": "20 сомонӣ", "180": "30 сомонӣ",
    "325": "48 сомонӣ", "385": "58 сомонӣ", "660": "92 сомонӣ",
    "720": "102 сомонӣ", "1320": "184 сомонӣ", "1800": "240 сомонӣ",
    "3850": "450 сомонӣ", "8100": "870 сомонӣ"
}

# 1. Менюи асосӣ (/start)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    if chat_id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📦 Заказҳо", "🌟 Отзывҳо")
        markup.row("⚙️ Танзими ЮС")
        bot.send_message(chat_id, "Хуш омадед, Админ!", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🛒 Харидани UC", callback_data="buy_uc_menu"),
            types.InlineKeyboardButton("📦 Заказҳои ман", callback_data="my_orders"),
            types.InlineKeyboardButton("🌟 Отзывҳо", callback_data="view_reviews"),
            types.InlineKeyboardButton("📞 Алоқа бо админ", callback_data="contact_admin")
        )
        bot.send_message(chat_id, "Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥", reply_markup=markup, parse_mode="Markdown")

# Идоракунии ҳамаи тугмаҳо (Callback Query)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    if call.data == "buy_uc_menu":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        for uc, price in UC_PACKAGES.items():
            markup.add(types.InlineKeyboardButton(f"💎 {uc} UC — {price}", callback_data=f"select_uc_{uc}"))
        markup.row(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
        bot.edit_message_text("🛒 Пакети худро интихоб кунед:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "contact_admin":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
        bot.edit_message_text("📞 **Алоқа бо админ:**\n\nДар ҳамин ҷо паём, савол ё акси худро нависед. Админ дар вақти кӯтоҳтарин ба шумо ҷавоб медиҳад! 👇", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        if chat_id not in user_data: user_data[chat_id] = {}
        user_data[chat_id]["waiting_for_admin_message"] = True

    elif call.data == "user_main_menu":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🛒 Харидани UC", callback_data="buy_uc_menu"),
            types.InlineKeyboardButton("📦 Заказҳои ман", callback_data="my_orders"),
            types.InlineKeyboardButton("🌟 Отзывҳо", callback_data="view_reviews"),
            types.InlineKeyboardButton("📞 Алоқа бо админ", callback_data="contact_admin")
        )
        bot.edit_message_text("Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    
    elif call.data.startswith("select_uc_"):
        uc_amount = call.data.split("_")[2]
        user_data[chat_id] = {"package": f"{uc_amount} UC", "price": UC_PACKAGES[uc_amount], "waiting_for_id": True}
        bot.answer_callback_query(call.id)
        bot.edit_message_text(f"Шумо {uc_amount} UC интихоб кардед. Лутфан, **PUBG ID**-и худро нависед:", chat_id, call.message.message_id, parse_mode="Markdown")

    elif call.data.startswith("reply_"):
        user_id = call.data.split("_")[1]
        msg = bot.send_message(ADMIN_ID, "Нависед ҷавобро барои корбар:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(user_id, f"📢 **Ҷавоб аз Админ:**\n\n{m.text}"))

# Қабули паём барои админ (матн ё расм)
@bot.message_handler(content_types=['text', 'photo'], func=lambda m: m.chat.id in user_data and user_data[m.chat.id].get("waiting_for_admin_message"))
def handle_admin_msg(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ Ҷавоб додан", callback_data=f"reply_{chat_id}"))
    
    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"📩 Паём аз @{message.from_user.username or chat_id}:\n{message.text}", reply_markup=markup)
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 Расм аз @{message.from_user.username or chat_id}", reply_markup=markup)
    
    bot.reply_to(message, "Паём ба админ фиристода шуд! ✅")
    user_data[chat_id].pop("waiting_for_admin_message")

bot.infinity_polling()
