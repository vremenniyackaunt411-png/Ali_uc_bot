import os
import time
import random
from threading import Thread
from flask import Flask
import telebot
from telebot import types

TOKEN = '8805476577:AAHlJF4UlB-n4bFRpMqKgj7WKqsXQp-LQqA'
# ИД-и телеграми шумо (Супер-Админ)
ADMIN_ID = 6871575684 

# Никнейм ва линки доимии шумо барои мағозаи худатон
MY_MAIN_ADMIN = "@ALI_UC_SHOPP" #
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

# Базаи огоҳиҳои корбарон
user_link_warnings = {}     
user_badword_warnings = {}  

# БАЗАИ БАҚАЙДГИРИИ АДМИНҲО
registered_admins = {
    ADMIN_ID: {"username": MY_MAIN_ADMIN}
}

# Махзани гурӯҳҳо (барои сабт кардани он гурӯҳҳое, ки бот дар онҳост)
# Дар ин ҷо сохтори база: {chat_id: "Номи гурӯҳ"} хоҳад буд
active_groups = {}

# Ҳолатҳои корбар барои бақайдгирӣ ва фиристодани паём ба гурӯҳ
user_states = {}

# Калимаҳои манъшуда
BAD_WORDS = [
    'кунте', 'кунти', 'гандон', 'сука', 'кс',
    'далбаёб',  'кер', 'гом', 'ks', 'сина'
]

# Функсия барои гузоштани реаксия ба паём
def send_reaction(chat_id, message_id, emoji):
    try:
        bot.set_message_reaction(
            chat_id=chat_id,
            message_id=message_id,
            reaction=[telebot.types.ReactionTypeEmoji(emoji)]
        )
    except Exception as e:
        print(f"Хатогӣ ҳангоми гузоштани реаксия: {e}")

# Функсия барои санҷидани админ будани нависанда дар гурӯҳ
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

# Функсияи муайянкунии админ
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
                return f"{adm_data['username']} (Канал: {adm_data['channel']})"
    except Exception as e:
        print(f"Хатогӣ ҳангоми гирифтани админҳои гурӯҳ: {e}")

    return f"{MY_MAIN_ADMIN} (Канал: {MY_CHANNEL_LINK})"

# Саволҳо ва ҷавобҳо
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
        'admin': f' {admin} <--- админ.',
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


# Функсияи умумӣ барои сохтани тугмаҳо (Регистратсия дар боло, Илова ба гурӯҳ дар поён)
def get_start_keyboard(bot_username, user_id):
    markup = types.InlineKeyboardMarkup()
    
    # Тугмаҳои бақайдгирӣ ва маълумот (Дар боло)
    btn_register = types.InlineKeyboardButton("📝 Бақайдгирии Админ", callback_data="register_admin")
    btn_my_info = types.InlineKeyboardButton("ℹ️ Маълумоти ман", callback_data="my_info")
    markup.row(btn_register, btn_my_info)
    
    # ТАНҲО БАРОИ СОЗАНДАИ БОТ (ADMIN_ID) - Тугмаи гурӯҳҳои ман
    if user_id == ADMIN_ID:
        btn_owner_groups = types.InlineKeyboardButton("⚙️ Гурӯҳҳои ман (Танҳо Созанда)", callback_data="owner_groups")
        markup.row(btn_owner_groups)
    
    # Тугмаи илова кардани бот ба гурӯҳ (Дар поён)
    add_to_group_url = f"https://t.me/{bot_username}?startgroup=true"
    btn_add_group = types.InlineKeyboardButton("➕ Илова кардан ба гурӯҳ (Добавить в группу)", url=add_to_group_url)
    markup.row(btn_add_group)
    
    return markup


# ================= КУШОДАНИ ЧАТИ ШАХСӢ БО БОТ (/start ва бақайдгирӣ) =================

@bot.message_handler(commands=['start'], chat_types=['private'])
def start_private(message):
    user_id = message.from_user.id
    bot_info = bot.get_me()
    
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
            f"Шумо метавонед маро ба гурӯҳи худ илова кунед ва ҳамчун Админ худро сабт кунед."
        )

    markup = get_start_keyboard(bot_info.username, user_id)
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode="Markdown")


