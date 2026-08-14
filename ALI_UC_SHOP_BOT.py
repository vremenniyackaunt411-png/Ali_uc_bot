import telebot
from telebot import types
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

ADMIN_ID = 6871575684  
TOKEN = "8660164143:AAGL13-xIC2pln1JKKYiPQagb2dzn6N9hhQ"

state_storage = StateMemoryStorage()
bot = telebot.TeleBot(TOKEN, state_storage=state_storage)

# --- БАЗАИ МАЪЛУМОТИ ХОТИРАВӢ (IN-MEMORY DB) ---
users_db = {}  # {chat_id: {"name": str, "username": str, "orders_count": int, "approved_orders": int, "rejected_orders": int}}
orders_db = [] # [{"id": int, "user_id": int, "user_name": str, "pubg_id": str, "uc": int, "price": int, "file_id": str, "status": str, "reason": str}]
reviews_db = [] # [{"id": int, "user_id": int, "user_name": str, "text": str, "status": str, "reason": str}]
cart_db = {} # {chat_id: {"uc": int, "price": int}}

UC_PACKAGES = {
    60: 10,
    120: 20,
    180: 30,
    325: 48,
    385: 58,
    660: 92,
    720: 102,
    1320: 184,
    1800: 240,
    3850: 450,
    8100: 870
}

# --- HOЛАТҲО (STATES) ---
class UserStates(StatesGroup):
    waiting_for_pubg_id = State()
    waiting_for_receipt = State()
    waiting_for_admin_msg = State()
    waiting_for_review = State()

class AdminStates(StatesGroup):
    waiting_for_reject_reason = State()
    waiting_for_review_reject_reason = State()
    waiting_for_admin_reply = State()
    waiting_for_broadcast_msg = State()
    waiting_for_direct_msg = State()
    waiting_for_add_package = State()
    waiting_for_delete_package = State()
    waiting_for_edit_package = State()

# --- ВСЕОБЩИЕ ФУНКСИЯҲОИ МЕНЮ ---
def get_user_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🛒 Харидани UC", callback_data="user_buy_uc"),
        types.InlineKeyboardButton("📦 Заказҳои ман", callback_data="user_my_orders")
    )
    markup.add(
        types.InlineKeyboardButton("🌟 Отзывҳо", callback_data="user_reviews"),
        types.InlineKeyboardButton("📞 Алоқа бо админ", callback_data="user_contact_admin")
    )
    return markup

def get_admin_main_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📦 Заказҳо", "🌟 Отзывҳо")
    markup.row("🏆 Корбарони муваффақ", "⚙️ Танзими ЮС")
    return markup

def register_user_if_not_exists(user):
    if user.id not in users_db:
        users_db[user.id] = {
            "name": user.first_name,
            "username": f"@{user.username}" if user.username else "Надорад",
            "orders_count": 0,
            "approved_orders": 0,
            "rejected_orders": 0
        }

# --- 1. СТАРТ ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    chat_id = message.chat.id
    bot.delete_state(chat_id, chat_id)
    register_user_if_not_exists(message.from_user)

    if chat_id == ADMIN_ID:
        bot.send_message(chat_id, "Хуш омадед, Админ! Панели идоракунӣ:", reply_markup=get_admin_main_markup())
    else:
        text = (
            "Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥\n\n"
            "Дар ин ҷо шумо метавонед бо нархи дастрас ва бехатар UC (ЮС) харидорӣ кунед.\n"
            "Лутфан яке аз тугмаҳои зеринро интихоб кунед: 👇"
        )
        bot.send_message(chat_id, text, reply_markup=get_user_main_markup(), parse_mode="Markdown")

