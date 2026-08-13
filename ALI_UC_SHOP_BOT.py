import telebot
from telebot import types

# Айдии админии шумо
ADMIN_ID = 6871575684  

# Токени боти шумо
TOKEN = "8660164143:AAGL13-xIC2pln1JKKYiPQagb2dzn6N9hhQ"
bot = telebot.TeleBot(TOKEN)

user_data = {}
user_review_attempts = {}

# 1. Менюи асосӣ (/start)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    
    if chat_id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📦 Заказҳо", "🌟 Отзывҳо")
        markup.row("⚙️ Танзими ЮС")
        bot.send_message(chat_id, "Хуш омадед, Админ! Марҳамат, бахшро интихоб кунед:", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🛒 Харидани UC", "📦 Заказҳои ман")
        markup.row("🌟 Отзывҳо", "📞 Алоқа бо админ")
        
        text = (
            "Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥\n\n"
            "Дар ин ҷо шумо метавонед бо нархи дастрас ва бехатар UC (ЮС) харидорӣ кунед.\n"
            "Лутфан яке аз тугмаҳои зеринро интихоб кунед: 👇"
        )
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# Идоракунии тугмаҳои панели админ
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
        bot.send_message(ADMIN_ID, "⚙️ **Танзими пакетҳои ЮС:**\nМарҳамат, амалиёти лозимиро интихоб кунед:", reply_markup=markup, parse_mode="Markdown")
        
    elif text == "🏠 Ба менюи асосӣ":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📦 Заказҳо", "🌟 Отзывҳо")
        markup.row("⚙️ Танзими ЮС")
        bot.send_message(ADMIN_ID, "🏠 Менюи асосӣ:", reply_markup=markup)
        
    elif text == "➕ Илова кардани пакет":
        bot.send_message(ADMIN_ID, "➕ Лутфан номи пакети нав ва нархи онро нависед:")
    elif text == "✏️ Иваз кардани нарх":
        bot.send_message(ADMIN_ID, "✏️ Номи пакет ва нархи навро нависед:")
    elif text == "🗑️ Ҳазф кардани пакет":
        bot.send_message(ADMIN_ID, "🗑️ Номи пакетеро, ки мехоҳед ҳазф кунед, нависед:")
        
    elif text in ["📋 Ҳамаи заказҳо", "📦 Заказҳои нав", "✅ Заказҳои Иҷрошуда", "❌ Заказҳои Иҷронашуда"]:
        bot.send_message(ADMIN_ID, f"Тартиби кор бо: {text}")
        
    elif text in ["📋 Ҳамаи отзывҳо", "🆕 Отзывҳои нав", "✅ Отзывҳои қабулшуда", "❌ Отзывҳои радшуда"]:
        bot.send_message(ADMIN_ID, f"Тартиби кор бо: {text}")

# 2. Тугмаҳои корбар дар чат
@bot.message_handler(func=lambda message: message.text == "🛒 Харидани UC")
def user_buy_uc(message):
    chat_id = message.chat.id
    user_data[chat_id] = {"package": "60 юс", "price": "10 сомонӣ", "waiting_for_id": True}
    
    text = (
        "Шумо пакети **60 юс**-ро бо нархи **10 сомонӣ** интихоб кардед. ✅\n\n"
        "⚠️ **Лутфан, PUBG ID-и худро бодиққат ва бехато равон кунед!**\n\n"
        "**Диққат:** Дар сурати иштибоҳ ворид кардани ID, масъулият бар дӯши худи шумост ва маблағ баргардонида **намешавад**. ❌\n\n"
        "Лутфан, ID-и худро ҳозир навишта ирсол кунед: 👇"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📦 Заказҳои ман")
def user_my_orders(message):
    bot.send_message(message.chat.id, "📦 Дар ин ҷо таърихи заказҳои шумо нишон дода мешавад.")

@bot.message_handler(func=lambda message: message.text == "🌟 Отзывҳо")
def user_view_reviews(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💬 Гузаштан ба канали отзывҳо", url="https://t.me/otziv_ALI_US_SHOPP"))
    bot.send_message(message.chat.id, "🌟 **Канали отзывҳои мизоҷони мо:**\nМарҳамат, бо зер кардани тугмаи зерин ба канал гузаред ва фикру мулоҳизаҳоро тамошо кунед: 👇", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📞 Алоқа бо админ")
def user_contact_admin(message):
    bot.send_message(message.chat.id, "📞 Барои тамос бо администратор ба ин профил нависед: @Admin_Username")

# 3. Қабули PUBG ID ва реквизитҳо
@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_id"))
def receive_pubg_id(message):
    chat_id = message.chat.id
    pubg_id = message.text.strip()
    
    user_data[chat_id]["pubg_id"] = pubg_id
    user_data[chat_id].pop("waiting_for_id")
    user_data[chat_id]["waiting_for_screenshot"] = True
    
    pkg = user_data[chat_id]["package"]
    price = user_data[chat_id]["price"]
    
    text = (
        f"PUBG ID-и шумо: `{pubg_id}` ✅\n\n"
        f"📦 **Пакет:** {pkg}\n"
        f"💰 **Маблағ:** {price}\n\n"
        f"РЕКВИЗИТИ КАРТЫ 🎫 👇\n\n"
        f"👉 Бонки Эсхата  +992 `555050093`\n"
        f"Ба номи Орифчон Г. М.\n\n"
        f"👉 ДУШАНБЕ СИТИ  +992 `555050093`\n"
        f"Ба номи Орифчон Г. М.\n\n"
        f"👉 АЛИФ БАНК  +992 `555050093` \n"
        f"Ба номи Орифчон Г. М.\n\n"
        f"**Хатман чеки лозимаро (скриншот) ба ин чат фиристед!** 📸👇"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")

# 4. Қабули скриншот ва равон кардан ба админ
@bot.message_handler(content_types=['photo'], func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_screenshot"))
def receive_screenshot(message):
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id
    
    pkg = user_data[chat_id]["package"]
    price = user_data[chat_id]["price"]
    pubg_id = user_data[chat_id]["pubg_id"]
    
    user_data[chat_id].pop("waiting_for_screenshot")
    bot.reply_to(message, "Чеки шумо қабул шуд ва ба администратор фиристода шуд! ⏳\nЗакази шумо дар навбат аст. Ташаккур!")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🟢 Тасдиқ кардан", callback_data=f"approve_{chat_id}"),
        types.InlineKeyboardButton("🔴 Рад кардан", callback_data=f"reject_{chat_id}")
    )
    
    admin_text = (
        f"🔔 **Закази нав ворид шуд!**\n"
        f"👤 Корбар: @{message.from_user.username or message.from_user.first_name}\n"
        f"🆔 PUBG ID: `{pubg_id}`\n"
        f"📦 Пакет: {pkg}\n"
        f"💰 Маблағ: {price}"
    )
    bot.send_photo(ADMIN_ID, file_id, caption=admin_text, reply_markup=markup, parse_mode="Markdown")

# 5. Қарори админ оид ба заказ
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_order_handler(call):
    action, chat_id = call.data.split("_")
    chat_id = int(chat_id)
    
    if action == "approve":
        bot.answer_callback_query(call.id, "Заказ тасдиқ шуд!")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n✅ **СТАТУС: Тасдиқ шуд**", parse_mode="Markdown")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Гузоштани отзыв", callback_data="leave_review"))
        markup.add(types.InlineKeyboardButton("🏠 Ба менюи асосӣ", callback_data="user_main_menu"))
        
        bot.send_message(chat_id, "60 юс ✅\n\nЗакази шумо бо муваффақият иҷро шуд! 🎮✨\n\nЛутфан, барои мо отзыв гузоред:", reply_markup=markup)
        
    elif action == "reject":
        bot.answer_callback_query(call.id, "Заказ рад карда шуд.")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n❌ **СТАТУС: Рад шуд**", parse_mode="Markdown")
        bot.send_message(chat_id, "Мутаассифона, закази шумо аз ҷониби админ рад карда шуд. ❌")

# 6. Отзывҳо ва маҳдудияти 2 маротиба
@bot.callback_query_handler(func=lambda call: call.data == "leave_review")
def review_start_callback(call):
    chat_id = call.message.chat.id
    attempts = user_review_attempts.get(chat_id, 0)
    
    if attempts >= 2:
        bot.answer_callback_query(call.id, "Шумо лимити фиристодани отзывҳоро тамом кардед!", show_alert=True)
        return
        
    user_review_attempts[chat_id] = attempts + 1
    user_data[chat_id] = {"waiting_for_review": True}
    bot.send_message(chat_id, "Лутфан, фикру мулоҳиза ё отзыви худро нависед: 👇")

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_review"))
def receive_review_text(message):
    chat_id = message.chat.id
    review_text = message.text
    user_data[chat_id].pop("waiting_for_review")
    
    bot.reply_to(message, "Отвизи шумо ба админ фиристода шуд. Ташаккур! ⏳")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🟢 Тасдиқ ва нашр", callback_data=f"revapp_{chat_id}"),
        types.InlineKeyboardButton("🔴 Рад кардан", callback_data=f"revrej_{chat_id}")
    )
    
    admin_msg = (
        f"📩 **Отзыви нав аз корбар:**\n"
        f"👤 Корбар: @{message.from_user.username or message.from_user.first_name}\n"
        f"📝 Матн: {review_text}"
    )
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup, parse_mode="Markdown")
    user_data[chat_id]["last_review"] = review_text

@bot.callback_query_handler(func=lambda call: call.data.startswith("revapp_") or call.data.startswith("revrej_"))
def admin_review_handler(call):
    action, chat_id = call.data.split("_")
    chat_id = int(chat_id)
    
    if action == "revapp":
        bot.answer_callback_query(call.id, "Отзыв тасдиқ шуд!")
        bot.edit_message_text(call.message.text + "\n\n✅ **[ТАСДИҚ КАРДА ШУД]**", call.message.chat.id, call.message.message_id)
        bot.send_message(chat_id, "Ташаккур! Отвизи шумо аз ҷониби админ тасдиқ ва нашр шуд! 😊")
        
    elif action == "revrej":
        bot.answer_callback_query(call.id, "Отзыв рад шуд.")
        bot.edit_message_text(call.message.text + "\n\n❌ **[РАД КАРДА ШУД]**", call.message.chat.id, call.message.message_id)
        
        attempts = user_review_attempts.get(chat_id, 0)
        if attempts < 2:
            bot.send_message(chat_id, f"Отвизи шумо рад шуд. ❌ Шумо метавонед боз **{2 - attempts} маротиба** отзыви худро фиристед.")
        else:
            bot.send_message(chat_id, "Мутаассифона, лимити отзыв гузоштани шумо тамом шуд. 🚫")

@bot.callback_query_handler(func=lambda call: call.data == "user_main_menu")
def user_back_to_menu(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🏠 Шумо ба менюи асосӣ баргаштед. Барои харид дубора /start -ро пахш кунед.")

bot.infinity_polling()