# Коркарди пахши тугмаҳои Inline
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    # Пахши тугмаи бақайдгирӣ
    if call.data == "register_admin":
        user_states[user_id] = {"step": "waiting_for_username"}
        bot.send_message(
            chat_id, 
            "Лутфан, никнейми худро нависед.\n"
            "Мисол: `@ALI_UC_SHOPP` (Ҳатман бо `@` сар шавад):"
        )
        bot.answer_callback_query(call.id)
        
    # Пахши тугмаи маълумоти ман
    elif call.data == "my_info":
        if user_id in registered_admins:
            data = registered_admins[user_id]
            bot.send_message(
                chat_id,
                f"📊 **Маълумоти шумо дар база:**\n\n"
                f"👤 Никнейми шумо: `{data['username']}`\n"
                f"📢 Канали шумо: {data['channel']}\n\n"
                f"Агар хоҳед маълумотро иваз кунед, тугмаи '📝 Бақайдгирии Админ'-ро аз нав пахш кунед."
            )
        else:
            bot.send_message(chat_id, "❌ Шумо то ҳол бақайдгирӣ накардаед. Тугмаи '📝 Бақайдгирии Админ'-ро пахш кунед.")
        bot.answer_callback_query(call.id)

    # ТАНҲО БАРОИ СОЗАНДА (Рӯйхати гурӯҳҳо)
    elif call.data == "owner_groups":
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Ин тугма танҳо барои соҳиби бот аст!", show_alert=True)
            return
        
        if not active_groups:
            bot.send_message(chat_id, "ℹ️ Бот то ҳол ба ягон гурӯҳ илова нашудааст ё ягон паём дар гурӯҳ навишта нашудааст.")
            bot.answer_callback_query(call.id)
            return
        
        # Сохтани тугмаҳо барои ҳар як гурӯҳ
        markup = types.InlineKeyboardMarkup()
        for gr_id, gr_name in active_groups.items():
            # Тугма бо номи гурӯҳ ва фиристодани callback бо ИД-и гурӯҳ
            btn = types.InlineKeyboardButton(f"💬 {gr_name}", callback_data=f"sendto_{gr_id}")
            markup.add(btn)
            
        bot.send_message(chat_id, "👥 **Рӯйхати гурӯҳҳое, ки бот дар онҳост:**\n\nГурӯҳеро, ки мехоҳед ба он аз номи бот паём нависед, интихоб кунед:", reply_markup=markup, parse_mode="Markdown")
        bot.answer_callback_query(call.id)

    # Вақте созанда яке аз гурӯҳҳоро барои навиштан интихоб мекунад
    elif call.data.startswith("sendto_"):
        if user_id != ADMIN_ID:
            bot.answer_callback_query(call.id)
            return
            
        target_group_id = int(call.data.split("_")[1])
        group_name = active_groups.get(target_group_id, "Гурӯҳи номаълум")
        
        # Сабти ҳолати корбар барои интизори паём
        user_states[user_id] = {
            "step": "waiting_for_broadcast_text",
            "target_group_id": target_group_id,
            "target_group_name": group_name
        }
        
        bot.send_message(
            chat_id, 
            f"✍️ Навиштани паём ба гурӯҳи **\"{group_name}\"**:\n\n"
            f"Ҳоло матни худро навишта фиристед ва бот онро ба ҳамон гурӯҳ равон мекунад. "
            f"Барои бекор кардан `/cancel` нависед."
        )
        bot.answer_callback_query(call.id)


