import telebot
from telebot import types

# Айдии админии шумо
ADMIN_ID = 6871575684  

# Токени боти шумо
TOKEN = "8660164143:AAGL13-xIC2pln1JKKYiPQagb2dzn6N9hhQ"
bot = telebot.TeleBot(TOKEN)

user_data = {}
user_review_attempts = {}

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
        msg = bot.send_message(ADMIN_ID, "➕ Лутфан миқдори ЮС ва нархи онро бо фосила нависед (Масол: `500 75 сомонӣ`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_add_package)
        
    elif text == "✏️ Иваз кардани нарх":
        msg = bot.send_message(ADMIN_ID, "✏️ Миқдори ЮС ва нархи навро нависед (Масол: `60 12 сомонӣ`):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, admin_edit_package)
        
    elif text == "🗑️ Ҳазф кардани пакет":
        msg = bot.send_message(ADMIN_ID, "🗑️ Миқдори ЮСеро, ки мехоҳед ҳазф кунед, нависед (Масол: `60`):")
        bot.register_next_step_handler(msg, admin_delete_package)
        
    elif text in ["📋 Ҳамаи заказҳо", "📦 Заказҳои нав", "✅ Заказҳои Иҷрошуда", "❌ Заказҳои Иҷронашуда"]:
        bot.send_message(ADMIN_ID, f"Тартиби кор бо: {text}")
        
    elif text in ["📋 Ҳамаи отзывҳо", "🆕 Отзывҳои нав", "✅ Отзывҳои қабулшуда", "❌ Отзывҳои радшуда"]:
        bot.send_message(ADMIN_ID, f"Тартиби кор бо: {text}")

# Функсияҳои идоракунии пакетҳо аз ҷониби админ
def admin_add_package(message):
    try:
        parts = message.text.split(maxsplit=1)
        uc_key = parts[0]
        price_val = parts[1]
        UC_PACKAGES[uc_key] = price_val
        bot.send_message(ADMIN_ID, f"✅ Пакет бомуваффақият илова шуд!\n💎 {uc_key} UC — {price_val}")
    except Exception:
        bot.send_message(ADMIN_ID, "❌ Хатогӣ дар ворид кардани маълумот. Лутфан дубора кӯшиш кунед.")

def admin_edit_package(message):
    try:
        parts = message.text.split(maxsplit=1)
        uc_key = parts[0]
        price_val = parts[1]
        if uc_key in UC_PACKAGES:
            UC_PACKAGES[uc_key] = price_val
            bot.send_message(ADMIN_ID, f"✅ Нархи пакети {uc_key} UC ба {price_val} иваз карда шуд!")
        else:
            bot.send_message(ADMIN_ID, f"❌ Пакет бо миқдори {uc_key} ёфт нашуд.")
    except Exception:
        bot.send_message(ADMIN_ID, "❌ Хатогӣ дар формат. Дубора кӯшиш кунед.")

def admin_delete_package(message):
    uc_key = message.text.strip()
    if uc_key in UC_PACKAGES:
        del UC_PACKAGES[uc_key]
        bot.send_message(ADMIN_ID, f"🗑️ Пакет бо миқдори {uc_key} UC тоза карда шуд!")
    else:
        bot.send_message(ADMIN_ID, f"❌ Чунин пакет дар рӯйхат нест.")

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
        # Намоиши маълумоти охирини закази корбар агар мавҷуд бошад
        user_history = user_data.get(chat_id, {}).get("last_order_info", "Шумо то ҳол заказе надоред. ❌")
        bot.edit_message_text(f"📦 **Заказҳои охирини шумо:**\n\n{user_history}", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        
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
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        contact_text = (
            "📞 **Алоқа бо администратор:**\n\n"
            "Дар ҳамин ҷо паём, савол ё акси худро нависед. Админ дар вақти кӯтоҳтарин ба шумо ҷавоб медиҳад! 👇"
        )
        bot.edit_message_text(contact_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]["waiting_for_admin_message"] = True
        
    elif call.data == "user_main_menu":
        bot.answer_callback_query(call.id)
        if chat_id in user_data and "waiting_for_admin_message" in user_data[chat_id]:
            user_data[chat_id].pop("waiting_for_admin_message")
            
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

# Қабули паёми корбар барои админ
@bot.message_handler(content_types=['text', 'photo', 'voice', 'video', 'document'], func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_admin_message"))
def forward_message_to_admin(message):
    chat_id = message.chat.id
    user_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ Ҷавоб додан", callback_data=f"reply_{chat_id}"))
    
    forward_text = f"📩 **Паёми нав ба админ!**\n👤 Корбар: {user_name} (ID: `{chat_id}`)"
    
    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{forward_text}\n\n📝 Матн: {message.text}", reply_markup=markup, parse_mode="Markdown")
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        caption = message.caption if message.caption else ""
        bot.send_photo(ADMIN_ID, file_id, caption=f"{forward_text}\n\n📸 Скриншот/Расм: {caption}", reply_markup=markup, parse_mode="Markdown")
    elif message.content_type == 'voice':
        file_id = message.voice.file_id
        bot.send_voice(ADMIN_ID, file_id, caption=forward_text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.send_message(ADMIN_ID, f"👆 Паёми боло аз корбар: {user_name}", reply_markup=markup)
        
    bot.reply_to(message, "Паёми шумо қабул шуд ва ба админ фиристода шуд! ⏳ Лутфан мутобиқи ҷавоб интизор шавед.")
    user_data[chat_id].pop("waiting_for_admin_message")

# Ҷавоб додани админ ба корбар
@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_"))
def admin_reply_callback(call):
    user_id = call.data.split("_")[1]
    msg = bot.send_message(ADMIN_ID, "Лутфан, ҷавоби худро ба ин корбар нависед:")
    bot.register_next_step_handler(msg, send_reply_to_user, user_id)

def send_reply_to_user(message, user_id):
    try:
        bot.send_message(user_id, f"📢 **Ҷавоб аз Админ:**\n\n{message.text}")
        bot.send_message(ADMIN_ID, "Ҷавоб бо муваффақият ба корбар фиристода шуд! ✅")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Хатогӣ рух дод! Шояд корбар ботро блок карда бошад.\nХатогӣ: {e}")

# Интихоби пакети мушаххаси ЮС аз тарафи корбар
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_uc_"))
def select_uc_package(call):
    chat_id = call.message.chat.id
    uc_amount = call.data.split("_")[2]
    price = UC_PACKAGES.get(uc_amount)
    
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id].update({"package": f"{uc_amount} юс", "price": price, "waiting_for_id": True})
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

# 4. Қабули скриншот ва равон кардан ба админ
@bot.message_handler(content_types=['photo'], func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_screenshot"))
def receive_screenshot(message):
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id
    
    pkg = user_data[chat_id]["package"]
    price = user_data[chat_id]["price"]
    pubg_id = user_data[chat_id]["pubg_id"]
    
    user_data[chat_id].pop("waiting_for_screenshot")
    
    # Сабти таърихи заказ барои бахши "Заказҳои ман"
    user_data[chat_id]["last_order_info"] = f"📦 Пакет: {pkg}\n🆔 ID: `{pubg_id}`\n💰 Маблағ: {price}\n⏳ Статус: Дар навбат..."
    
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

# 5. Қарори админ оид ба заказ
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_order_handler(call):
    action, chat_id = call.data.split("_")
    chat_id = int(chat_id)
    
    if action == "approve":
        bot.answer_callback_query(call.id, "Заказ тасдиқ шуд!")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n✅ **СТАТУС: Тасдиқ шуд**", parse_mode="Markdown")
        
        if chat_id in user_data:
            user_data[chat_id]["last_order_info"] = user_data[chat_id].get("last_order_info", "").replace("⏳ Статус: Дар навбат...", "✅ Статус: Иҷро шуд 🎉")
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Гузоштани отзыв", callback_data="leave_review"))
        markup.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
        
        bot.send_message(chat_id, "Закази шумо бо муваффақият иҷро шуд! 🎮✨\n\nЛутфан, барои мо отзыв гузоред:", reply_markup=markup)
        
    elif action == "reject":
        bot.answer_callback_query(call.id, "Заказ рад карда шуд.")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n❌ **СТАТУС: Рад шуд**", parse_mode="Markdown")
        
        if chat_id in user_data:
            user_data[chat_id]["last_order_info"] = user_data[chat_id].get("last_order_info", "").replace("⏳ Статус: Дар навбат...", "❌ Статус: Рад шуд")
            
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
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]["waiting_for_review"] = True
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
        types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
    )
    bot.edit_message_text("Лутфан, фикру мулоҳиза ё отзыви худро нависед: 👇", chat_id, call.message.message_id, reply_markup=markup)

@bot.message_handler(func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_review"))
def receive_review_text(message):
    chat_id = message.chat.id
    review_text = message.text
    user_data[chat_id].pop("waiting_for_review")
    
    markup_user = types.InlineKeyboardMarkup()
    markup_user.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
    bot.reply_to(message, "Отвизи шумо ба админ фиристода шуд. Ташаккур! ⏳", reply_markup=markup_user)
    
    markup_admin = types.InlineKeyboardMarkup()
    markup_admin.add(
        types.InlineKeyboardButton("🟢 Тасдиқ ва нашр", callback_data=f"revapp_{chat_id}"),
        types.InlineKeyboardButton("🔴 Рад кардан", callback_data=f"revrej_{chat_id}")
    )
    
    admin_msg = (
        f"📩 **Отзыви нав аз корбар:**\n"
        f"👤 Корбар: @{message.from_user.username or message.from_user.first_name}\n"
        f"📝 Матн: {review_text}"
    )
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=markup_admin, parse_mode="Markdown")
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

bot.infinity_polling()