# ==================== СЕНАРИЯИ КОРБАР ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_"))
def user_callback_handler(call):
    chat_id = call.message.chat.id
    register_user_if_not_exists(call.from_user)

    if call.data == "user_main_menu":
        bot.delete_state(chat_id, chat_id)
        bot.edit_message_text("Салом! Хуш омадед ба мағозаи расмии **ALI UC SHOP** 🎮🔥\n\nЛутфан яке аз тугмаҳои зеринро интихоб кунед: 👇",
                              chat_id, call.message.message_id, reply_markup=get_user_main_markup(), parse_mode="Markdown")

    elif call.data == "user_buy_uc":
        if chat_id not in cart_db:
            cart_db[chat_id] = {"uc": 0, "price": 0}
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        sorted_packages = dict(sorted(UC_PACKAGES.items()))
        for uc, pr in sorted_packages.items():
            markup.add(types.InlineKeyboardButton(f"💎 {uc} UC — {pr} сомонӣ", callback_data=f"add_cart_{uc}_{pr}"))
        
        curr_uc = cart_db[chat_id]["uc"]
        curr_pr = cart_db[chat_id]["price"]
        
        markup.row(
            types.InlineKeyboardButton("🗑️ Очистить", callback_data="cart_clear"),
            types.InlineKeyboardButton("✅ Харидан", callback_data="cart_checkout")
        )
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        
        msg_text = f"🛒 **Интихоби ЮС:**\n\nИнтихобшуда: **{curr_uc} UC**\nМаблағ: **{curr_pr} сомонӣ**\n\nПакетҳоро зер карда илова кунед:"
        bot.edit_message_text(msg_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("add_cart_"):
        _, _, uc, pr = call.data.split("_")
        if chat_id not in cart_db:
            cart_db[chat_id] = {"uc": 0, "price": 0}
        cart_db[chat_id]["uc"] += int(uc)
        cart_db[chat_id]["price"] += int(pr)
        bot.answer_callback_query(call.id, f"+{uc} UC илова шуд!")
        user_callback_handler(type('obj', (object,), {'message': call.message, 'data': 'user_buy_uc', 'from_user': call.from_user, 'id': call.id}))

    elif call.data == "cart_clear":
        cart_db[chat_id] = {"uc": 0, "price": 0}
        bot.answer_callback_query(call.id, "Сабад тоза шуд!")
        user_callback_handler(type('obj', (object,), {'message': call.message, 'data': 'user_buy_uc', 'from_user': call.from_user, 'id': call.id}))

    elif call.data == "cart_checkout":
        if chat_id not in cart_db or cart_db[chat_id]["uc"] == 0:
            bot.answer_callback_query(call.id, "⚠️ Лутфан аввал миқдори ЮС-ро интихоб кунед!", show_alert=True)
            return
        
        bot.set_state(chat_id, UserStates.waiting_for_pubg_id, chat_id)
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_buy_uc"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        text = "⚠️ **Лутфан PUBG ID-и худро бодиққат ва бехато равон кунед!**\nАгар ID хато бошад, мо ҷавобгӯ нестем."
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "user_my_orders":
        u_info = users_db.get(chat_id, {})
        m_count = u_info.get("orders_count", 0)
        app_count = u_info.get("approved_orders", 0)
        rej_count = u_info.get("rejected_orders", 0)
        
        text = (
            f"📦 **Заказҳои ман:**\n\n"
            f"📊 Миқдори умумии заказҳо: **{m_count}**\n"
            f"✅ Заказҳои иҷрошуда: **{app_count}**\n"
            f"❌ Заказҳои радшуда: **{rej_count}**"
        )
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "user_reviews":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("💬 Гузаштан ба канали отзывҳо", url="https://t.me/otziv_ALI_US_SHOPP"))
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        text = "🌟 **Канали отзывҳои мизоҷони мо:**\nМарҳамат, бо зер кардани тугмаи зерин ба канал гузаред: 👇"
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "user_contact_admin":
        bot.set_state(chat_id, UserStates.waiting_for_admin_msg, chat_id)
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        text = "📞 **Алоқа бо администратор:**\n\nДар ҳамин ҷо нависед, админ хатман ба шумо ҷавоб медиҳад!"
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "user_leave_review":
        bot.set_state(chat_id, UserStates.waiting_for_review, chat_id)
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_main_menu"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        bot.send_message(chat_id, "Лутфан, фикру мулоҳиза ё отзыви худро нависед: 👇", reply_markup=markup)

