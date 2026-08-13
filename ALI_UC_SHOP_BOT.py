import telebot
from telebot import types

# Айдии админии шумо
ADMIN_ID = 6871575684  

# Токени боти шумо
TOKEN = "8660164143:AAGL13-xIC2pln1JKKYiPQagb2dzn6N9hhQ"
bot = telebot.TeleBot(TOKEN)

user_data = {}
user_review_attempts = {}

# Пойгоҳи маълумот барои паёмҳои корбарон ба админ
admin_messages = {}  # {msg_id: {"user_id": ..., "username": ..., "text": ..., "status": "беҷавоб", "completed_orders": ..., "approved_reviews": ...}}
msg_counter = 1

# Рӯйхати пакетҳо ва нархҳо
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

# 1. Менюи асосӣ (/start)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    
    if chat_id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📦 Заказҳо", "🌟 Отзывҳо")
        markup.row("📩 Паёмҳои корбарон")
        markup.row("⚙️ Танзими ЮС")
        bot.send_message(chat_id, "Хуш омадед, Админ! Марҳамат, бахшро интихоб кунед:", reply_markup=markup)
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
        
        text = (
            "Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥\n\n"
            "Дар ин ҷо шумо метавонед бо нархи дастрас ва бехатар UC (ЮС) харидорӣ кунед.\n"
            "Лутфан яке аз тугмаҳои зеринро интихоб кунед: 👇"
        )
        
        remove_markup = types.ReplyKeyboardRemove()
        bot.send_message(chat_id, "⌛", reply_markup=remove_markup)
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# Идоракунии тугмаҳои панели админ
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and not message.text.startswith("/"))
def admin_panels(message):
    text = message.text
    chat_id = message.chat.id
    
    if chat_id in user_data and user_data[chat_id].get("replying_to_msg"):
        target_msg_id = user_data[chat_id]["replying_to_msg"]
        user_data[chat_id].pop("replying_to_msg")
        
        target_data = admin_messages.get(target_msg_id)
        if target_data:
            target_user_id = target_data["user_id"]
            target_data["status"] = "боҷавоб"
            
            # Ба корбар ҷавоби админ фиристода мешавад
            bot.send_message(target_user_id, f"💬 **Ҷавоби администратор:**\n\n{text}")
            bot.send_message(ADMIN_ID, "✅ Ҷавоб ба корбар бо муваффақият фиристода шуд!")
        return

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
        
    elif text == "📩 Паёмҳои корбарон":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📥 Паёмҳои беҷавоб", "📤 Паёмҳои боҷавоб")
        markup.row("🏠 Ба менюи асосӣ")
        bot.send_message(ADMIN_ID, "📩 Бахши паёмҳои корбарон, категорияро интихоб кунед:", reply_markup=markup)
        
    elif text == "📥 Паёмҳои беҷавоб":
        markup = types.InlineKeyboardMarkup(row_width=1)
        has_msgs = False
        for m_id, data in admin_messages.items():
            if data["status"] == "беҷавоб":
                has_msgs = False if has_msgs else True # just to track
                markup.add(types.InlineKeyboardButton(f"Паём №{m_id} (@{data['username']})", callback_data=f"adm_msg_{m_id}"))
        
        if not markup.keyboard:
            bot.send_message(ADMIN_ID, "📭 Ҳоло паёмҳои беҷавоб нестанд.")
        else:
            bot.send_message(ADMIN_ID, "📥 **Паёмҳои беҷавоб:**", reply_markup=markup, parse_mode="Markdown")
            
    elif text == "📤 Паёмҳои боҷавоб":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for m_id, data in admin_messages.items():
            if data["status"] == "боҷавоб":
                markup.add(types.InlineKeyboardButton(f"Паём №{m_id} (@{data['username']}) ✅", callback_data=f"adm_msg_{m_id}"))
        
        if not markup.keyboard:
            bot.send_message(ADMIN_ID, "📭 Ҳоло паёмҳои боҷавоб нестанд.")
        else:
            bot.send_message(ADMIN_ID, "📤 **Паёмҳои боҷавобшуда:**", reply_markup=markup, parse_mode="Markdown")
        
    elif text == "⚙️ Танзими ЮС":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("➕ Илова кардани пакет", "✏️ Иваз кардани нарх")
        markup.row("🗑️ Ҳазф кардани пакет", "🏠 Ба менюи асосӣ")
        bot.send_message(ADMIN_ID, "⚙️ **Танзими пакетҳои ЮС:**\nМарҳамат, амалиёти лозимиро интихоб кунед:", reply_markup=markup, parse_mode="Markdown")
        
    elif text == "🏠 Ба менюи асосӣ":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("📦 Заказҳо", "🌟 Отзывҳо")
        markup.row("📩 Паёмҳои корбарон")
        markup.row("⚙️ Танзими ЮС")
        bot.send_message(ADMIN_ID, "🏠 Менюи асосӣ:", reply_markup=markup)
        
    elif text == "➕ Илова кардани пакет":
        bot.send_message(ADMIN_ID, "➕ Лутфан номи пакети нав ва нархи онро нависед:")
    elif text == "✏️ Иваз кардани нарх":
        bot.send_message(ADMIN_ID, "✏️ Номи пакет ва нархи навро нависед:")
    elif text == "🗑️ Ҳазф кардани пакет":
        bot.send_message(ADMIN_ID, "🗑️ Номи пакетеро, ки мехоҳед ҳазф кунед, нависед:")

