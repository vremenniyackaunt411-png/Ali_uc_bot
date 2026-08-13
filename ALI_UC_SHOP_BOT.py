import telebot
from telebot import types

ADMIN_ID = 6871575684  
TOKEN = "8660164143:AAGL13-xIC2pln1JKKYiPQagb2dzn6N9hhQ"
bot = telebot.TeleBot(TOKEN)

user_data = {}
user_review_attempts = {}

UC_PACKAGES = {
    "60": "10 сомонӣ",
    "120": "20 сомонӣ",
    "180": "30 сомонӣ",
    "325": "48 сомонӣ",
    "385": "58 сомонӣ",
    "660": "92 сомонӣ",
    "720": "102 сомонӣ",
    "1320": "184 сомонӣ",
    "1800": "240 сомонӣ",
    "3850": "450 сомонӣ",
    "8100": "870 сомонӣ"
}

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
            types.InlineKeyboardButton("📦 Заказҳои ман", callback_data="my_orders")
        )
        markup.add(
            types.InlineKeyboardButton("🌟 Отзывҳо", callback_data="view_reviews"),
            types.InlineKeyboardButton("📞 Алоқа бо админ", callback_data="contact_admin")
        )
        bot.send_message(chat_id, "Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID)
def admin_panels(message):
    text = message.text
    if text == "📦 Заказҳо":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📋 Ҳамаи заказҳо", "📦 Заказҳои нав")
        markup.row("✅ Заказҳои Иҷрошуда", "❌ Заказҳои Иҷронашуда")
        markup.row("🏠 Ба менюи асосӣ")
        bot.send_message(ADMIN_ID, "📦 Бахши заказҳо:", reply_markup=markup)
    elif text == "🌟 Отзывҳо":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📋 Ҳамаи отзывҳо", "🆕 Отзывҳои нав")
        markup.row("✅ Отзывҳои қабулшуда", "❌ Отзывҳои радшуда")
        markup.row("🏠 Ба менюи асосӣ")
        bot.send_message(ADMIN_ID, "🌟 Бахши отзывҳо:", reply_markup=markup)
    elif text == "⚙️ Танзими ЮС":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("➕ Илова кардани пакет", "✏️ Иваз кардани нарх")
        markup.row("🗑️ Ҳазф кардани пакет", "🏠 Ба менюи асосӣ")
        bot.send_message(ADMIN_ID, "⚙️ Танзими пакетҳои ЮС:", reply_markup=markup)
    elif text == "🏠 Ба менюи асосӣ":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📦 Заказҳо", "🌟 Отзывҳо")
        markup.row("⚙️ Танзими ЮС")
        bot.send_message(ADMIN_ID, "🏠 Менюи асосӣ:", reply_markup=markup)
    elif text == "➕ Илова кардани пакет":
        msg = bot.send_message(ADMIN_ID, "Миқдори ЮС ва нархро нависед (Масол: `500 75 сомонӣ`)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_add_package)
    elif text == "✏️ Иваз кардани нарх":
        msg = bot.send_message(ADMIN_ID, "Миқдори ЮС ва нархи навро нависед (Масол: `60 12 сомонӣ`)", parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_edit_package)
    elif text == "🗑️ Ҳазф кардани пакет":
        msg = bot.send_message(ADMIN_ID, "Миқдори ЮСеро, ки мехоҳед ҳазф кунед, нависед (Масол: `60`):")
        bot.register_next_step_handler(msg, admin_delete_package)

def admin_add_package(message):
    try:
        parts = message.text.split(maxsplit=1)
        UC_PACKAGES[parts[0]] = parts[1]
        bot.send_message(ADMIN_ID, f"✅ Пакет илова шуд: {parts[0]} UC - {parts[1]}")
    except: bot.send_message(ADMIN_ID, "❌ Хатогӣ.")

def admin_edit_package(message):
    try:
        parts = message.text.split(maxsplit=1)
        if parts[0] in UC_PACKAGES:
            UC_PACKAGES[parts[0]] = parts[1]
            bot.send_message(ADMIN_ID, "✅ Нарх иваз шуд!")
        else: bot.send_message(ADMIN_ID, "❌ Пакет ёфт нашуд.")
    except: bot.send_message(ADMIN_ID, "❌ Хатогӣ.")

def admin_delete_package(message):
    uc_key = message.text.strip()
    if uc_key in UC_PACKAGES:
        del UC_PACKAGES[uc_key]
        bot.send_message(ADMIN_ID, "🗑️ Тоза карда шуд!")
    else: bot.send_message(ADMIN_ID, "❌ Ёфт нашуд.")

@bot.callback_query_handler(func=lambda call: call.data in ["buy_uc_menu", "my_orders", "view_reviews", "contact_admin", "user_main_menu"])
def user_inline_menu(call):
    chat_id = call.message.chat.id
    if call.data == "buy_uc_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for uc, price in UC_PACKAGES.items():
            markup.add(types.InlineKeyboardButton(f"💎 {uc} UC — {price}", callback_data=f"select_uc_{uc}"))
        markup.row(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
        bot.edit_message_text("🛒 **Марҳамат, пакети дилхоҳи ЮС-ро интихоб кунед:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    elif call.data == "my_orders":
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
        user_history = user_data.get(chat_id, {}).get("last_order_info", "Шумо то ҳол заказе надоред. ❌")
        bot.edit_message_text(f"📦 **Заказҳои охирини шумо:**\n\n{user_history}", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    elif call.data == "view_reviews":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("💬 Гузаштан ба канали отзывҳо", url="https://t.me/otziv_ALI_US_SHOPP"))
        markup.row(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
        bot.edit_message_text("🌟 **Канали отзывҳои мизоҷони мо:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    elif call.data == "contact_admin":
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
        bot.edit_message_text("📞 **Алоқа бо администратор:**\nПаём ё акси худро нависед 👇", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        if chat_id not in user_data: user_data[chat_id] = {}
        user_data[chat_id]["waiting_for_admin_message"] = True
    elif call.data == "user_main_menu":
        if chat_id in user_data and "waiting_for_admin_message" in user_data[chat_id]: user_data[chat_id].pop("waiting_for_admin_message")
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🛒 Харидани UC", callback_data="buy_uc_menu"),
            types.InlineKeyboardButton("📦 Заказҳои ман", callback_data="my_orders"),
            types.InlineKeyboardButton("🌟 Отзывҳо", callback_data="view_reviews"),
            types.InlineKeyboardButton("📞 Алоқа бо админ", callback_data="contact_admin")
        )
        bot.edit_message_text("Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['text', 'photo', 'voice', 'video', 'document'], func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_admin_message"))
def forward_message_to_admin(message):
    chat_id = message.chat.id
    user_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ Ҷавоб додан", callback_data=f"reply_{chat_id}"))
    
    if message.content_type == 'text': bot.send_message(ADMIN_ID, f"📩 Паёми нав аз: {user_name}\nМатн: {message.text}", reply_markup=markup)
    elif message.content_type == 'photo': bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"📩 Паём аз: {user_name}", reply_markup=markup)
    else: bot.forward_message(ADMIN_ID, chat_id, message.message_id)
    
    markup_user = types.InlineKeyboardMarkup()
    markup_user.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
    bot.reply_to(message, "Паёми шумо ба админ фиристода шуд! ⏳", reply_markup=markup_user)
    user_data[chat_id].pop("waiting_for_admin_message")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def admin_reply_callback(call):
    user_id = call.data.split("_")[1]
    msg = bot.send_message(ADMIN_ID, "Ҷавоби худро ба ин корбар нависед:")
    bot.register_next_step_handler(msg, send_reply_to_user, user_id)

def send_reply_to_user(message, user_id):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("↩️ Ҷавоб додан", callback_data="contact_admin"))
        bot.send_message(user_id, f"📢 **Ҷавоб аз Админ:**\n\n{message.text}", reply_markup=markup)
        bot.send_message(ADMIN_ID, "Ҷавоб бо муваффақият фиристода шуд! ✅")
    except Exception as e: bot.send_message(ADMIN_ID, f"Хатогӣ: {e}")

# (Қисмҳои дигари код - аз select_uc_package то охир бетағйир мемонанд)
# ... Идомаи коди шумо ...

bot.infinity_polling()