# Интизории PUBG ID
@bot.message_handler(state=UserStates.waiting_for_pubg_id)
def process_pubg_id(message):
    chat_id = message.chat.id
    pubg_id = message.text.strip()
    
    with bot.retrieve_data(chat_id, chat_id) as data:
        data['pubg_id'] = pubg_id

    cart_info = cart_db.get(chat_id, {"uc": 0, "price": 0})
    
    bot.set_state(chat_id, UserStates.waiting_for_receipt, chat_id)
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("⬅️ Ба қафо", callback_data="user_buy_uc"),
        types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
    )
    
    text = (
        f"💎 Миқдори ЮС: **{cart_info['uc']} UC**\n"
        f"💰 Миқдори маблағ: **{cart_info['price']} сомонӣ**\n\n"
        f"РЕКВИЗИТИ КАРТЫ 🎫 👇\n\n"
        f"👉 Бонки Эсхата: `555050093`\nБа номи Орифчон Г. М.\n\n"
        f"👉 ДУШАНБЕ СИТИ: `555050093`\nБа номи Орифчон Г. М.\n\n"
        f"👉 АЛИФ БАНК: `555050093`\nБа номи Орифчон Г. М.\n\n"
        f"**Баъд аз равон кардани маблағ чеки лозимаро (скриншот) равон кунед!** 📸"
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# Интизории Скриншот
@bot.message_handler(state=UserStates.waiting_for_receipt, content_types=['photo'])
def process_receipt(message):
    chat_id = message.chat.id
    file_id = message.photo[-1].file_id
    
    pubg_id = ""
    with bot.retrieve_data(chat_id, chat_id) as data:
        pubg_id = data.get('pubg_id', 'Номаълум')
        
    cart_info = cart_db.get(chat_id, {"uc": 0, "price": 0})
    bot.delete_state(chat_id, chat_id)
    
    order_id = len(orders_db) + 1
    user_name = message.from_user.first_name
    orders_db.append({
        "id": order_id,
        "user_id": chat_id,
        "user_name": user_name,
        "pubg_id": pubg_id,
        "uc": cart_info['uc'],
        "price": cart_info['price'],
        "file_id": file_id,
        "status": "Нав",
        "reason": ""
    })
    
    users_db[chat_id]["orders_count"] += 1
    cart_db[chat_id] = {"uc": 0, "price": 0}

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
    bot.reply_to(message, "Закази шумо ба админ равон карда шуд. Дар муддати кӯтоҳтарин юс ба айди пубг ирсол карда мешавад. Мунтазир шавед.", reply_markup=markup)
    
    # Хабар ба админ
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Иҷро шуд", callback_data=f"adm_app_{order_id}"),
        types.InlineKeyboardButton("❌ Иҷро нашуд", callback_data=f"adm_rej_{order_id}")
    )
    adm_txt = f"🔔 **Закази нав №{order_id}**\n👤 Корбар: {user_name} (`{chat_id}`)\n🆔 PUBG ID: `{pubg_id}`\n💎 UC: {cart_info['uc']}\n💰 Маблағ: {cart_info['price']} сомонӣ"
    bot.send_photo(ADMIN_ID, file_id, caption=adm_txt, reply_markup=admin_markup, parse_mode="Markdown")

# Огоҳӣ агар ба ҷои фото матн фиристад
@bot.message_handler(state=UserStates.waiting_for_receipt, content_types=['text', 'voice', 'document'])
def process_receipt_wrong(message):
    bot.reply_to(message, "⚠️ Лутфан танҳо **скриншоти чеки пардохт (расм)**-ро фиристед!")

