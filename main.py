import os
import time
import random
import re
import json
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# ТОКЕНИ БОТ ВА ID-И СОҲИБИ АСОСӢ
TOKEN = '8805476577:AAHlJF4UlB-n4bFRpMqKgj7WKqsXQp-LQqA'
ADMIN_ID = 6871575684

# Никнейми асосии соҳиби бот
MY_MAIN_ADMIN = "@ALI_UC_SHOPP"

bot = telebot.TeleBot(TOKEN)

# ----------------- ҚИСМИ ВЕБ-СЕРВЕР БАРОИ RENDER -----------------
app = Flask('')

@app.route('/')
def home():
    return "Бот бо муваффақият кор карда истодааст ва порт зинда аст!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
# -----------------------------------------------------------------

user_link_warnings = {}    
user_badword_warnings = {} 

# Базаи маълумот
registered_admins = {
    ADMIN_ID: {"username": MY_MAIN_ADMIN, "group_username": None}
}
active_groups = {}
user_states = {}

BAD_WORDS = [
    'кунте', 'кунти', 'гандон', 'сука',
    'далбаёб', 'кери', 'керм', 'мегом', 'бгом', 'гойда', 'сина'
]

# ----------------- СИСТЕМАИ САБТ ВА БОРКУНИИ ФАЙЛҲОИ JSON -----------------
def load_data():
    global registered_admins, active_groups
    if os.path.exists('admins.json'):
        try:
            with open('admins.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                registered_admins = {int(k): v for k, v in data.items()}
            print("Админҳо аз файл бор карда шуданд.")
        except Exception as e:
            print(f"Хатогии боркунии файл: {e}")
    else:
        registered_admins = {ADMIN_ID: {"username": MY_MAIN_ADMIN, "group_username": None}}

    if os.path.exists('groups.json'):
        try:
            with open('groups.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                active_groups = {int(k): v for k, v in data.items()}
            print("Гурӯҳҳо аз файл бор карда шуданд.")
        except Exception as e:
            print(f"Хатогӣ ҳангоми боркунии гурӯҳҳо: {e}")

def save_data():
    try:
        with open('admins.json', 'w', encoding='utf-8') as f:
            json.dump(registered_admins, f, ensure_ascii=False, indent=4)
        with open('groups.json', 'w', encoding='utf-8') as f:
            json.dump(active_groups, f, ensure_ascii=False, indent=4)
        print("Маълумот бо муваффақият сабт шуд.")
    except Exception as e:
        print(f"Хатогӣ ҳангоми сабт ба файл: {e}")

load_data()
# --------------------------------------------------------------------------

def send_reaction(chat_id, message_id, emoji):
    try:
        bot.set_message_reaction(
            chat_id=chat_id,
            message_id=message_id,
            reaction=[telebot.types.ReactionTypeEmoji(emoji)]
        )
    except Exception as e:
        print(f"Хатогӣ ҳангоми гузоштани реаксия: {e}")

def is_admin_in_this_chat(chat_id, message):
    if message.chat.type == 'private':
        return False
    if message.sender_chat is not None:
        return True
    try:
        member = bot.get_chat_member(chat_id, message.from_user.id)
        if member.status in ['administrator', 'creator']:
            return True
    except Exception as e:
        print(f"Хатогӣ ҳангоми санҷиши ҳуқуқи admin: {e}")
    return False

def get_admin_mention(chat_id):
    try:
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id in registered_admins and admin.user.id != ADMIN_ID:
                return registered_admins[admin.user.id]['username']
        for admin in admins:
            if admin.user.id == ADMIN_ID:
                return MY_MAIN_ADMIN
    except Exception as e:
        print(f"Хатогӣ ҳангоми гирифтани админҳои гурӯҳ: {e}")
    return "Админ"

def get_answers(chat_id):
    admin = get_admin_mention(chat_id)
    return {
        'салом': 'Салом! Хушхолам шуморо мебинам 🫶',
        'ссалом': 'ВОАЛЛЕЙКУМ САЛОМ ! Хуш омадед ❤️',
        'сети': 'МАН ДАР СЕТАМ 24/7 🥰 \nБарои мухофизати гурух сохта шудаам. ',
        'хуби': 'Хубам, раҳмат! 🥰. Шумо чихел?',
        'sozi': 'Хубам, раҳмат! 🥰. Шумо чихел?',
        'сози': 'Хубам, раҳмат! 🥰. Шумо чихел?',
        'юс': f'Барои нарх ба {admin} муроҷиат кунед.',
        'uc': f'Барои нарх ба {admin} муроҷиат кунед.',
        'админ': f' {admin} <--- админ.',
        'admin': f' {admin} <--- admin.',
        'нарх': f'нархо барои харидани юс {admin} нависен ❤️',
        'narx': f'нархо барои харидани юс {admin} нависен ❤️',
        'рахмат': 'САЛОМАТ БОШЕН 🫶',
        'ки мехара': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'хариданийм': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'фуруши дорм': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'мефурушм': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'мехарм': f'√1 ГАРАНТ {admin} ❤️ нависен. \n АГАР бе гарант СКАМ ХУРДЕН АДМИН ГНАХГОР НЕСТ!',
        'аккаунт': f'аккаунт харидан ё фурухтани бошен лс {admin} ❤️ нависен',
        'акаунт': f'аккаунт харидан ё фурухтани бошен лс {admin} ❤️ нависен',
        'бот': f'СаЛоМ. \nМан зехни сунъи хастам ёрдамчии {admin} ❤️ хастам'
    }

def has_link_or_nickname(message):
    if message.entities:
        for entity in message.entities:
            if entity.type in ['url', 'text_link', 'mention']:
                return True
    if message.caption_entities: 
        for entity in message.caption_entities:
            if entity.type in ['url', 'text_link', 'mention']:
                return True
                
    text = (message.text or message.caption or "").lower()
    if text:
        if "http" in text or "t.me" in text or "@" in text:
            if MY_MAIN_ADMIN.lower() in text or "bot" in text:
                return False
            return True
    return False

def is_forwarded_message(message):
    if message.forward_from or message.forward_from_chat or message.forward_signature:
        return True
    if message.forward_sender_name:
        return True
    return False

def find_bad_word(text):
    if not text:
        return None
    text = text.lower()
    for word in BAD_WORDS:
        if word in text:
            return word
    return None

def restrict_user(chat_id, user_id, seconds):
    try:
        until_date = int(time.time()) + seconds
        permissions = telebot.types.ChatPermissions(
            can_send_messages=False, can_send_media_messages=False,
            can_send_audios=False, can_send_documents=False,
            can_send_photos=False, can_send_videos=False,
            can_send_video_notes=False, can_send_voice_notes=False,
            can_send_polls=False, can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        bot.restrict_chat_member(chat_id, user_id, until_date=until_date, permissions=permissions)
    except Exception as e:
        print(f"Хатогӣ ҳангоми маҳдуд кардани корбар: {e}")

def get_bottom_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_menu = types.KeyboardButton("🏠 Менюи Асосӣ")
    btn_update = types.KeyboardButton("🔄 Навсозӣ (Обновить)")
    markup.row(btn_menu, btn_update)
    return markup

def get_start_keyboard(bot_username, user_id):
    markup = types.InlineKeyboardMarkup()
    btn_register = types.InlineKeyboardButton("📝 Рӯйхати сабти Админ", callback_data="register_username_step")
    btn_my_info = types.InlineKeyboardButton("ℹ️ Маълумоти ман", callback_data="my_info")
    markup.row(btn_register, btn_my_info)
    
    if user_id == ADMIN_ID:
        btn_owner_groups = types.InlineKeyboardButton("⚙️ Гурӯҳҳои ман", callback_data="owner_groups")
        markup.row(btn_owner_groups)
    
    add_to_group_url = f"https://t.me/{bot_username}?startgroup=true"
    btn_add_group = types.InlineKeyboardButton("➕ Илова кардан ба гурӯҳ", url=add_to_group_url)
    markup.row(btn_add_group)
    
    return markup


# ================= КУШОДАНИ ЧАТИ ШАХСӢ БО БОТ =================

@bot.message_handler(commands=['start'], chat_types=['private'])
def start_private(message):
    user_id = message.from_user.id
    bot_info = bot.get_me()
    
    if user_id in user_states:
        del user_states[user_id]
        
    if user_id == ADMIN_ID:
        registered_admins[ADMIN_ID] = {"username": MY_MAIN_ADMIN, "group_username": None}
        save_data()
        welcome_text = (
            f"Салом, Оғои Император! 👑\n\n"
            f"Шумо соҳиби асосии бот ҳастед. Маълумоти шумо ба таври худкор сабт шуд:\n"
            f"👤 Никнейми шумо: `{MY_MAIN_ADMIN}`\n\n"
            f"Идоракунии бот ва гурӯҳҳо аз менюи зерин 👇"
        )
    else:
        welcome_text = (
            f"Салом, {message.from_user.first_name}! 🤖\n\n"
            f"Ман боти муҳофизи гурӯҳ ва ёрдамчии admin ҳастам.\n"
            f"Барои бақайдгирӣ ва ҳамчун Админ сабт шудан тугмаи зеринро пахш кунед."
        )

    inline_markup = get_start_keyboard(bot_info.username, user_id)
    reply_markup = get_bottom_keyboard()
    
    bot.send_message(user_id, welcome_text, reply_markup=inline_markup, parse_mode="Markdown")
    bot.send_message(user_id, "Интихоби амалҳо аз тугмаҳои поён 👇", reply_markup=reply_markup)


# ================= КОРКАРДИ ТУГМАҲОИ ПОЁНИИ МЕНЮИ АСОСӢ ВА ОБНОВИТЬ =================

@bot.message_handler(func=lambda message: message.text in ["🏠 Менюи Асосӣ", "🔄 Навсозӣ (Обновить)"], chat_types=['private'])
def handle_text_buttons(message):
    user_id = message.from_user.id
    bot_info = bot.get_me()
    
    if message.text == "🏠 Менюи Асосӣ":
        if user_id in user_states:
            del user_states[user_id]
            
        welcome_text = (
            f"Салом, {message.from_user.first_name}! 🤖\n\n"
            f"Шумо дар Менюи Асосӣ ҳастед.\n"
            f"Барои амалҳо тугмаҳои зеринро пахш кунед:"
        )
        inline_markup = get_start_keyboard(bot_info.username, user_id)
        bot.send_message(user_id, welcome_text, reply_markup=inline_markup, parse_mode="Markdown")
        
    elif message.text == "🔄 Навсозӣ (Обновить)":
        # 1. Санҷиш: Агар пахшкунанда Соҳиби бот (Император) набошад
        if user_id != ADMIN_ID:
            bot.send_message(user_id, "❌ Ин тугма танҳо барои соҳиби асосии бот (Император) дастрас аст!")
            return
            
        # 2. Агар Соҳиби бот пахш кунад - Оғози навсозии админҳо дар ҳама гурӯҳҳо
        if not active_groups:
            bot.send_message(user_id, "ℹ️ Дар база ягон гурӯҳ ёфт нашуд, ки админҳояшро навсозӣ кунам.")
            return
            
        status_message = bot.send_message(user_id, "🔄 Лутфан интизор шавед, админҳо дар гурӯҳҳо аз нав сканер ва ҷойгир карда шуда истодаанд...")
        
        updated_count = 0
        # Сканер кардани тамоми гурӯҳҳо аз базаи groups.json
        for gr_id, gr_title in list(active_groups.items()):
            try:
                # Гирифтани рӯйхати админҳои ҳақиқии гурӯҳ аз Телеграм
                admins = bot.get_chat_administrators(gr_id)
                for admin in admins:
                    # Агар админи гурӯҳ бошад, никнейм дошта бошад ва худи соҳиби бот набошад
                    if admin.user.username and admin.user.id != ADMIN_ID:
                        admin_username = f"@{admin.user.username}"
                        
                        # Кӯшиши гирифтани никнейми худи гурӯҳ барои база
                        try:
                            chat_det = bot.get_chat(gr_id)
                            gr_link = f"@{chat_det.username}" if chat_det.username else gr_title
                        except Exception:
                            gr_link = gr_title
                            
                        # Сабт ё навсозӣ кардани админ дар базаи admins.json
                        registered_admins[admin.user.id] = {
                            "username": admin_username,
                            "group_username": gr_link
                        }
                        updated_count += 1
            except Exception as e:
                print(f"Хатогӣ ҳангоми навсозии гурӯҳи {gr_title} (ID: {gr_id}): {e}")
                
        # Ҳатман маълумоти навро ба файлҳо сабт мекунем
        save_data()
        
        bot.edit_message_text(
            chat_id=user_id,
            message_id=status_message.message_id,
            text=f"✅ **Навсозӣ бо муваффақият анҷом ёфт!**\n\n"
                 f"📊 Ҳамагӣ `{updated_count}` админ(ҳо) дар гурӯҳҳои худ аз нав шинохта ва ҷойгир карда шуданд.\n"
                 f"Акнун бот админҳои шуморо дар гурӯҳҳо гум намекунад! 🔥"
        )


# ================= СИСТЕМАИ БАҚАЙДГИРӢ =================

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    bot_info = bot.get_me()
    
    if call.data == "register_username_step":
        if user_id == ADMIN_ID:
            bot.answer_callback_query(call.id, "👑 Шумо соҳиби бот ҳастед, бақайдгирӣ шарт нест!", show_alert=True)
            return
            
        user_states[user_id] = {"step": "waiting_for_username"}
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Бекор кардан", callback_data="cancel_registration"))
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="✍ *Қадами 1:*\n\nЛутфан, никнейми шахсии худро фиристед.\n"
                 "Мисол: `@username` (Ҳатман бо аломати `@` сар шавад):",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)

    elif call.data == "back_to_username":
        user_states[user_id]["step"] = "waiting_for_username"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❌ Бекор кардан", callback_data="cancel_registration"))
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="✍ *Қадами 1:*\n\nЛутфан, никнейми худро аз нав фиристед (бо `@` сар шавад):",
            reply_markup=markup,
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id)

    elif call.data == "cancel_registration":
        if user_id in user_states:
            del user_states[user_id]
        
        bot.answer_callback_query(call.id, "❌ Амал бекор карда шуд!")
        markup = get_start_keyboard(bot_info.username, user_id)
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"Салом, {call.from_user.first_name}! 🤖\n\nБақайдгирӣ бекор карда шуд. Барои сабти нав тугмаи зеринро истифода баред 👇",
            reply_markup=markup
        )

    elif call.data == "my_info":
        if user_id in registered_admins:
            data = registered_admins[user_id]
            bot.send_message(
                chat_id,
                f"📊 **Маълумоти шумо дар база:**\n\n"
                f"👤 Никнейми шумо: `{data['username']}`\n"
                f"💬 Гурӯҳи шумо: `{data.get('group_username', 'Нест')}`\n\n"
                f"Маълумоти шумо тасдиқ шудааст ва шумо ҳуқуқи админ доред. ✅"
            )
        else:
            bot.send_message(chat_id, "❌ Шумо то ҳол бақайдгирии тасдиқшуда надоред. Тугмаи '📝 Рӯйхати сабти Admin'-ро пахш кунед.")
        bot.answer_callback_query(call.id)

    elif call.data == "owner_groups":
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Ин тугма танҳо барои соҳиби бот аст!", show_alert=True)
            return
        
        if not active_groups:
            bot.send_message(chat_id, "ℹ️ Бот то ҳол ба ягон гурӯҳ илова нашудааст.")
            bot.answer_callback_query(call.id)
            return
        
        markup = types.InlineKeyboardMarkup()
        for gr_id, gr_name in active_groups.items():
            btn = types.InlineKeyboardButton(f"💬 {gr_name}", callback_data=f"sendto_{gr_id}")
            markup.add(btn)
            
        bot.send_message(chat_id, "👥 **Рӯйхати гурӯҳҳо:**\n\nГурӯҳеро интихоб кунед:", reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif call.data.startswith("sendto_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id)
            return
            
        target_group_id = int(call.data.split("_")[1])
        group_name = active_groups.get(target_group_id, "Гурӯҳи номаълум")
        
        user_states[user_id] = {
            "step": "waiting_for_broadcast_text",
            "target_group_id": target_group_id,
            "target_group_name": group_name
        }
        
        cancel_markup = types.InlineKeyboardMarkup()
        cancel_markup.add(types.InlineKeyboardButton("❌ Бекор кардан", callback_data="cancel_registration"))
        
        bot.send_message(
            chat_id,
            f"✍️ Навиштани паём ба гурӯҳи **\"{group_name}\"**:\n\n"
            f"Паёми худро фиристед. Барои бекор кардан тугмаи зеринро пахш кунед 👇",
            reply_markup=cancel_markup
        )
        bot.answer_callback_query(call.id)

    elif call.data == "check_status":
        data = user_states.get(user_id, {})
        if not data or data.get('step') != "waiting_for_group":
            bot.send_message(chat_id, "❌ Хатогӣ! Лутфан бақайдгириро аз аввал оғоз кунед /start.")
            bot.answer_callback_query(call.id)
            return
            
        group_username = data['group_username']
        nickname = data['username'].replace("@", "").lower()
        
        try:
            admins = bot.get_chat_administrators(group_username)
            
            user_is_admin = False
            for admin in admins:
                if admin.user.username and admin.user.username.lower() == nickname:
                    user_is_admin = True
                    break
            
            if user_is_admin:
                registered_admins[user_id] = {
                    "username": data["username"],
                    "group_username": group_username
                }
                
                try:
                    chat_info = bot.get_chat(group_username)
                    active_groups[chat_info.id] = chat_info.title
                except Exception:
                    pass
                
                save_data()
                del user_states[user_id]
                
                markup = get_start_keyboard(bot_info.username, user_id)
                bot.send_message(
                    chat_id,
                    f"🎉 **Ҳамааш дуруст! Бақайдгирӣ тасдиқ шуд.**\n\n"
                    f"✅ Бот дар гурӯҳи `{group_username}` бомуваффақият фаъол шуд!\n"
                    f"✅ Никнейми шумо (`@{nickname}`) ҳамчун админи ҳақиқӣ сабт гардид.\n\n"
                    f"Акнун бот дар ин гурӯҳ ба таври худкор бо никнейми шумо ба саволҳои корбарон ҷавоб медиҳад.",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(
                    chat_id,
                    f"⚠️ **Мушкилӣ ошкор шуд!**\n\n"
                    f"Бот ба гурӯҳ дастрасӣ дорад, вале никнейми `@{nickname}` дар рӯйхати администраторҳои ин гурӯҳ ёфт нашуд.\n\n"
                    f"Лутфан боварӣ ҳосил кунед, ки никнеймро дар қадами якум дуруст навиштаед ё дар он гурӯҳ ҳуқуқи админ доред.",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            bot.send_message(
                chat_id,
                f"❌ **Хатогии пайвастшавӣ!**\n\n"
                f"Бот ҳанӯз ба гурӯҳи `{group_username}` илова нашудааст ё ба он ҳуқуқи администратор дода нашудааст.\n\n"
                f"Лутфан тугмаи аввали болоро пахш карда, ботро ба гурӯҳ ҳамроҳ кунед ва ба он ҳуқуқи админ диҳед, пас аз он тугмаи санҷишро пахш кунед.",
                parse_mode="Markdown"
            )
            
        bot.answer_callback_query(call.id)


# ================= ҚАДАМҲОИ ВОРУД КАРДАНИ МАЪЛУМОТИ МАТНИИ БАҚАЙДГИРӢ =================

@bot.message_handler(func=lambda message: message.from_user.id in user_states, chat_types=['private'])
def registration_text_inputs(message):
    user_id = message.from_user.id
    state_data = user_states[user_id]
    step = state_data.get("step")
    text_input = message.text.strip() if message.text else ""
    
    if text_input == "/start":
        del user_states[user_id]
        start_private(message)
        return

    if step == "waiting_for_username":
        if not text_input.startswith("@"):
            bot.send_message(user_id, "❌ Никнейм бояд бо `@` сар шавад! Масалан: `@ALI_UC_SHOPP` \n\nЛутфан аз нав нависед:")
            return
            
        user_states[user_id]["username"] = text_input
        user_states[user_id]["step"] = "waiting_for_group"
        
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("⬅️ Ба ақиб", callback_data="back_to_username"),
            types.InlineKeyboardButton("❌ Бекор кардан", callback_data="cancel_registration")
        )
        
        bot.send_message(
            user_id,
            "👥 **Қадами 2:**\n\n"
            "Акнун **линки гурӯҳи худро** ворид кунед, ки бот дар онҷо ҳаст.\n"
            "Мисол: `https://t.me/ALI_US_SHOPP` ё `@ALI_US_SHOPP`.",
            reply_markup=markup
        )
        
    elif step == "waiting_for_group":
        group_input = text_input
        group_username = None

        if "t.me/" in group_input:
            match = re.search(r"t\.me/([^/\?]+)", group_input)
            if match:
                group_username = f"@{match.group(1)}"
        elif group_input.startswith("@"):
            group_username = group_input
        else:
            group_username = f"@{group_input}"

        if not group_username or "+" in group_username:
            bot.reply_to(message, "❌ Лутфан танҳо линки умумии гурӯҳро (ки дорои никнейми оммавӣ бошад) равон кунед. Линки хусусӣ (бо аломати +) барои санҷиши худкор кор намекунад.")
            return

        user_states[user_id]['group_username'] = group_username
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        bot_username = bot.get_me().username
        
        add_to_group_url = f"https://t.me/{bot_username}?startgroup=true&admin=post_messages+edit_messages+delete_messages+invite_users"
        
        btn_add = types.InlineKeyboardButton("➕ Илова кардани бот ва админ кардан", url=add_to_group_url)
        btn_check = types.InlineKeyboardButton("🔄 Санҷиши иҷрои корҳо", callback_data="check_status")
        btn_restart = types.InlineKeyboardButton("↩️ Аз аввал сар кардан", callback_data="cancel_registration")
        
        markup.add(btn_add, btn_check, btn_restart)
        
        text = (
            f"**Қадами 3:** Корҳои зеринро иҷро кунед:\n\n"
            f"1. Тӯгмаи аввали болоро пахш карда, ботро ба гурӯҳи худ илова кунед ва ба он ҳуқуқи **Администратор** диҳед.\n"
            f"2. Пас аз илова намудан ва ҳуқуқи админ додан, тугмаи **'🔄 Санҷиши иҷрои корҳо'**-ро пахш кунед."
        )
        bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")

    elif step == "waiting_for_broadcast_text":
        target_id = state_data["target_group_id"]
        group_name = state_data["target_group_name"]
        bot_info = bot.get_me()
        
        try:
            if message.content_type == 'text':
                bot.send_message(target_id, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(target_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(target_id, message.video.file_id, caption=message.caption)
            else:
                bot.copy_message(target_id, user_id, message.message_id)
                
            bot.send_message(user_id, f"✅ Паёми шумо ба гурӯҳи **\"{group_name}\"** расонида шуд!")
            del user_states[user_id]
            
            markup = get_start_keyboard(bot_info.username, user_id)
            bot.send_message(user_id, "Менюи асосӣ:", reply_markup=markup)
            
        except Exception as e:
            bot.send_message(user_id, f"❌ Хатогӣ ҳангоми фиристодани паём: {e}")

# ==============================================================================

# ФИЛТРИ ПАЁМҲО ВА ТОЗА КАРДАНИ НАВИШТАҶОТИ ТАГИ РАСМ ВА ВИДЕО
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'animation', 'video_note'])
def filter_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Никнейм надорад"

    if message.chat.type in ['group', 'supergroup']:
        if chat_id not in active_groups:
            active_groups[chat_id] = message.chat.title
            save_data()

    admin_status = is_admin_in_this_chat(chat_id, message)

    # 1. АГАР НАВИСАНДА АДМИН БОШАД:
    if admin_status:
        text_to_check = message.text or message.caption
        if text_to_check:
            detected_bad_word = find_bad_word(text_to_check)
            if detected_bad_word:
                send_reaction(chat_id, message.message_id, "😱")
                return

            text_lower = text_to_check.lower()
            try:
                answers = get_answers(chat_id)
                for word, answer in answers.items():
                    if word in text_lower:
                        if 'салом' in word:
                            send_reaction(chat_id, message.message_id, random.choice(["❤️", "🔥", "👍"]))
                        elif 'рахмат' in word:
                            send_reaction(chat_id, message.message_id, "🤝")
                        
                        bot.reply_to(message, answer)
                        break
            except Exception as e:
                print(f"Хатогӣ дар автоответики админ: {e}")
        return

    # 2. АГАР НАВИСАНДА КОРБАРИ ОДДӢ БОШАД:

    # А) САНҶИШИ ПЕРЕСЛАТЬ (FORWARD):
    if is_forwarded_message(message):
        try:
            bot.delete_message(chat_id, message.message_id)
            
            if user_id not in user_link_warnings:
                user_link_warnings[user_id] = 0
            
            user_link_warnings[user_id] += 1
            
            if user_link_warnings[user_id] == 1:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, Переслать (форвард) кардани паёмҳо аз дигар гурӯҳ/каналҳо манъ аст! 🚫 Огоҳӣ: (1/3)"
                )
            elif user_link_warnings[user_id] == 2:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, бори дуюм аст! Огоҳии охирин: (2/3)"
                )
            elif user_link_warnings[user_id] >= 3:
                restrict_user(chat_id, user_id, 86400)
                bot.send_message(
                    chat_id, 
                    f"🚫 Корбар {user_name} қоидаро 3 бор шикаст ва барои спам (форвард) ба муҳлати 24 соат блок шуд!"
                )
                user_link_warnings[user_id] = 0
        except Exception as e:
            print(f"Хатогӣ ҳангоми тозакунии паёми форвардшуда: {e}")
        return

    # Б) САНҶИШИ ЛИНКҲО ВА РЕКЛАМАҲО:
    if has_link_or_nickname(message):
        try:
            bot.delete_message(chat_id, message.message_id)
            
            if user_id not in user_link_warnings:
                user_link_warnings[user_id] = 0
            
            user_link_warnings[user_id] += 1
            
            if user_link_warnings[user_id] == 1:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, Ссылка ё реклама манъ аст! Нагузоред, вагарна блок мешавед. Огоҳӣ: (1/3)"
                )
            elif user_link_warnings[user_id] == 2:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, бори дуюм аст ки огохи гирифтед! Огоҳии охирин: (2/3)"
                )
            elif user_link_warnings[user_id] >= 3:
                restrict_user(chat_id, user_id, 86400)
                bot.send_message(
                    chat_id, 
                    f"🚫 Корбар {user_name} қоидаро 3 бор шикаст ва барои спам ба муҳлати 24 соат блок шуд! Пас аз 24 соат худкор кушода мешавад."
                )
                user_link_warnings[user_id] = 0
        except Exception as e:
            print(f"Хатогӣ дар антиспам: {e}")
        return

    # В) САНҶИШИ ДАШНОМҲО (дар матни паём ва зери тамоми намуди файлҳо):
    text_to_check = message.text or message.caption
    if text_to_check:
        detected_bad_word = find_bad_word(text_to_check)
        if detected_bad_word:
            try:
                bot.delete_message(chat_id, message.message_id)
                
                group_title = message.chat.title if message.chat.title else "Чат"
                report_message = (
                    f"🚨 <b>Дашном ошкор шуд!</b>\n\n"
                    f"👥 <b>Гурӯҳ:</b> {group_title} (ID: <code>{chat_id}</code>)\n"
                    f"👤 <b>Нависанда:</b> {user_name} ({username}) (ID: <code>{user_id}</code>)\n"
                    f"🤬 <b>Калимаи ёфтшуда:</b> <code>{detected_bad_word}</code>\n"
                    f"📝 <b>Паёми пурра:</b>\n<i>\"{text_to_check}\"</i>"
                )
                
                try:
                    bot.send_message(ADMIN_ID, report_message, parse_mode="HTML")
                except Exception as send_err:
                    print(f"Хатогӣ ҳангоми фиристодани отчёт ба admin: {send_err}")

                if user_id not in user_badword_warnings:
                    user_badword_warnings[user_id] = 0
                    
                user_badword_warnings[user_id] += 1
                
                current_admin = get_admin_mention(chat_id)
                if user_badword_warnings[user_id] == 1:
                    bot.send_message(
                        chat_id,
                        f"⚠️ Корбар {user_name}, \n Дар гурух суханхои кабех ва дашном манъ аст! Огоҳӣ: (1/3)\nАДМИН: {current_admin} ❤️"
                    )
                elif user_badword_warnings[user_id] == 2:
                    bot.send_message(
                        chat_id,
                        f"⚠️ Корбар {user_name}, \n Бори дуюм аст! Огоҳии охирин барои калимаҳои ноҷо: (2/3)"
                    )
                elif user_badword_warnings[user_id] >= 3:
                    restrict_user(chat_id, user_id, 28800)
                    bot.send_message(
                        chat_id,
                        f"🚫 Корбар {user_name} \n барои истифодаи суханхои кабех ё дашном ба муҳлати 8 соат блок шуд!"
                    )
                    user_badword_warnings[user_id] = 0
            except Exception as e:
                print(f"Хатогӣ дар тозакунии калимаҳо: {e}")
            return

    # Г) ҶАВОБ БА КАЛИМАҲОИ КАЛИДӢ (АВТООТВЕТЧИК):
    if message.content_type == 'text':
        text = message.text.lower()
        try:
            answers = get_answers(chat_id)
            for word, answer in answers.items():
                if word in text:
                    if 'салом' in word or 'юс' in word or 'uc' in word or 'нарх' in word:
                        send_reaction(chat_id, message.message_id, "⚡")
                    elif 'рахмат' in word:
                        send_reaction(chat_id, message.message_id, "🤝")
                    
                    bot.reply_to(message, answer)
                    return
        except Exception as e:
            print(f"Хатогӣ дар автоответики оддӣ: {e}")

        if random.random() < 0.10:
            random_emoji = random.choice(["👍", "❤️", "🔥", "🥰", "🫶", "😂", "🤯", "🩵", "🎉", "😎"])
            send_reaction(chat_id, message.message_id, random_emoji)


