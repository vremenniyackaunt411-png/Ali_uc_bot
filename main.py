import os
import time
import random
from threading import Thread
from flask import Flask
import telebot
from telebot import types

TOKEN = '8805476577:AAHlJF4UlB-n4bFRpMqKgj7WKqsXQp-LQqA'
ADMIN_ID = 6871575684 

MY_MAIN_ADMIN = "@ALI_UC_SHOPP"
MY_CHANNEL_LINK = "https://t.me/ALI_US_SHOPP"

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

# Базаи админҳо
registered_admins = {
    ADMIN_ID: {"username": MY_MAIN_ADMIN, "channel": MY_CHANNEL_LINK}
}

active_groups = {}
user_states = {}

BAD_WORDS = [
    'кунте', 'кунти', 'гандон', 'сука',
    'далбаёб',  'кери', 'керм', 'мегом', 'бгом', 'гойда', 'сина'
]

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
        member = bot.get_chat_member(chat_id, ADMIN_ID)
        if member.status in ['creator', 'administrator']:
            return f"{MY_MAIN_ADMIN} (Канал: {MY_CHANNEL_LINK})"
    except Exception:
        pass

    try:
        admins = bot.get_chat_administrators(chat_id)
        for admin in admins:
            if admin.user.id in registered_admins:
                adm_data = registered_admins[admin.user.id]
                return f"{adm_data['username']} (Канал: {adm_data.get('channel', MY_CHANNEL_LINK)})"
    except Exception as e:
        print(f"Хатогӣ ҳангоми гирифтани админҳои гурӯҳ: {e}")

    return f"{MY_MAIN_ADMIN} (Канал: {MY_CHANNEL_LINK})"