# Интизории паём ба Админ
@bot.message_handler(state=UserStates.waiting_for_admin_msg, content_types=['text', 'photo', 'voice'])
def process_user_msg_to_admin(message):
    chat_id = message.chat.id
    bot.delete_state(chat_id, chat_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ Ҷавоб додан", callback_data=f"reply_to_user_{chat_id}"))
    
    user_info = f"📩 **Паёми нав аз корбар:** {message.from_user.first_name} (`{chat_id}`)"
    
    if message.content_type == 'text':
        bot.send_message(ADMIN_ID, f"{user_info}\n\n📝 Матн: {message.text}", reply_markup=markup, parse_mode="Markdown")
    elif message.content_type == 'photo':
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=user_info, reply_markup=markup, parse_mode="Markdown")
    elif message.content_type == 'voice':
        bot.send_voice(ADMIN_ID, message.voice.file_id, caption=user_info, reply_markup=markup, parse_mode="Markdown")
        
    bot.reply_to(message, "Дар ҳамин ҷо нависед, админ хатман ба шумо ҷавоб медиҳад.")

# Интизории отзыв
@bot.message_handler(state=UserStates.waiting_for_review)
def process_user_review(message):
    chat_id = message.chat.id
    bot.delete_state(chat_id, chat_id)
    
    rev_id = len(reviews_db) + 1
    reviews_db.append({
        "id": rev_id,
        "user_id": chat_id,
        "user_name": message.from_user.first_name,
        "text": message.text,
        "status": "Нав",
        "reason": ""
    })
    
    adm_markup = types.InlineKeyboardMarkup()
    adm_markup.add(
        types.InlineKeyboardButton("🟢 Қабул шуд", callback_data=f"rev_app_{rev_id}"),
        types.InlineKeyboardButton("🔴 Қабул нашуд", callback_data=f"rev_rej_{rev_id}")
    )
    
    bot.send_message(ADMIN_ID, f"🌟 **Отзыви нав №{rev_id}:**\n👤 Аз: {message.from_user.first_name}\n📝 Матн: {message.text}", reply_markup=adm_markup)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
    bot.send_message(chat_id, "Отзыви шумо фиристода шуд! Мунтазири тасдиқи админ бошед.", reply_markup=markup)

# ==================== СЕНАРИЯИ АДМИН ====================

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text in ["📦 Заказҳо", "🌟 Отзывҳо", "🏆 Корбарони муваффақ", "⚙️ Танзими ЮС"])
def admin_menu_handler(message):
    text = message.text
    
    if text == "📦 Заказҳо":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🆕 Заказҳои нав", "📋 Ҳамаи заказҳо")
        markup.row("✅ Заказҳои Иҷрошуда", "❌ Заказҳои радшуда")
        markup.row("🏠 Ба менюи асосӣ")
        bot.send_message(ADMIN_ID, "📦 Бахши заказҳо:", reply_markup=markup)

    elif text == "🌟 Отзывҳо":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("🆕 Отзывҳои нав", "📋 Ҳамаи отзывҳо")
        markup.row("✅ Отзывҳои қабулшуда", "❌ Отзывҳои радшуда")
        markup.row("🏠 Ба менюи асосӣ")
        bot.send_message(ADMIN_ID, "🌟 Бахши отзывҳо:", reply_markup=markup)

    elif text == "🏆 Корбарони муваффақ":
        sorted_users = sorted(users_db.items(), key=lambda x: x[1]['approved_orders'], reverse=True)
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        for u_id, u_data in sorted_users:
            btn_txt = f"👤 {u_data['name']} | Заказҳо: {u_data['approved_orders']}"
            markup.add(types.InlineKeyboardButton(btn_txt, callback_data=f"adm_user_info_{u_id}"))
            
        markup.add(types.InlineKeyboardButton("📢 Паём ба ҳама", callback_data="adm_broadcast_all"))
        bot.send_message(ADMIN_ID, "🏆 **Рӯйхати корбарон (аз бисёр ба кам):**", reply_markup=markup, parse_mode="Markdown")

    elif text == "⚙️ Танзими ЮС":
        sorted_packages = dict(sorted(UC_PACKAGES.items()))
        pkg_str = "\n".join([f"💎 {uc} UC — {pr} сомонӣ" for uc, pr in sorted_packages.items()])
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Илова кардани пакет", callback_data="pkg_add"),
            types.InlineKeyboardButton("🗑️ Нест кардани пакет", callback_data="pkg_del")
        )
        markup.add(
            types.InlineKeyboardButton("✏️ Иваз кардани пакет", callback_data="pkg_edit")
        )
        bot.send_message(ADMIN_ID, f"⚙️ **Нархномаи ҷорӣ:**\n\n{pkg_str}", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID and m.text in ["🏠 Ба менюи асосӣ", "🆕 Заказҳои нав", "📋 Ҳамаи заказҳо", "✅ Заказҳои Иҷрошуда", "❌ Заказҳои радшуда", "🆕 Отзывҳои нав", "📋 Ҳамаи отзывҳо", "✅ Отзывҳои қабулшуда", "❌ Отзывҳои радшуда"])