# Қадамҳои бақайдгирӣ ва фиристодани паём ба гурӯҳ
@bot.message_handler(func=lambda message: message.from_user.id in user_states, chat_types=['private'])
def registration_and_broadcast_steps(message):
    user_id = message.from_user.id
    state_data = user_states[user_id]
    step = state_data.get("step")
    bot_info = bot.get_me()
    
    # Фармони бекоркунӣ
    if message.text and message.text.strip() == "/cancel":
        del user_states[user_id]
        bot.send_message(user_id, "❌ Амал бекор карда шуд.")
        return

    # Қадами 1: Никнейм
    if step == "waiting_for_username":
        username = message.text.strip()
        if not username.startswith("@"):
            bot.send_message(user_id, "❌ Никнейм бояд ҳатман бо аломати `@` оғоз шавад! Масалан: `@ALI_UC_SHOPP` \n\nЛутфан аз нав нависед:")
            return
            
        registered_admins[user_id] = {"username": username}
        user_states[user_id]["step"] = "waiting_for_channel"
        bot.send_message(user_id, "Аъло! Акнун линки канали худро фиристед.\nМисол: `https://t.me/ALI_US_SHOPP`:")
        
    # Қадами 2: Канал
    elif step == "waiting_for_channel":
        channel = message.text.strip()
        if not (channel.startswith("http://") or channel.startswith("https://") or channel.startswith("t.me/")):
            bot.send_message(user_id, "❌ Линки нодуруст! Линк бояд бо `https://` ё `t.me/` сар шавад.\n\nЛутфан линки дурустро фиристед:")
            return
            
        registered_admins[user_id]["channel"] = channel
        del user_states[user_id] # Тоза кардани ҳолат
        
        markup = get_start_keyboard(bot_info.username, user_id)
        
        bot.send_message(
            user_id, 
            "🎉 Табрик! Маълумоти шумо бо муваффақият сабт шуд.\n"
            "Акнун ботро ба гурӯҳи худ илова кунед ва ҳуқуқи Админ (мудирият) диҳед.\n"
            "Ҳангоми навиштани калимаҳои калидӣ, бот худкор маълумоти шуморо нишон медиҳад!",
            reply_markup=markup
        )

    # Махсус барои Созанда: Қабули матн ва фиристодан ба гурӯҳ аз номи бот
    elif step == "waiting_for_broadcast_text":
        target_id = state_data["target_group_id"]
        group_name = state_data["target_group_name"]
        
        try:
            # Ирсоли паём ба гурӯҳи интихобшуда (ҳаргуна паём: матн, акс ва ғ.)
            if message.content_type == 'text':
                bot.send_message(target_id, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(target_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(target_id, message.video.file_id, caption=message.caption)
            else:
                bot.copy_message(target_id, user_id, message.message_id)
                
            bot.send_message(user_id, f"✅ Паёми шумо ба гурӯҳи **\"{group_name}\"** бо муваффақият расонида шуд!", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(user_id, f"❌ Хатогӣ ҳангоми фиристодани паём ба гурӯҳ: {e}")
            
        del user_states[user_id] # Баъди иҷро ҳолатро тоза мекунем


# ==============================================================================


# Коркарди паёмҳо дар ГУРӮҲҲО
@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'voice'])
def filter_messages(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "Никнейм надорад"

    # САБТ КАРДАНИ ГУРӮҲ: Вақте дар гурӯҳ ягон паём навишта мешавад, бот он гурӯҳро ба рӯйхати фаъол илова мекунад
    if message.chat.type in ['group', 'supergroup']:
        if chat_id not in active_groups:
            active_groups[chat_id] = message.chat.title

    admin_status = is_admin_in_this_chat(chat_id, message)

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
                restrict_user(chat_id, user_id, 86400) # 24 соат блок
                bot.send_message(
                    chat_id, 
                    f"🚫 Корбар {user_name} қоидаро 3 бор шикаст ва барои спам ба муҳлати 24 соат блок шуд! Пас аз 24 соат худкор кушода мешавад."
                )
                user_link_warnings[user_id] = 0
        except Exception as e:
            print(f"Хатогӣ дар антиспам: {e}")
        return

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
                    restrict_user(chat_id, user_id, 28800) # 8 соат блок
                    bot.send_message(
                        chat_id,
                        f"🚫 Корбар {user_name} \n барои истифодаи суханхои кабех ё дашном ба муҳлати 8 соат блок шуд!"
                    )
                    user_badword_warnings[user_id] = 0
            except Exception as e:
                print(f"Хатогӣ дар тозакунии калимаҳо: {e}")
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
                elif 'юс' in word or 'uc' in word or 'нарх' in word:
                    send_reaction(chat_id, message.message_id, "⚡")
                
                bot.reply_to(message, answer)
                return

        if random.random() < 0.10:
            random_emoji = random.choice(["👍", "❤️", "🔥", "🥰", "🫶", "😂", "🤯", "🩵", "🎉", "😎"])
            send_reaction(chat_id, message.message_id, random_emoji)

# Ба кор андохтани сервер ва бот
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.start()
    
    print("🤖 Бот бо тугмаҳои Inline ва функсияи созанда омода аст...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
