import telebot
from telebot import types

# 1. Танзимот
TOKEN = "8660164143:AAGL13-xIC2pln1JKKYiPQagb2dzn6N9hhQ"
# ИН ҶО ID-И ШАХСИИ ХУДРО АЗ @userinfobot ГИРИФТА МОНЕД:
ADMIN_ID = 6871575684 

bot = telebot.TeleBot(TOKEN)

# Базаи маълумот
user_data = {}
user_review_attempts = {}
UC_PACKAGES = {
    "60": "10 сомонӣ", "120": "20 сомонӣ", "180": "30 сомонӣ",
    "325": "48 сомонӣ", "385": "58 сомонӣ", "660": "92 сомонӣ",
    "720": "102 сомонӣ", "1320": "184 сомонӣ", "1800": "240 сомонӣ",
    "3850": "450 сомонӣ", "8100": "870 сомонӣ"
}

# --- МЕНЮИ АСОСӢ ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📦 Заказҳо", "🌟 Отзывҳо", "⚙️ Танзими ЮС")
        bot.send_message(message.chat.id, "Хуш омадед, Админ!", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🛒 Харидани UC", callback_data="buy_uc_menu"),
            types.InlineKeyboardButton("📦 Заказҳои ман", callback_data="my_orders"),
            types.InlineKeyboardButton("🌟 Отзывҳо", callback_data="view_reviews"),
            types.InlineKeyboardButton("📞 Алоқа бо админ", callback_data="contact_admin")
        )
        bot.send_message(message.chat.id, "Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥", reply_markup=markup, parse_mode="Markdown")

# --- ПАНЕЛИ АДМИН ---
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.text in ["📦 Заказҳо", "🌟 Отзывҳо", "⚙️ Танзими ЮС"])
def admin_panel(message):
    bot.send_message(ADMIN_ID, f"Шумо дар бахши {message.text} ҳастед.")

# --- CALLBACKS (ТУГМАҲО) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == "buy_uc_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for uc, price in UC_PACKAGES.items():
            markup.add(types.InlineKeyboardButton(f"💎 {uc} UC — {price}", callback_data=f"select_uc_{uc}"))
        bot.edit_message_text("🛒 Пакети худро интихоб кунед:", chat_id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "contact_admin":
        if chat_id not in user_data: user_data[chat_id] = {}
        user_data[chat_id]["waiting_for_admin_message"] = True
        bot.edit_message_text("📞 Паём ё саволи худро нависед, админ ҷавоб медиҳад:", chat_id, call.message.message_id)

    elif call.data.startswith("select_uc_"):
        uc_amount = call.data.split("_")[2]
        user_data[chat_id] = {"package": f"{uc_amount} UC", "price": UC_PACKAGES[uc_amount], "waiting_for_id": True}
        bot.edit_message_text(f"Шумо {uc_amount} UC интихоб кардед. PUBG ID-и худро нависед:", chat_id, call.message.message_id)

    elif call.data.startswith("reply_"):
        user_id = call.data.split("_")[1]
        msg = bot.send_message(ADMIN_ID, "Ҷавобро нависед:")
        bot.register_next_step_handler(msg, lambda m: bot.send_message(user_id, f"📢 Админ: {m.text}"))

# --- ҚАБУЛИ ҲАМАИ ПАЁМҲО ---
@bot.message_handler(content_types=['text', 'photo'])
def handle_messages(message):
    chat_id = message.chat.id
    # Агар алоқа бо админ бошад
    if chat_id in user_data and user_data[chat_id].get("waiting_for_admin_message"):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("↩️ Ҷавоб додан", callback_data=f"reply_{chat_id}"))
        bot.send_message(ADMIN_ID, f"📩 Паём аз @{message.from_user.username or chat_id}:\n{message.text}", reply_markup=markup)
        bot.reply_to(message, "✅ Паём фиристода шуд.")
        user_data[chat_id]["waiting_for_admin_message"] = False
    
    # Агар интизори PUBG ID бошад
    elif chat_id in user_data and user_data[chat_id].get("waiting_for_id"):
        user_data[chat_id]["pubg_id"] = message.text
        user_data[chat_id]["waiting_for_id"] = False
        bot.reply_to(message, "ID қабул шуд! Акнун скриншоти пардохтро фиристед.")

bot.infinity_polling()