def admin_submenus(message):
    txt = message.text
    if txt == "🏠 Ба менюи асосӣ":
        bot.send_message(ADMIN_ID, "🏠 Менюи асосӣ:", reply_markup=get_admin_main_markup())
        return

    # Заказҳо
    if txt in ["🆕 Заказҳои нав", "📋 Ҳамаи заказҳо", "✅ Заказҳои Иҷрошуда", "❌ Заказҳои радшуда"]:
        st_map = {"🆕 Заказҳои нав": "Нав", "📋 Ҳамаи заказҳо": "ALL", "✅ Заказҳои Иҷрошуда": "Иҷро шуд", "❌ Заказҳои радшуда": "Рад шуд"}
        target_st = st_map[txt]
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        for o in orders_db:
            if target_st == "ALL" or o["status"] == target_st:
                markup.add(types.InlineKeyboardButton(f"Закази №{o['id']} ({o['status']})", callback_data=f"view_ord_{o['id']}"))
        bot.send_message(ADMIN_ID, f"📋 Рӯйхат: {txt}", reply_markup=markup)

    # Отзывҳо
    elif txt in ["🆕 Отзывҳои нав", "📋 Ҳамаи отзывҳо", "✅ Отзывҳои қабулшуда", "❌ Отзывҳои радшуда"]:
        st_map = {"🆕 Отзывҳои нав": "Нав", "📋 Ҳамаи отзывҳо": "ALL", "✅ Отзывҳои қабулшуда": "Қабул шуд", "❌ Отзывҳои радшуда": "Рад шуд"}
        target_st = st_map[txt]
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        for r in reviews_db:
            if target_st == "ALL" or r["status"] == target_st:
                markup.add(types.InlineKeyboardButton(f"Отзыви №{r['id']} ({r['status']})", callback_data=f"view_rev_{r['id']}"))
        bot.send_message(ADMIN_ID, f"🌟 Рӯйхат: {txt}", reply_markup=markup)

