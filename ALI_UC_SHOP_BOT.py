# Намунаи коди идоракунии закази UC ва отзывҳо (Python / Telebot)
# Илтимос, тағйироти лозимиро (token ва admin_id) ба коди асосии худ мувофиқ кунед.

import telebot
from telebot import types

TOKEN = "BOT_TOKEN_IN_HERE"
ADMIN_ID = 123456789  # Айдии админ дар Telegram

bot = telebot.TeleBot(TOKEN)

# Базаи муваққатӣ барои нигоҳ доштани ҳолати корбарон (дар лоиҳаи калон ба БД мегузаред)
user_data = {}
user_review_attempts = {} # Барои ҳисоби кӯшишҳои отзыв (то 2 маротиба)

# 1. Қадами интихоби пакет (Масалан, пас аз пахши 60 UC)
def send_id_prompt(chat_id, package_name, price):
    user_data[chat_id] = {"package": package_name, "price": price}
    
    text = (
        f"Шумо пакети **{package_name}**-ро бо нархи **{price}** интихоб кардед. ✅\n\n"
        f"⚠️ **Лутфан, PUBG ID-и худро бодиққат ва бехато равон кунед!**\n\n"
        f"**Диққат:** Дар сурати иштибоҳ ворид кардани ID, масъулият бар дӯши худи шумост ва маблағ (пул) баргардонида **намешавад**. ❌\n\n"
        f"Лутфан, ID-и худро ҳозир навишта ирсол кунед: 👇"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")

# 2. Қабули PUBG ID ва фиристодани реквизитҳо
@bot.message_handler(func=lambda message: message.chat.id in user_data and "waiting_for_id" in user_data[message.chat.id])
def receive_pubg_id(message):
    chat_id = message.chat.id
    pubg_id = message.text.strip()
    
    user_data[chat_id]["pubg_id"] = pubg_id
    user_data[chat_id].pop("waiting_for_id") # Тоза кардани ҳолати интизори ID
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

# 3. Қабули скриншоти чек ва фиристодан ба админ
@bot.message_handler(content_types=['photo'], func=lambda message: message.chat.id in user_data and user_data[message.chat.id].get("waiting_for_screenshot"))
def receive_screenshot(message):
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id
    
    pkg = user_data[chat_id]["package"]
    price = user_data[chat_id]["price"]
    pubg_id = user_data[chat_id]["pubg_id"]
    
    user_data[chat_id].pop("waiting_for_screenshot")
    
    # Паём ба корбар
    bot.reply_to(message, "Чеки шумо қабул шуд ва ба администратор фиристод شد! ⏳\nЗакази шумо дар навбат аст. Ташаккур!")
    
    # Тугмаҳо барои админ
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

# 4. Ҷавоби админ ба заказ (Тасдиқ / Рад)
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def admin_order_handler(call):
    action, chat_id = call.data.split("_")
    chat_id = int(chat_id)
    
    if action == "approve":
        bot.answer_callback_query(call.id, "Заказ тасдиқ шуд!")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n✅ **СТАТУС: Тасдиқ шуд**", parse_mode="Markdown")
        
        # Паём ба корбар бо тугмаи отзыв ва меню
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Гузоштани отзыв", callback_data="leave_review"))
        markup.add(types.InlineKeyboardButton("🏠 Ба менюи асосӣ", callback_data="main_menu"))
        
        bot.send_message(chat_id, "60 юс ✅\n\nЗакази шумо бо муваффақият иҷро шуд! 🎮✨\n\nЛутфан, барои мо отзыв (фикру мулоҳиза) гузоред. Ин ба мо хеле кӯмак мекунад! 👇", reply_markup=markup)
        
    elif action == "reject":
        bot.answer_callback_query(call.id, "Заказ рад карда шуд.")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n❌ **СТАТУС: Рад шуд**", parse_mode="Markdown")
        bot.send_message(chat_id, "Мутаассифона, закази шумо аз ҷониби админ рад карда шуд. ❌ Лутфан бо админ дар тамос шавед.")

# 5. Оғози навиштани отзыв
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

# Қабули матни отзыв аз корбар ва фиристодан ба админ
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
    # Матнро дар хотир нигоҳ медорем то ба канал фиристед агар тасдиқ шавад
    user_data[chat_id]["last_review"] = review_text

# 6. Қарори админ дар бораи отзыв
@bot.callback_query_handler(func=lambda call: call.data.startswith("revapp_") or call.data.startswith("revrej_"))
def admin_review_handler(call):
    action, chat_id = call.data.split("_")
    chat_id = int(chat_id)
    
    if action == "revapp":
        bot.answer_callback_query(call.id, "Отзыв тасдиқ шуд!")
        bot.edit_message_text(call.message.text + "\n\n✅ **[ТАСДИҚ КАРДА ШУД]**", call.message.chat.id, call.message.message_id)
        
        # Фиристодан ба канали отзывҳо (ба ҷои @YourReviewChannel номи канали худро монед)
        review_content = user_data.get(chat_id, {}).get("last_review", "")
        # bot.send_message("@YourReviewChannel", f"💬 **Отзыви нав аз харидор:**\n\n{review_content}")
        
        bot.send_message(chat_id, "Ташаккур! Отвизи шумо аз ҷониби админ тасдиқ ва нашр шуд! 😊")
        
    elif action == "revrej":
        bot.answer_callback_query(call.id, "Отзыв рад шуд.")
        bot.edit_message_text(call.message.text + "\n\n❌ **[РАД КАРДА ШУД]**", call.message.chat.id, call.message.message_id)
        
        attempts = user_review_attempts.get(chat_id, 0)
        if attempts < 2:
            bot.send_message(chat_id, f"Отвизи шумо аз ҷониби админ рад шуд. ❌ Шумо метавонед боз **{2 - attempts} маротиба** отзыви худро аз нав нависед ва фиристед. Барои ин тугмаи «Гузоштани отзыв»-ро пахш кунед.")
        else:
            bot.send_message(chat_id, "Мутаассифона, дархости отзыви шумо ду маротиба пай дар пай рад шуд. Шумо дигар лимити отзыв гузоштан надоред. 🚫")

@bot.callback_query_handler(func=lambda call: call.data == "main_menu")
def back_to_menu(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "🏠 Шумо ба менюи асосӣ баргаштед. Марҳамат, хизматрасониро интихоб кунед:")