def get_answers(chat_id):
    admin = get_admin_mention(chat_id)
    return {
        'salom': 'Воаллейкум салом !',
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
    if message.text:
        text = message.text.lower()
        if "http" in text or "t.me" in text or "@" in text:
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

def get_start_keyboard(bot_username, user_id):
    markup = types.InlineKeyboardMarkup()
    btn_register = types.InlineKeyboardButton("📝 Бақайдгирии Admin", callback_data="register_admin")
    btn_my_info = types.InlineKeyboardButton("ℹ️ Маълумоти ман", callback_data="my_info")
    markup.row(btn_register, btn_my_info)
    
    if user_id == ADMIN_ID:
        btn_owner_groups = types.InlineKeyboardButton("⚙️ Гурӯҳҳои ман (Танҳо Созанда)", callback_data="owner_groups")
        markup.row(btn_owner_groups)
    
    add_to_group_url = f"https://t.me/{bot_username}?startgroup=true"
    btn_add_group = types.InlineKeyboardButton("➕ Илова кардан ба гурӯҳ (Добавить в группу)", url=add_to_group_url)
    markup.row(btn_add_group)
    
    return markup

# Функсия барои сохтани тугмаҳои идоракунии қадамҳо (Ба ақиб / Бекор кардан)
def get_step_keyboard(step_name):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn_cancel = types.KeyboardButton("❌ Бекор кардан")
    
    # Агар қадами аввал набошад, тугмаи «Ба ақиб»-ро илова мекунем
    if step_name in ["waiting_for_channel", "waiting_for_group_verification"]:
        btn_back = types.KeyboardButton("⬅️ Ба ақиб")
        markup.row(btn_back, btn_cancel)
    else:
        markup.row(btn_cancel)
        
    return markup


# ================= КУШОДАНИ ЧАТИ ШАХСӢ БО БОТ =================

@bot.message_handler(commands=['start'], chat_types=['private'])
def start_private(message):
    user_id = message.from_user.id
    bot_info = bot.get_me()
    
    # Хомӯш кардани клавиатураи оддии қаблӣ (агар монда бошад)
    remove_markup = types.ReplyKeyboardRemove()
    
    if user_id == ADMIN_ID:
        registered_admins[ADMIN_ID] = {"username": MY_MAIN_ADMIN, "channel": MY_CHANNEL_LINK}
        welcome_text = (
            f"Салом, Оғои Император! 👑\n\n"
            f"Шумо соҳиби асосии бот ҳастед. Маълумоти шумо ба таври худкор сабт шуд:\n"
            f"👤 Никнейми шумо: `{MY_MAIN_ADMIN}`\n"
            f"📢 Канали шумо: {MY_CHANNEL_LINK}\n\n"
            f"Идоракунии бот ва гурӯҳҳо аз менюи зерин 👇"
        )
    else:
        welcome_text = (
            f"Салом, {message.from_user.first_name}! 🤖\n\n"
            f"Ман боти муҳофизи гурӯҳ ва ёрдамчии админ ҳастам.\n"
            f"Барои бақайдгирӣ ва ҳамчун Админ сабт шудан тугмаи зеринро пахш кунед."
        )

    markup = get_start_keyboard(bot_info.username, user_id)
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if call.data == "register_admin":
        if user_id == ADMIN_ID:
            bot.answer_callback_query(call.id, "👑 Шумо соҳиби асосӣ ҳастед, бақайдгирӣ лозим нест!", show_alert=True)
            return
            
        user_states[user_id] = {"step": "waiting_for_username"}
        
        step_markup = get_step_keyboard("waiting_for_username")
        bot.send_message(
            chat_id, 
            "Лутфан, никнейми худро нависед.\n"
            "Мисол: `@username` (Ҳатман бо `@` сар шавад):",
            reply_markup=step_markup
        )
        bot.answer_callback_query(call.id)
        
    elif call.data == "my_info":
        if user_id in registered_admins:
            data = registered_admins[user_id]
            channel_link = data.get('channel', 'Сабт нашудааст')
            bot.send_message(
                chat_id,
                f"📊 **Маълумоти шумо дар база:**\n\n"
                f"👤 Никнейми шумо: `{data['username']}`\n"
                f"📢 Канали шумо: {channel_link}\n\n"
                f"Маълумоти шумо тасдиқ шудааст ва шумо ҳуқуқи админ доред. ✅"
            )
        else:
            bot.send_message(chat_id, "❌ Шумо то ҳол бақайдгирии тасдиқшуда надоред. Тугмаи '📝 Бақайдгирии Админ'-ро пахш кунед.")
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
        
        # Клавиатураи бекоркунӣ барои созанда
        cancel_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        cancel_markup.add(types.KeyboardButton("❌ Бекор кардан"))
        
        bot.send_message(
            chat_id, 
            f"✍️ Навиштани паём ба гурӯҳи **\"{group_name}\"**:\n\n"
            f"Паёми худро фиристед. Барои бекор кардан тугмаи зеринро истифода баред 👇",
            reply_markup=cancel_markup
        )
        bot.answer_callback_query(call.id)


# ================= СИСТЕМАИ ТАФТИШИ АДМИНКА БО ТУГМАИ БА ҚАФО =================

@bot.message_handler(func=lambda message: message.from_user.id in user_states, chat_types=['private'])
def registration_and_broadcast_steps(message):
    user_id = message.from_user.id
    state_data = user_states[user_id]
    step = state_data.get("step")
    bot_info = bot.get_me()
    text_input = message.text.strip() if message.text else ""
    
    # 1. АМАЛИ БЕКОР КАРДАН
    if text_input == "❌ Бекор кардан" or text_input == "/cancel":
        del user_states[user_id]
        remove_markup = types.ReplyKeyboardRemove()
        bot.send_message(user_id, "❌ Амал бекор карда шуд.", reply_markup=remove_markup)
        
        # Бозгашт ба менюи асосӣ
        markup = get_start_keyboard(bot_info.username, user_id)
        bot.send_message(user_id, "Менюи асосӣ:", reply_markup=markup)
        return

    # 2. АМАЛИ БА АҚИБ (БАРГАШТАН БА ҚАДАМИ ПЕШТАРА)
    if text_input == "⬅️ Ба ақиб":
        if step == "waiting_for_channel":
            # Бозгашт ба Қадами 1 (Интизори Никнейм)
            user_states[user_id]["step"] = "waiting_for_username"
            step_markup = get_step_keyboard("waiting_for_username")
            bot.send_message(
                user_id, 
                "⬅️ Ба қадами пештара баргаштед.\n\nЛутфан, никнейми худро аз нав нависед (бо `@` оғоз шавад):",
                reply_markup=step_markup
            )
            
        elif step == "waiting_for_group_verification":
            # Бозгашт ба Қадами 2 (Интизори Канал)
            user_states[user_id]["step"] = "waiting_for_channel"
            step_markup = get_step_keyboard("waiting_for_channel")
            bot.send_message(
                user_id, 
                "⬅️ Ба қадами пештара баргаштед.\n\nЛутфан, линки канали худро аз нав фиристед (бо `https://` ё `t.me/` сар шавад):",
                reply_markup=step_markup
            )
        return

    # 3. ҚАДАМҲОИ БАҚАЙДГИРӢ

    # Қадами 1: Никнейм
    if step == "waiting_for_username":
        if not text_input.startswith("@"):
            bot.send_message(user_id, "❌ Никнейм бояд бо аломати `@` оғоз шавад! Масалан: `@ALI_UC_SHOPP` \n\nЛутфан аз нав нависед:")
            return
            
        user_states[user_id]["username"] = text_input
        user_states[user_id]["step"] = "waiting_for_channel"
        
        step_markup = get_step_keyboard("waiting_for_channel")
        bot.send_message(
            user_id, 
            "Аъло! Акнун линки канали худро фиристед:\nМисол: `https://t.me/ALI_US_SHOPP`:",
            reply_markup=step_markup
        )
        
    # Қадами 2: Канал
    elif step == "waiting_for_channel":
        if not (text_input.startswith("http://") or text_input.startswith("https://") or text_input.startswith("t.me/")):
            bot.send_message(user_id, "❌ Линки нодуруст! Линк бояд бо `https://` ё `t.me/` сар шавад.\n\nЛутфан аз нав фиристед:")
            return
            
        user_states[user_id]["channel"] = text_input
        user_states[user_id]["step"] = "waiting_for_group_verification"
        
        group_list_text = ""
        if active_groups:
            group_list_text = "\n\n📋 **Гурӯҳҳои дастрас, ки бот дар онҳост:**\n"
            for g_id, g_name in active_groups.items():
                group_list_text += f"• `{g_id}` (Гурӯҳи: *{g_name}*)\n"
        
        step_markup = get_step_keyboard("waiting_for_group_verification")
        bot.send_message(
            user_id, 
            f"⚙️ **Қадами охирин - Тафтиши ҳуқуқи Админ:**\n\n"
            f"Барои он ки бот тасдиқ кунад, ки шумо дар ҳақиқат админ ҳастед, лутфан **ID-и гурӯҳи худро** (ки бот дар он ҷо ҳаст) нависед.\n"
            f"Мисол: `-100123456789` ё линки оммавии он гурӯҳ.{group_list_text}\n"
            f"✍️ ID ё линки гурӯҳро нависед:",
            reply_markup=step_markup,
            parse_mode="Markdown"
        )

    # Қадами 3: Тафтиши ҳуқуқи админ дар гурӯҳ
    elif step == "waiting_for_group_verification":
        group_identifier = text_input
        target_chat_id = None

        if group_identifier.startswith("-"):
            try:
                target_chat_id = int(group_identifier)
            except ValueError:
                pass
        else:
            target_chat_id = group_identifier

        if not target_chat_id:
            bot.send_message(user_id, "❌ ID ё линки гурӯҳ нодуруст аст. Лутфан дуруст нависед:")
            return

        try:
            member_status = bot.get_chat_member(target_chat_id, user_id)
            
            if member_status.status in ['administrator', 'creator']:
                registered_admins[user_id] = {
                    "username": state_data["username"],
                    "channel": state_data["channel"]
                }
                
                try:
                    chat_info = bot.get_chat(target_chat_id)
                    active_groups[chat_info.id] = chat_info.title
                except Exception:
                    pass
                
                del user_states[user_id]
                
                # Тоза кардани тугмаҳои клавиатураи оддӣ
                remove_markup = types.ReplyKeyboardRemove()
                bot.send_message(user_id, "🔄 Маълумот сабт шуд...", reply_markup=remove_markup)
                
                markup = get_start_keyboard(bot_info.username, user_id)
                bot.send_message(
                    user_id, 
                    f"🎉 **Тасдиқ шуд!**\n\n"
                    f"Бот муайян кард, ки шумо дар ин гурӯҳ ҳуқуқи Админ доред. ✅\n"
                    f"Маълумоти шумо ба база илова шуд ва акнун ҳангоми навиштани калимаҳои калидӣ дар гурӯҳҳо, бот ба таври худкор никнейм ва канали шуморо нишон медиҳад!",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(
                    user_id, 
                    "❌ **Рад карда шуд!**\n"
                    "Шумо дар гурӯҳи нишондодашуда ҳуқуқи Администраторро надоред. Бот танҳо админҳои ҳақиқиро сабт мекунад. \n\n"
                    "Агар хатогӣ бошад, лутфан ID-и гурӯҳи дурустро нависед ё аз нав кӯшиш кунед:"
                )
        except Exception as e:
            bot.send_message(
                user_id, 
                f"❌ **Хатогии тафтиш!**\n"
                f"Бот ба ин гурӯҳ дастрасӣ надорад ё бот дар он гурӯҳ илова нашудааст.\n\n"
                f"⚠️ **Чӣ бояд кард?**\n"
                f"1. Аввал ботро ба гурӯҳи худ илова кунед ва ҳуқуқи Админ диҳед.\n"
                f"2. Сипас ID-и дурусти гурӯҳро ба ман фиристед:\n\n"
                f"Хатогии системавӣ: `{e}`",
                parse_mode="Markdown"
            )

    # Барои созанда (паём ба гурӯҳ)
    elif step == "waiting_for_broadcast_text":
        target_id = state_data["target_group_id"]
        group_name = state_data["target_group_name"]
        
        try:
            if message.content_type == 'text':
                bot.send_message(target_id, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(target_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(target_id, message.video.file_id, caption=message.caption)
            else:
                bot.copy_message(target_id, user_id, message.message_id)
                
            remove_markup = types.ReplyKeyboardRemove()
            bot.send_message(user_id, f"✅ Паёми шумо ба гурӯҳи **\"{group_name}\"** расонида шуд!", reply_markup=remove_markup)
            
            del user_states[user_id]
            
            # Намоиши менюи асосӣ пас аз паём
            markup = get_start_keyboard(bot_info.username, user_id)
            bot.send_message(user_id, "Менюи асосӣ:", reply_markup=markup)
            
        except Exception as e:
            bot.send_message(user_id, f"❌ Хатогӣ ҳангоми фиристодани паём: {e}")


# ==============================================================================


@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def filter_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Никнейм надорад"

    if message.chat.type in ['group', 'supergroup']:
        if chat_id not in active_groups:
            active_groups[chat_id] = message.chat.title

    admin_status = is_admin_in_this_chat(chat_id, message)

 # 1. АГАР НАВИСАНДА АДМИН БОШАД:
    if admin_status:
        if message.content_type == 'text':
            detected_bad_word = find_bad_word(message.text)
            if detected_bad_word:
                send_reaction(chat_id, message.message_id, "😱")
                return

        if message.content_type == 'text':
            text = message.text.lower()
            answers = get_answers(chat_id)
            for word, answer in answers.items():
                if word in text:
                    if 'салом' in word or 'salom' in word:
                        send_reaction(chat_id, message.message_id, random.choice(["❤️", "🔥", "👍"]))
                    elif 'рахмат' in word:
                        send_reaction(chat_id, message.message_id, "🤝")
                    
                    bot.reply_to(message, answer)
                    break
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

    # В) САНҶИШИ ДАШНОМҲО:
    if message.content_type == 'text':
        detected_bad_word = find_bad_word(message.text)
        if detected_bad_word:
            try:
                bot.delete_message(chat_id, message.message_id)
                
                group_title = message.chat.title if message.chat.title else "Гурӯҳи хусусӣ"
                report_message = (
                    f"🚨 **Дашном ошкор шуд!**\n\n"
                    f"👥 **Гурӯҳ:** {group_title} (ID: `{chat_id}`)\n"
                    f"👤 **Нависанда:** {user_name} ({username}) (ID: `{user_id}`)\n"
                    f"🤬 **Калимаи ёфтшуда:** `{detected_bad_word}`\n"
                    f"📝 **Паёми пурра:**\n_\"{message.text}\"_"
                )
                
                try:
                    bot.send_message(ADMIN_ID, report_message, parse_mode="Markdown")
                except Exception as send_err:
                    print(f"Хатогӣ ҳангоми фиристодани отчёт ба админ: {send_err}")

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

    # Г) ҶАВОБ БА КАЛИМАҲОИ КАЛИДӢ:
    if message.content_type == 'text':
        text = message.text.lower()
        answers = get_answers(chat_id)
        
        for word, answer in answers.items():
            if word in text:
                if 'салом' in word or 'salom' in word:
                    send_reaction(chat_id, message.message_id, random.choice(["❤️", "🔥", "👍"]))
                elif 'рахмат' in word:
                    send_reaction(chat_id, message.message_id, "🤝")
                elif 'юс' in word or 'uc' in word or 'нарх' in word:
                    send_reaction(chat_id, message.message_id, "⚡")
                
                bot.reply_to(message, answer)
                return

        if random.random() < 0.10:
            random_emoji = random.choice(["👍", "❤️", "🔥", "🥰", "🫶", "😂", "🤯", "🩵", "🎉", "😎"])
            send_reaction(chat_id, message.message_id, random_emoji)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    
    print("🤖 Бот бо муваффақият оғоз ёфт...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