# ИДОРАКУНИИ CALLBACK-ҲОИ АДМИН
@bot.callback_query_handler(func=lambda call: call.message.chat.id == ADMIN_ID)
def admin_callbacks(call):
    data = call.data
    
    if data.startswith("view_ord_"):
        o_id = int(data.split("_")[2])
        o = next((x for x in orders_db if x["id"] == o_id), None)
        if o:
            msg_txt = f"📦 **Закази №{o['id']}**\n👤 Корбар: {o['user_name']}\n🆔 PUBG ID: `{o['pubg_id']}`\n💎 UC: {o['uc']}\n💰 Маблағ: {o['price']} сомонӣ\n📊 Статус: {o['status']}"
            if o['reason']:
                msg_txt += f"\n❌ Сабаб: {o['reason']}"
            
            markup = types.InlineKeyboardMarkup()
            if o['status'] == "Нав":
                markup.add(
                    types.InlineKeyboardButton("✅ Иҷро шуд", callback_data=f"adm_app_{o['id']}"),
                    types.InlineKeyboardButton("❌ Иҷро нашуд", callback_data=f"adm_rej_{o['id']}")
                )
            bot.send_photo(ADMIN_ID, o['file_id'], caption=msg_txt, reply_markup=markup, parse_mode="Markdown")

    elif data.startswith("adm_app_"):
        o_id = int(data.split("_")[2])
        o = next((x for x in orders_db if x["id"] == o_id), None)
        if o:
            o["status"] = "Иҷро шуд"
            users_db[o["user_id"]]["approved_orders"] += 1
            
            bot.answer_callback_query(call.id, "Заказ тасдиқ шуд!")
            
            # Ба корбар
            usr_markup = types.InlineKeyboardMarkup()
            usr_markup.add(types.InlineKeyboardButton("🌟 Гузоштани отзыв", callback_data="user_leave_review"))
            usr_markup.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
            bot.send_message(o["user_id"], f"{o['uc']} юс ИРСОЛ КАРДА ШУД ✅", reply_markup=usr_markup)

    elif data.startswith("adm_rej_"):
        o_id = int(data.split("_")[2])
        bot.set_state(ADMIN_ID, AdminStates.waiting_for_reject_reason, ADMIN_ID)
        with bot.retrieve_data(ADMIN_ID, ADMIN_ID) as state_data:
            state_data['target_order_id'] = o_id
        bot.send_message(ADMIN_ID, "Сабаби иҷро нашудани заказро нависед:")

    # Отзывҳо
    elif data.startswith("view_rev_"):
        r_id = int(data.split("_")[2])
        r = next((x for x in reviews_db if x["id"] == r_id), None)
        if r:
            msg_txt = f"🌟 **Отзыви №{r['id']}**\n👤 Аз: {r['user_name']}\n📝 Матн: {r['text']}\n📊 Статус: {r['status']}"
            markup = types.InlineKeyboardMarkup()
            if r['status'] == "Нав":
                markup.add(
                    types.InlineKeyboardButton("🟢 Қабул шуд", callback_data=f"rev_app_{r['id']}"),
                    types.InlineKeyboardButton("🔴 Қабул нашуд", callback_data=f"rev_rej_{r['id']}")
                )
            bot.send_message(ADMIN_ID, msg_txt, reply_markup=markup)

    elif data.startswith("rev_app_"):
        r_id = int(data.split("_")[2])
        r = next((x for x in reviews_db if x["id"] == r_id), None)
        if r:
            r["status"] = "Қабул шуд"
            usr_markup = types.InlineKeyboardMarkup()
            usr_markup.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
            bot.send_message(r["user_id"], "Отзыви шумо қабул шуд!", reply_markup=usr_markup)
            bot.answer_callback_query(call.id, "Тасдиқ шуд!")

    elif data.startswith("rev_rej_"):
        r_id = int(data.split("_")[2])
        bot.set_state(ADMIN_ID, AdminStates.waiting_for_review_reject_reason, ADMIN_ID)
        with bot.retrieve_data(ADMIN_ID, ADMIN_ID) as state_data:
            state_data['target_review_id'] = r_id
        bot.send_message(ADMIN_ID, "Сабаби қабул нашудани отзывро нависед:")

    # Корбарон ва паёмҳо
    elif data.startswith("adm_user_info_"):
        u_id = int(data.split("_")[3])
        u = users_db.get(u_id, {})
        text = f"👤 Корбар: {u.get('name')}\nНикнейм: {u.get('username')}\nЗаказҳо: {u.get('orders_count')}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📩 Фиристодани паём", callback_data=f"send_direct_msg_{u_id}"))
        bot.send_message(ADMIN_ID, text, reply_markup=markup)

    elif data.startswith("send_direct_msg_"):
        u_id = int(data.split("_")[3])
        bot.set_state(ADMIN_ID, AdminStates.waiting_for_direct_msg, ADMIN_ID)
        with bot.retrieve_data(ADMIN_ID, ADMIN_ID) as state_data:
            state_data['target_user_id'] = u_id
        bot.send_message(ADMIN_ID, "Паёми худро барои ин корбар нависед:")

    elif data == "adm_broadcast_all":
        bot.set_state(ADMIN_ID, AdminStates.waiting_for_broadcast_msg, ADMIN_ID)
        bot.send_message(ADMIN_ID, "Паёмеро, ки ба ҲАМАИ корбарон фиристодан мехоҳед, нависед:")

    elif data.startswith("reply_to_user_"):
        u_id = int(data.split("_")[3])
        bot.set_state(ADMIN_ID, AdminStates.waiting_for_admin_reply, ADMIN_ID)
        with bot.retrieve_data(ADMIN_ID, ADMIN_ID) as state_data:
            state_data['reply_user_id'] = u_id
        bot.send_message(ADMIN_ID, "Ҷавоби худро нависед:")

    # Танзими пакетҳо
    elif data == "pkg_add":
        bot.set_state(ADMIN_ID, AdminStates.waiting_for_add_package, ADMIN_ID)
        bot.send_message(ADMIN_ID, "Миқдори ЮС ва нархро бо фосила нависед (Масал: `90 15`):", parse_mode="Markdown")

    elif data == "pkg_del":
        bot.set_state(ADMIN_ID, AdminStates.waiting_for_delete_package, ADMIN_ID)
        bot.send_message(ADMIN_ID, "Миқдори ЮСеро, ки нест кардан мехоҳед, нависед (Масал: `60`):")

    elif data == "pkg_edit":
        bot.set_state(ADMIN_ID, AdminStates.waiting_for_edit_package, ADMIN_ID)
        bot.send_message(ADMIN_ID, "Миқдори ЮС ва нархи навро нависед (Масал: `60 12`):", parse_mode="Markdown")