# 2. Тугмаҳои Inline-и корбар ва идоракунии гузаришҳо
@bot.callback_query_handler(func=lambda call: call.data in ["buy_uc_menu", "my_orders", "view_reviews", "contact_admin", "user_main_menu"])
def user_inline_menu(call):
    chat_id = call.message.chat.id
    
    if call.data == "buy_uc_menu":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=2)
        for uc, price in UC_PACKAGES.items():
            markup.add(types.InlineKeyboardButton(f"💎 {uc} UC — {price}", callback_data=f"select_uc_{uc}"))
        
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        bot.edit_message_text("🛒 **Марҳамат, пакети дилхоҳи ЮС-ро интихоб кунед:** 👇", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        
    elif call.data == "my_orders":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        bot.edit_message_text("📦 Дар ин ҷо таърихи заказҳои шумо нишон дода мешавад.", chat_id, call.message.message_id, reply_markup=markup)
        
    elif call.data == "view_reviews":
        bot.answer_callback_query(call.id)
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("💬 Гузаштан ба канали отзывҳо", url="https://t.me/otziv_ALI_US_SHOPP"))
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        bot.edit_message_text("🌟 **Канали отзывҳои мизоҷони мо:**\nМарҳамат, бо зер кардани тугмаи зерин ба канал гузаред: 👇", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        
    elif call.data == "contact_admin":
        bot.answer_callback_query(call.id)
        user_data[chat_id] = {"waiting_for_admin_message": True}
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        contact_text = (
            "📞 **Алоқа бо администратор:**\n\n"
            "Админ омода аст ба саволҳои шумо ҷавоб диҳад! 👨‍💻\n\n"
            "Лутфан савол ё паёми худро ба ин чат нависед ва ирсол кунед: 👇"
        )
        bot.edit_message_text(contact_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        
    elif call.data == "user_main_menu":
        bot.answer_callback_query(call.id)
        if chat_id in user_data:
            user_data[chat_id].pop("waiting_for_admin_message", None)
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🛒 Харидани UC", callback_data="buy_uc_menu"),
            types.InlineKeyboardButton("📦 Заказҳои ман", callback_data="my_orders")
        )
        markup.add(
            types.InlineKeyboardButton("🌟 Отзывҳо", callback_data="view_reviews"),
            types.InlineKeyboardButton("📞 Алоқа бо админ", callback_data="contact_admin")
        )
        bot.edit_message_text("Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥\n\nЛутфан яке аз тугмаҳои зеринро интихоб кунед: 👇", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# Қабули паёми корбар ба админ ва фиристодан бо рақам
@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_admin_message"))
def receive_user_admin_message(message):
    global msg_counter
    chat_id = message.chat.id
    msg_text = message.text
    user_data[chat_id].pop("waiting_for_admin_message")
    
    # Ҳисоб кардани заказҳои иҷрошуда ва отзывҳои қабулшудаи корбар
    completed_orders_count = user_data.get(chat_id, {}).get("completed_orders_count", 0)
    approved_reviews_count = user_data.get(chat_id, {}).get("approved_reviews_count", 0)
    
    current_msg_id = msg_counter
    msg_counter += 1
    
    admin_messages[current_msg_id] = {
        "user_id": chat_id,
        "username": message.from_user.username or message.from_user.first_name,
        "text": msg_text,
        "status": "беҷавоб",
        "completed_orders": completed_orders_count,
        "approved_reviews": approved_reviews_count
    }
    
    markup_user = types.InlineKeyboardMarkup()
    markup_user.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
    bot.reply_to(message, "Паёми шумо ба админ фиристода шуд! Админ ҳатман ба шумо ҷавоб медиҳад. ⏳", reply_markup=markup_user)
    
    # Ба админ фиристодани паём бо рақам ба монанди заказҳо
    markup_admin = types.InlineKeyboardMarkup()
    markup_admin.add(types.InlineKeyboardButton(f"💬 Ҷавоб додан ба Паём №{current_msg_id}", callback_data=f"adm_msg_{current_msg_id}"))
    
    admin_notification = (
        f"📩 **Паёми нав ба админ (№{current_msg_id})!**\n\n"
        f"👤 Корбар: @{message.from_user.username or message.from_user.first_name}\n"
        f"💬 Матн: {msg_text}"
    )
    bot.send_message(ADMIN_ID, admin_notification, reply_markup=markup_admin, parse_mode="Markdown")

# Коркарди пахши паёмҳои алоҳидаи корбарон аз тарафи админ
@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_msg_"))
def admin_view_specific_message(call):
    if call.message.chat.id != ADMIN_ID:
        return
    
    m_id = int(call.data.split("_")[2])
    data = admin_messages.get(m_id)
    
    if not data:
        bot.answer_callback_query(call.id, "Паём ёфт нашуд ё нест карда шудааст!", show_alert=True)
        return
        
    bot.answer_callback_query(call.id)
    
    text = (
        f"📄 **Маълумот оид ба паём №{m_id}:**\n\n"
        f"👤 **Ном / Никнейм:** @{data['username']}\n"
        f"📦 **Заказҳои иҷрошудаи у:** {data['completed_orders']}\n"
        f"🌟 **Отзывҳои қабулшудаи у:** {data['approved_reviews']}\n\n"
        f"💬 **Матни паём:**\n{data['text']}\n\n"
        f"📌 **Статус:** {data['status']}"
    )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✍️ Ҷавоб додан", callback_data=f"adm_reply_{m_id}"))
    markup.row(
        types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="admin_back_to_msgs"),
        types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
    )
    
    bot.edit_message_text(text, ADMIN_ID, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_reply_"))
def admin_start_reply(call):
    if call.message.chat.id != ADMIN_ID:
        return
    m_id = int(call.data.split("_")[2])
    user_data[ADMIN_ID] = {"replying_to_msg": m_id}
    
    bot.answer_callback_query(call.id)
    bot.send_message(ADMIN_ID, f"✍️ Лутфан матни ҷавобро барои Паём №{m_id} нависед ва ирсол кунед:")

@bot.callback_query_handler(func=lambda call: call.data == "admin_back_to_msgs")
def admin_back_msgs(call):
    if call.message.chat.id != ADMIN_ID:
        return
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📥 Паёмҳои беҷавоб", "📤 Паёмҳои боҷавоб")
    markup.row("🏠 Ба менюи асосӣ")
    bot.send_message(ADMIN_ID, "📩 Бахши паёмҳои корбарон:", reply_markup=markup)

# Интихоби пакети мушаххаси ЮС аз тарафи корбар
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_uc_"))
def select_uc_package(call):
    chat_id = call.message.chat.id
    uc_amount = call.data.split("_")[2]
    price = UC_PACKAGES.get(uc_amount)
    
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]["package"] = f"{uc_amount} юс"
    user_data[chat_id]["price"] = price
    user_data[chat_id]["waiting_for_id"] = True
    bot.answer_callback_query(call.id)
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="buy_uc_menu"),
        types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
    )
    
    text = (
        f"Шумо пакети **{uc_amount} юс**-ро бо нархи **{price}** интихоб кардед. ✅\n\n"
        "⚠️ **Лутфан, PUBG ID-и худро бодиққат ва бехато равон кунед!**\n\n"
        "**Диққат:** Дар сурати иштибоҳ ворид кардани ID, масъулият бар дӯши худи шумост ва маблағ баргардонида **намешавад**. ❌\n\n"
        "Лутфан, ID-и худро ҳозир навишта ирсол кунед: 👇"
    )
    bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