# ================= СИСТЕМАИ НАЗОРАТИ ПАЁМҲОИ ТАҲРИРШУДА (EDITED MESSAGES) =================

@bot.edited_message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice', 'sticker', 'animation', 'video_note'])
def filter_edited_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Никнейм надорад"

    if is_admin_in_this_chat(chat_id, message):
        return

    # 1. Санҷиши линк ва реклама ҳангоми таҳрири паём
    if has_link_or_nickname(message):
        try:
            bot.delete_message(chat_id, message.message_id)
            
            if user_id not in user_link_warnings:
                user_link_warnings[user_id] = 0
            user_link_warnings[user_id] += 1
            
            if user_link_warnings[user_id] == 1:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, Таҳрир карда илова кардани линк ё реклама манъ аст! Огоҳӣ: (1/3)"
                )
            elif user_link_warnings[user_id] == 2:
                bot.send_message(
                    chat_id, 
                    f"⚠️ Корбар {user_name}, бори дуюм аст! Огоҳии охирин: (2/3)"
                )
            elif user_link_warnings[user_id] >= 3:
                restrict_user(chat_id, user_id, 86400)
                bot.send_message(
                    chat_id, 
                    f"🚫 Корбар {user_name} қоидаро 3 бор шикаст ва барои реклама ба муҳлати 24 соат блок шуд!"
                )
                user_link_warnings[user_id] = 0
        except Exception as e:
            print(f"Хатогӣ дар антиспами таҳриршуда: {e}")
        return

    # 2. Санҷиши дашномҳо ҳангоми таҳрири паём (ҳам матн ва ҳам зери расм)
    text_to_check = message.text or message.caption
    if text_to_check:
        detected_bad_word = find_bad_word(text_to_check)
        if detected_bad_word:
            try:
                bot.delete_message(chat_id, message.message_id)
                
                group_title = message.chat.title if message.chat.title else "Чат"
                report_message = (
                    f"🚨 <b>Дашном ҳангоми таҳрири паём ошкор шуд!</b>\n\n"
                    f"👥 <b>Гурӯҳ:</b> {group_title} (ID: <code>{chat_id}</code>)\n"
                    f"👤 <b>Нависанда:</b> {user_name} ({username}) (ID: <code>{user_id}</code>)\n"
                    f"🤬 <b>Калимаи ёфтшуда:</b> <code>{detected_bad_word}</code>\n"
                    f"📝 <b>Паёми таҳриршудаи пурра:</b>\n<i>\"{text_to_check}\"</i>"
                )
                
                try:
                    bot.send_message(ADMIN_ID, report_message, parse_mode="HTML")
                except Exception as send_err:
                    print(f"Хатогӣ дар отчёти таҳрири паём: {send_err}")

                if user_id not in user_badword_warnings:
                    user_badword_warnings[user_id] = 0
                user_badword_warnings[user_id] += 1
                
                current_admin = get_admin_mention(chat_id)
                if user_badword_warnings[user_id] == 1:
                    bot.send_message(
                        chat_id,
                        f"⚠️ Корбар {user_name}, \n Таҳрир карда илова кардани суханҳои қабеҳ манъ аст! Огоҳӣ: (1/3)\nАДМИН: {current_admin} ❤️"
                    )
                elif user_badword_warnings[user_id] == 2:
                    bot.send_message(
                        chat_id,
                        f"⚠️ Корбар {user_name}, \n Бори дуюм аст! Огоҳии охирин барои калимаҳои ноҷо: (2/3)"
                    )
                elif user_badword_warnings[user_id] >= 3:
                    restrict_user(chat_id, user_id, 28800)
                    bot.send_message(
                        chat_id,
                        f"🚫 Корбар {user_name} \n барои истифодаи дашном (ҳангоми таҳрир) ба муҳлати 8 соат блок шуд!"
                    )
                    user_badword_warnings[user_id] = 0
            except Exception as e:
                print(f"Хатогӣ дар тозакунии калимаҳои таҳриршуда: {e}")
            return


if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    
    print("🤖 Бот бо муваффақият оғоз ёфт...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