# ХАНДЛЕРҲОИ ИНТИЗОРИИ АДМИН (STATES)
@bot.message_handler(state=AdminStates.waiting_for_reject_reason)
def process_order_reject_reason(message):
    reason = message.text
    o_id = None
    with bot.retrieve_data(ADMIN_ID, ADMIN_ID) as data:
        o_id = data.get('target_order_id')
    bot.delete_state(ADMIN_ID, ADMIN_ID)
    
    o = next((x for x in orders_db if x["id"] == o_id), None)
    if o:
        o["status"] = "Рад шуд"
        o["reason"] = reason
        users_db[o["user_id"]]["rejected_orders"] += 1
        
        usr_markup = types.InlineKeyboardMarkup()
        usr_markup.add(types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu"))
        bot.send_message(o["user_id"], f"Закази шумо рад шуд.\nСабаб: {reason}", reply_markup=usr_markup)
        bot.send_message(ADMIN_ID, "Хабар ба корбар фиристода шуд!")

@bot.message_handler(state=AdminStates.waiting_for_review_reject_reason)
def process_review_reject_reason(message):
    reason = message.text
    r_id = None
    with bot.retrieve_data(ADMIN_ID, ADMIN_ID) as data:
        r_id = data.get('target_review_id')
    bot.delete_state(ADMIN_ID, ADMIN_ID)
    
    r = next((x for x in reviews_db if x["id"] == r_id), None)
    if r:
        r["status"] = "Рад шуд"
        r["reason"] = reason
        usr_markup = types.InlineKeyboardMarkup()
        usr_markup.add(
            types.InlineKeyboardButton("🌟 Гузоштани дубораи отзыв", callback_data="user_leave_review"),
            types.InlineKeyboardButton("🏠 Менюи асосӣ", callback_data="user_main_menu")
        )
        bot.send_message(r["user_id"], f"Отзыви шумо қабул нашуд.\nСабаб: {reason}", reply_markup=usr_markup)
        bot.send_message(ADMIN_ID, "Хабар ба корбар фиристода шуд!")

@bot.message_handler(state=AdminStates.waiting_for_admin_reply)
def process_admin_reply(message):
    u_id = None
    with bot.retrieve_data(ADMIN_ID, ADMIN_ID) as data:
        u_id = data.get('reply_user_id')
    bot.delete_state(ADMIN_ID, ADMIN_ID)
    
    try:
        bot.send_message(u_id, f"📢 **Ҷавоб аз админ:**\n\n{message.text}", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, "Ҷавоб расонида шуд!")
    except Exception:
        bot.send_message(ADMIN_ID, "Хатогӣ дар фиристодани паём!")

@bot.message_handler(state=AdminStates.waiting_for_direct_msg)
def process_direct_msg(message):
    u_id = None
    with bot.retrieve_data(ADMIN_ID, ADMIN_ID) as data:
        u_id = data.get('target_user_id')
    bot.delete_state(ADMIN_ID, ADMIN_ID)
    
    try:
        bot.send_message(u_id, f"📩 **Паём аз админ:**\n\n{message.text}")
        bot.send_message(ADMIN_ID, "Паём фиристода шуд!")
    except Exception:
        bot.send_message(ADMIN_ID, "Хатогӣ дар фиристодани паём!")

@bot.message_handler(state=AdminStates.waiting_for_broadcast_msg)
def process_broadcast_msg(message):
    bot.delete_state(ADMIN_ID, ADMIN_ID)
    count = 0
    for u_id in users_db.keys():
        try:
            bot.send_message(u_id, f"📢 **Хабари муҳим:**\n\n{message.text}")
            count += 1
        except Exception:
            pass
    bot.send_message(ADMIN_ID, f"Паём ба {count} корбар муваффақона фиристода шуд!")

@bot.message_handler(state=AdminStates.waiting_for_add_package)
def process_add_pkg(message):
    bot.delete_state(ADMIN_ID, ADMIN_ID)
    try:
        uc, pr = map(int, message.text.split())
        UC_PACKAGES[uc] = pr
        bot.send_message(ADMIN_ID, f"✅ Пакети {uc} UC бо нархи {pr} сомонӣ илова шуд!")
    except Exception:
        bot.send_message(ADMIN_ID, "❌ Хатогӣ дар формати воридот. Масал: `90 15`")

@bot.message_handler(state=AdminStates.waiting_for_delete_package)
def process_del_pkg(message):
    bot.delete_state(ADMIN_ID, ADMIN_ID)
    try:
        uc = int(message.text.strip())
        if uc in UC_PACKAGES:
            del UC_PACKAGES[uc]
            bot.send_message(ADMIN_ID, f"🗑️ Пакети {uc} UC нест карда шуд!")
        else:
            bot.send_message(ADMIN_ID, "❌ Чунин пакет ёфт нашуд.")
    except Exception:
        bot.send_message(ADMIN_ID, "❌ Лутфан танҳо рақам ворид кунед.")

@bot.message_handler(state=AdminStates.waiting_for_edit_package)
def process_edit_pkg(message):
    bot.delete_state(ADMIN_ID, ADMIN_ID)
    try:
        uc, pr = map(int, message.text.split())
        UC_PACKAGES[uc] = pr
        bot.send_message(ADMIN_ID, f"✏️ Нархи пакети {uc} UC ба {pr} сомонӣ иваз карда шуд!")
    except Exception:
        bot.send_message(ADMIN_ID, "❌ Хатогӣ дар формати воридот. Масал: `60 12`")

bot.infinity_polling()