# Қабули PUBG ID ва реквизитҳо
@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_id"))
def receive_pubg_id(message):
    chat_id = message.chat.id
    pubg_id = message.text.strip()
    
    user_data[chat_id]["pubg_id"] = pubg_id
    user_data[chat_id].pop("waiting_for_id")
    user_data[chat_id]["waiting_for_screenshot"] = True
    
    pkg = user_data[chat_id]["package"]
    price = user_data[chat_id]["price"]
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="buy_uc_menu"),
        types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
    )
    
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
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# Қабули скриншот ва равон кардан ба админ
@bot.message_handler(content_types=['photo'], func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_screenshot"))
def receive_screenshot(message):
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id
    
    pkg = user_data[chat_id]["package"]
    price = user_data[chat_id]["price"]
    pubg_id = user_data[chat_id]["pubg_id"]
    
    user_data[chat_id].pop("waiting_for_screenshot")
    
    markup_user = types.InlineKeyboardMarkup()
    markup_user.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
    bot.reply_to(message, "Чеки шумо қабул шуд ва ба администратор фиристода шуд! ⏳\nЗакази шумо дар навбат аст. Ташаккур!", reply_markup=markup_user)
    
    markup_admin = types.InlineKeyboardMarkup()
    markup_admin.add(
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
    bot.send_photo(ADMIN_ID, file_id, caption=admin_text, reply_markup=markup_admin, parse_mode="Markdown")

# Қарори админ оид ба заказ
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_order_handler(call):
    action, chat_id = call.data.split("_")
    chat_id = int(chat_id)
    
    if action == "approve":
        bot.answer_callback_query(call.id, "Заказ тасдиқ шуд!")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n✅ **СТАТУС: Тасдиқ шуд**", parse_mode="Markdown")
        
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]["completed_orders_count"] = user_data[chat_id].get("completed_orders_count", 0) + 1
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Гузоштани отзыв", callback_data="leave_review"))
        markup.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
        
        bot.send_message(chat_id, "Закази шумо бо муваффақият иҷро шуд! 🎮✨\n\nЛутфан, барои мо отзыв гузоред:", reply_markup=markup)
        
    elif action == "reject":
        bot.answer_callback_query(call.id, "Заказ рад карда шуд.")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n❌ **СТАТУС: Рад шуд**", parse_mode="Markdown")
        bot.send_message(chat_id, "Мутаассифона, закази шумо аз ҷониби админ рад карда шуд. ❌")

# Отзывҳо ва маҳдудияти 2 маротиба
@bot.callback_query_handler(func=lambda call: call.data == "leave_review")
def review_start_callback(call):
    chat_id = call.message.chat.id
    attempts = user_review_attempts.get(chat_id, 0)
    
    if attempts >= 2:
        bot.answer_callback_query(call.id, "Шумо лимити фиристодани отзывҳоро тамом кардед!", show_alert=True)
        return
        
    user_review
