import telebot
from telebot import types

TOKEN = "8660164143:AAGL13-xIC2pln1JKKYiPQagb2dzn6N9hhQ"
ADMIN_ID = 6871575684  # ID-и худро гузоред!

bot = telebot.TeleBot(TOKEN)
user_data = {}

# --- START ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📦 Заказҳо", "🌟 Отзывҳо")
        markup.row("⚙️ Танзими ЮС")
        bot.send_message(message.chat.id, "Хуш омадед, Админ!", reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🛒 Харидани UC", callback_data="buy_uc_menu"),
            types.InlineKeyboardButton("📦 Заказҳои ман", callback_data="my_orders"),
            types.InlineKeyboardButton("🌟 Отзывҳо", callback_data="view_reviews"),
            types.InlineKeyboardButton("📞 Алоқа бо админ", callback_data="contact_admin")
        )
        bot.send_message(message.chat.id, "Салом! Хуш омадед ба ALI UC SHOP 🎮", reply_markup=markup)

# --- МЕНЮИ АДМИН (Кнопкаҳо) ---
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.text in ["📦 Заказҳо", "🌟 Отзывҳо", "⚙️ Танзими ЮС"])
def admin_menu(message):
    bot.send_message(ADMIN_ID, f"Шумо ба бахши {message.text} даромадед.")

# --- CALLBACK (Тугмаҳои корбар) ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    if call.data == "contact_admin":
        user_data[chat_id] = {"waiting": True}
        bot.edit_message_text("📞 Паёми худро нависед, админ мебинад:", chat_id, call.message.message_id)
    
    elif call.data == "buy_uc_menu":
        bot.edit_message_text("🛒 Харидани UC интихоб шуд.", chat_id, call.message.message_id)

# --- ҚАБУЛИ ПАЁМҲО (Алоқа) ---
@bot.message_handler(content_types=['text', 'photo'])
def handle_all(message):
    chat_id = message.chat.id
    # Агар корбар паём нависад барои админ
    if chat_id in user_data and user_data[chat_id].get("waiting"):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("↩️ Ҷавоб додан", callback_data=f"reply_{chat_id}"))
        bot.send_message(ADMIN_ID, f"📩 Паём аз @{message.from_user.username or chat_id}:\n{message.text}", reply_markup=markup)
        bot.reply_to(message, "✅ Паём ба админ расид.")
        user_data[chat_id]["waiting"] = False

    # Ҷавоб додан аз ҷониби админ
    elif chat_id == ADMIN_ID and message.reply_to_message:
        target_id = message.reply_to_message.text.split("@")[-1].split(":")[0].strip()
        # Ин ҷо мантиқи ҷавоб додани админро мегузорем
        bot.send_message(target_id, f"📢 Ҷавоб аз Админ:\n{message.text}")
        bot.reply_to(message, "✅ Ҷавоб фиристода шуд.")

bot.infinity_polling()
