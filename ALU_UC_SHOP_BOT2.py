import os
import time
import telebot
from telebot import types
import sqlite3
import threading
import html
from datetime import datetime
from flask import Flask


# ============================================================
# НАСТРОЙКА
# ============================================================

BOT_TOKEN = "8660164143:AAEt1TXap-zqppH819CdWX2P3vwCFT99Hfs"

ADMIN_ID = 6871575684

# Канали отзывҳо
REVIEWS_CHANNEL = "@otziv_ALI_US_SHOPP"

# Username-и админ барои тугмаи алоқа
ADMIN_USERNAME = "@ALI_UC_SHOP"

DB_NAME = "ali_uc_shop.db"

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

db_lock = threading.Lock()

user_states = {}
admin_states = {}

# Барои нигоҳ доштани message_id-и менюи харид
shop_messages = {}


# ============================================================
# WEB SERVER FOR RENDER + UPTIMEROBOT
# ============================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "ALI UC SHOP BOT is running!", 200


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# ============================================================
# НАРХНОМА
# ============================================================

DEFAULT_PRICES = {
    60: 10,
    325: 48,
    660: 92,
    1800: 240,
    3850: 450,
    8100: 870
}


# ============================================================
# РЕКВИЗИТҲО
# ============================================================

PAYMENT_DETAILS = """
<b>РЕКВИЗИТ КАРТА 🎫👇</b>

👉 <b>Бонки Эсхата</b>
<code>+992 555050093</code>
Ба номи Орифҷон Г. М.


👉 <b>ДУШАНБЕ СИТИ</b>
<code>+992 555050093</code>
Ба номи Орифҷонҷон Г. М.


👉 <b>АЛИФ БАНК</b>
<code>+992 555050093</code>
Ба номи Орифҷон Г. М.
"""


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    with db_lock:

        conn = get_db()
        cur = conn.cursor()

        # USERS
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            joined_at TEXT
        )
        """)

        # PRICES
        cur.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            uc INTEGER PRIMARY KEY,
            price INTEGER NOT NULL
        )
        """)

        # ORDERS
        cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            first_name TEXT,
            username TEXT,
            pubg_id TEXT,
            uc INTEGER,
            amount INTEGER,
            bonus_earned INTEGER DEFAULT 0,
            receipt_file_id TEXT,
            receipt_type TEXT,
            status TEXT DEFAULT 'pending',
            reject_reason TEXT,
            created_at TEXT,
            completed_at TEXT
        )
        """)

        # Илова кардани bonus_earned ба базаи кӯҳна
        try:
            cur.execute(
                "ALTER TABLE orders ADD COLUMN bonus_earned INTEGER DEFAULT 0"
            )
        except sqlite3.OperationalError:
            pass

        # REVIEWS
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            user_id INTEGER,
            first_name TEXT,
            username TEXT,
            uc INTEGER,
            amount INTEGER,
            text TEXT,
            status TEXT DEFAULT 'pending',
            reject_reason TEXT,
            created_at TEXT
        )
        """)

        # Нархномаи аввал
        cur.execute(
            "SELECT COUNT(*) FROM prices"
        )

        if cur.fetchone()[0] == 0:

            for uc, price in DEFAULT_PRICES.items():

                cur.execute(
                    """
                    INSERT INTO prices
                    (uc, price)
                    VALUES (?, ?)
                    """,
                    (uc, price)
                )

        conn.commit()
        conn.close()


init_db()

# ============================================================
# BONUS SYSTEM
# ============================================================

with db_lock:
    conn = get_db()

    # Илова кардани bonus ба users
    try:
        conn.execute(
            "ALTER TABLE users ADD COLUMN bonus INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    # Ҷадвали танзими бонус
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bonus_settings (
            uc INTEGER PRIMARY KEY,
            bonus INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Қоидаҳои аввалияи бонус
    bonus_rules = [
        (60, 1),
        (325, 2),
        (660, 3),
        (1800, 4),
        (3850, 5),
        (8100, 6)
    ]

    for uc_value, bonus_value in bonus_rules:
        conn.execute("""
            INSERT OR IGNORE INTO bonus_settings
            (uc, bonus)
            VALUES (?, ?)
        """, (uc_value, bonus_value))

    conn.commit()
    conn.close()
    
# Илова кардани сутунҳо барои файли отзыв
with db_lock:
    conn = get_db()

    try:
        conn.execute(
            "ALTER TABLE reviews ADD COLUMN review_file_id TEXT"
        )
    except sqlite3.OperationalError:
        pass

    try:
        conn.execute(
            "ALTER TABLE reviews ADD COLUMN review_file_type TEXT"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()
    

# ============================================================
# BONUS USED IN ORDERS
# ============================================================

with db_lock:
    conn = get_db()

    try:
        conn.execute(
            "ALTER TABLE orders ADD COLUMN bonus_used INTEGER DEFAULT 0"
        )
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


# ============================================================
# USER DATABASE
# ============================================================

def add_user(user):

    with db_lock:

        conn = get_db()

        conn.execute("""
            INSERT INTO users
            (
                telegram_id,
                first_name,
                username,
                joined_at,
                bonus
            )
            VALUES (
                ?,
                ?,
                ?,
                ?,
                0
            )
            ON CONFLICT(telegram_id)
            DO UPDATE SET
                first_name = excluded.first_name,
                username = excluded.username
        """, (
            user.id,
            user.first_name or "",
            user.username or "",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

        conn.commit()
        conn.close()


# ============================================================
# PRICE HELPERS
# ============================================================

def get_prices():

    with db_lock:

        conn = get_db()

        rows = conn.execute(
            """
            SELECT uc, price
            FROM prices
            ORDER BY uc ASC
            """
        ).fetchall()

        conn.close()

    return [
        (row["uc"], row["price"])
        for row in rows
    ]


def get_price(uc):

    with db_lock:

        conn = get_db()

        row = conn.execute(
            """
            SELECT price
            FROM prices
            WHERE uc=?
            """,
            (uc,)
        ).fetchone()

        conn.close()

    if row:
        return row["price"]

    return None


# ============================================================
# ORDER HELPERS
# ============================================================

def get_order(order_id):

    with db_lock:

        conn = get_db()

        row = conn.execute(
            """
            SELECT *
            FROM orders
            WHERE id=?
            """,
            (order_id,)
        ).fetchone()

        conn.close()

    return row


def status_text(status):

    return {
        "pending": "🟡 Дар интизори санҷиш",
        "completed": "🟢 Иҷро шуд",
        "rejected": "🔴 Рад шуд"
    }.get(
        status,
        status
    )


def user_name(row):

    return html.escape(
        row["first_name"] or "Номаълум"
    )


def username_text(row):

    if row["username"]:

        return "@" + html.escape(
            row["username"]
        )

    return "Нест"


# ============================================================
# REVIEW HELPERS
# ============================================================

def get_review(review_id):

    with db_lock:

        conn = get_db()

        row = conn.execute(
            """
            SELECT *
            FROM reviews
            WHERE id=?
            """,
            (review_id,)
        ).fetchone()

        conn.close()

    return row


# ============================================================
# MAIN USER MENU
# ============================================================

def main_menu():

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.row(
        "🛒 Харидани UC"
    )

    kb.row(
        "📦 Заказҳои ман"
    )

    kb.row(
        "⭐ Отзывы"
    )

    kb.row(
    "🎁 Бонусҳои ман"
    )

    kb.row(
        "👨‍💻 Алоқа бо админ"
    )

    return kb


def admin_menu():

    # ========================================================
    # ҲИСОБИ ЗАКАЗҲО ВА ОТЗЫВҲО
    # ========================================================

    with db_lock:
            conn = get_db()

    total_orders = conn.execute("""
        SELECT COUNT(*)
        FROM orders
    """).fetchone()[0]

    total_reviews = conn.execute("""
        SELECT COUNT(*)
        FROM reviews
    """).fetchone()[0]

    total_users = conn.execute("""
        SELECT COUNT(*)
        FROM users
    """).fetchone()[0]

    conn.close()

    # ========================================================
    # МЕНЮИ АДМИН
    # ========================================================

    kb = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    kb.row(
        f"📦 Заказҳо ({total_orders})"
    )

    kb.row(
        f"⭐ Отзывы ({total_reviews})"
    )

    kb.row(
        f"👥 Корбарони фаъол ({total_users})"
    )

    kb.row(
        "💰 Танзими UC"
    )

    kb.row(
        "🎁 Танзими бонус"
    )

    return kb


# ============================================================
# USER INLINE BACK/HOME
# ============================================================

def user_back_home():

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    return kb


# ============================================================
# ADMIN BACK/HOME
# ============================================================

def admin_back_home():

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    return kb


# ============================================================
# START
# ============================================================

@bot.message_handler(
    commands=["start"]
)
def start(message):

    add_user(
        message.from_user
    )

    user_states.pop(
        message.from_user.id,
        None
    )

    admin_states.pop(
        message.from_user.id,
        None
    )

    if message.from_user.id == ADMIN_ID:

        bot.send_message(
        message.chat.id,

        f"Салом, <b>{message.from_user.first_name}</b>! 👋\n\n"
        "👨‍💻 Хуш омадед ба панели идоракунии <b>ALI UC SHOP</b>!\n\n"
        "⚙️ Аз менюи поён бахши лозимаро интихоб кунед:",

        reply_markup=admin_menu()
    )

    else:

        bot.send_message(
            message.chat.id,

            f"Салом, <b>{message.from_user.first_name}</b>! 👋\n\n"
            "🛍️ Ба <b>ALI UC SHOP</b> хуш омадед!\n\n"
            "✨ Яке аз хизматрасониҳои моро интихоб кунед:",

            reply_markup=main_menu()
        )


# ============================================================
# USER BONUS
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text == "🎁 Бонусҳои ман"
)
def my_bonus(message):

    user_id = message.from_user.id

    # Бонуси ҳозираи корбар
    with db_lock:

        conn = get_db()

        user_row = conn.execute(
            """
            SELECT bonus
            FROM users
            WHERE telegram_id=?
            """,
            (user_id,)
        ).fetchone()

        # Қоидаҳои бонусро АЗ БАЗА мехонем
        bonus_rows = conn.execute(
            """
            SELECT uc, bonus
            FROM bonus_settings
            ORDER BY uc ASC
            """
        ).fetchall()

        conn.close()

    # Бонусҳои ҷамъшудаи корбар
    if user_row:
        total_bonus = user_row["bonus"] or 0
    else:
        total_bonus = 0

    # Матни асосӣ
    text = (
        "🎁 <b>БОНУСҲОИ МАН</b>\n\n"
        f"💰 <b>Бонусҳои шумо:</b> {total_bonus}\n"
        f"💵 <b>Арзиш:</b> {total_bonus} сомонӣ\n\n"
        "📋 <b>ҚОИДАҲОИ БОНУС:</b>\n\n"
    )

    # Қоидаҳоро аз bonus_settings нишон медиҳем
    if bonus_rows:

        for row in bonus_rows:

            text += (
                f"💎 <b>{row['uc']} UC</b> "
                f"→ 🎁 <b>{row['bonus']} бонус</b>\n"
            )

    else:

        text += "❌ Қоидаҳои бонус ҳоло нестанд.\n"

    text += (
        "\n━━━━━━━━━━━━━━\n"
        "💵 <b>1 бонус = 1 сомонӣ</b>"
    )

        # ========================================================
    # ТУГМАҲОИ БОНУС
    # ========================================================

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🎁 Истифодаи бонус",
            callback_data="use_bonus"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb
    )
    
# ============================================================
# SHOP KEYBOARD
# ============================================================

def shop_keyboard():

    prices = get_prices()

    kb = types.InlineKeyboardMarkup()

    row = []

    for uc, price in prices:

        row.append(
            types.InlineKeyboardButton(
                f"{uc} UC — {price} с.",
                callback_data=f"adduc:{uc}"
            )
        )

        if len(row) == 2:

            kb.row(*row)

            row = []

    if row:

        kb.row(*row)

    kb.row(
        types.InlineKeyboardButton(
            "🗑 Очистить",
            callback_data="clear_cart"
        ),
        types.InlineKeyboardButton(
            "🛒 Харидан",
            callback_data="buy"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    return kb


# ============================================================
# USE BONUS
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "use_bonus"
)
def use_bonus(call):

    user_id = call.from_user.id

    with db_lock:
        conn = get_db()

        # Бонуси ҳозираи корбар
        user_row = conn.execute(
            """
            SELECT bonus
            FROM users
            WHERE telegram_id=?
            """,
            (user_id,)
        ).fetchone()

        # Нархи UC барои харид бо бонус
        rows = conn.execute(
            """
            SELECT uc, price
            FROM prices
            ORDER BY uc ASC
            """
        ).fetchall()

        conn.close()

    total_bonus = (
        user_row["bonus"]
        if user_row and user_row["bonus"]
        else 0
    )

    kb = types.InlineKeyboardMarkup()

    for row in rows:

        uc = row["uc"]
        required_bonus = row["price"]

        kb.add(
            types.InlineKeyboardButton(
                f"💎 {uc} UC — 🎁 {required_bonus} бонус",
                callback_data=f"use_bonus_uc:{uc}"
            )
        )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="bonus_back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        user_id,

        f"🎁 <b>ХАРИДАНИ UC БО БОНУС</b>\n\n"
        f"💰 <b>Бонусҳои шумо:</b> {total_bonus}\n\n"
        "📋 <b>Пакети UC-ро интихоб кунед:</b>\n\n"
        "⚠️ Бонуси зарурӣ барои ҳар пакет "
        "дар тугма нишон дода шудааст.",

        reply_markup=kb
    )
    
# ============================================================
# SELECT UC FOR BONUS PURCHASE
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("use_bonus_uc:")
)
def use_bonus_uc(call):

    user_id = call.from_user.id

    uc = int(
        call.data.split(":")[1]
    )

    # Нарх аз prices гирифта мешавад
    price = get_price(uc)

    if price is None:

        bot.answer_callback_query(
            call.id,
            "❌ Ин UC ҳоло дастрас нест.",
            show_alert=True
        )

        return

    # Бонуси корбар
    with db_lock:

        conn = get_db()

        user_row = conn.execute(
            """
            SELECT bonus
            FROM users
            WHERE telegram_id=?
            """,
            (user_id,)
        ).fetchone()

        conn.close()

    user_bonus = (
        user_row["bonus"]
        if user_row and user_row["bonus"]
        else 0
    )

    # Бонуси лозим = нархи UC
    required_bonus = price

    # Агар бонус нарасад
    if user_bonus < required_bonus:

        bot.answer_callback_query(
            call.id,
            "❌ Бонуси шумо намерасад.",
            show_alert=True
        )

        bot.send_message(
            user_id,

            f"❌ <b>Бонус намерасад.</b>\n\n"
            f"💎 UC: <b>{uc}</b>\n"
            f"🎁 Бонуси лозим: <b>{required_bonus}</b>\n"
            f"💰 Бонуси шумо: <b>{user_bonus}</b>\n"
            f"📉 Камбудӣ: <b>{required_bonus - user_bonus}</b> бонус"
        )

        return

    # Агар бонус расад
    bot.answer_callback_query(
        call.id
    )

    # Барои қадами навбатӣ нигоҳ медорем
    user_states[user_id] = {
        "state": "waiting_bonus_pubg_id",
        "uc": uc,
        "bonus_used": required_bonus
    }

    bot.send_message(
        user_id,

        f"✅ <b>Бонусҳо кофӣ мебошанд!</b>\n\n"
        f"💎 <b>{uc} UC</b>\n"
        f"🎁 Бонус барои пардохт: <b>{required_bonus}</b>\n"
        f"💰 Бонуси шумо: <b>{user_bonus}</b>\n\n"
        f"🎮 <b>PUBG ID-и худро равон кунед:</b>",

        reply_markup=user_back_home()
    )
    
# ============================================================
# SHOP TEXT
# ============================================================

def shop_text(user_id):

    prices = get_prices()

    text = (
        "🛒 <b>ХАРИДАНИ UC</b>\n\n"
        "<b>НАРХНОМА:</b>\n\n"
    )

    for uc, price in prices:

        text += (
            f"💎 <b>{uc} UC</b> — "
            f"{price} сомонӣ\n"
        )

    cart = user_states.get(
        user_id,
        {}
    ).get(
        "cart",
        {}
    )

    total_uc = sum(
        uc * quantity
        for uc, quantity in cart.items()
    )

    total_amount = sum(
        get_price(uc) * quantity
        for uc, quantity in cart.items()
        if get_price(uc) is not None
    )

    text += (
        "\n━━━━━━━━━━━━━━\n"
        "🧮 <b>КАЛЬКУЛЯТОР</b>\n\n"
        f"🛒 <b>UC интихобшуда:</b> "
        f"{total_uc} UC\n"
        f"💰 <b>Маблағ:</b> "
        f"{total_amount} сомонӣ"
    )

    return text


# ============================================================
# SHOW SHOP
# ============================================================

def show_shop(
    chat_id,
    user_id,
    message_id=None
):

    if user_id not in user_states:
        user_states[user_id] = {}

    if "cart" not in user_states[user_id]:
        user_states[user_id]["cart"] = {}

    cart = user_states[user_id]["cart"]

    # Ҳисобкунак
    total_uc = sum(
        uc * quantity
        for uc, quantity in cart.items()
    )

    total_amount = sum(
        (get_price(uc) or 0) * quantity
        for uc, quantity in cart.items()
    )

    # Ҳисоб кардани бонус
    total_bonus = 0

    with db_lock:
        conn = get_db()

        for uc, quantity in cart.items():

            row = conn.execute(
                """
                SELECT bonus
                FROM bonus_settings
                WHERE uc=?
                """,
                (uc,)
            ).fetchone()

            if row:
                total_bonus += row["bonus"] * quantity

        conn.close()
        
    # Матни боло
    text = "🛒 <b>ХАРИДАНИ UC</b>"

    kb = types.InlineKeyboardMarkup()

    # Тугмаҳои UC
    row = []

    for uc, price in get_prices():

        row.append(
            types.InlineKeyboardButton(
                f"{uc} UC — {price} с.",
                callback_data=f"adduc:{uc}"
            )
        )

        if len(row) == 2:
            kb.row(*row)
            row = []

    if row:
        kb.row(*row)

        # Ҳисобкунак дар поёни тугмаҳои UC
    kb.row(
        types.InlineKeyboardButton(
            f"📦 {total_uc} UC",
            callback_data="calculator"
        ),
        types.InlineKeyboardButton(
            f"💰 {total_amount} сомонӣ",
            callback_data="calculator"
        ),
        types.InlineKeyboardButton(
            f"🎁 +{total_bonus} бонус",
            callback_data="calculator"
        )
    )

    # Тугмаҳои асосӣ
    kb.row(
        types.InlineKeyboardButton(
            "🗑 Тоза кардан",
            callback_data="clear_cart"
        ),
        types.InlineKeyboardButton(
            "🛒 Харидан",
            callback_data="buy"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    # Агар ҳамин паём аллакай вуҷуд дошта бошад,
    # ТАНҲО ҲАМИН ПАЁМ тағйир дода мешавад
    if message_id:

        try:

            bot.edit_message_text(
                text,
                chat_id,
                message_id,
                reply_markup=kb
            )

            return

        except Exception as e:
            print("EDIT ERROR:", e)

    # Танҳо ҳангоми кушодани аввалини магазин
    # паёми нав сохта мешавад
    msg = bot.send_message(
        chat_id,
        text,
        reply_markup=kb
    )

    if "shop_messages" not in globals():
        globals()["shop_messages"] = {}

    shop_messages[user_id] = msg.message_id


# ============================================================
# USER BUY UC
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text == "🛒 Харидани UC"
)
def buy_uc(message):

    user_id = message.from_user.id

    user_states[user_id] = {
        "state": "shopping",
        "cart": {}
    }

    show_shop(
        message.chat.id,
        user_id
    )


# ============================================================
# ADD UC
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("adduc:")
)
def add_uc(call):

    user_id = call.from_user.id

    try:
        uc = int(call.data.split(":")[1])
    except:
        bot.answer_callback_query(call.id, "❌ Хатогӣ.")
        return

    # Сохтани сабади корбар
    if user_id not in user_states:
        user_states[user_id] = {
            "state": "shopping",
            "cart": {}
        }

    if "cart" not in user_states[user_id]:
        user_states[user_id]["cart"] = {}

    cart = user_states[user_id]["cart"]

    # Илова кардани UC
    cart[uc] = cart.get(uc, 0) + 1

    # Ҳисобкунак
    total_uc = sum(
        x * q
        for x, q in cart.items()
    )

    total_amount = sum(
        (get_price(x) or 0) * q
        for x, q in cart.items()
    )

    # Ҳисоб кардани бонус
    total_bonus = 0

    with db_lock:
        conn = get_db()

        for x, q in cart.items():
            row = conn.execute(
                """
                SELECT bonus
                FROM bonus_settings
                WHERE uc=?
                """,
                (x,)
            ).fetchone()

            if row:
                total_bonus += row["bonus"] * q

        conn.close()
        
    # Сохтани ҳамон тугмаҳо
    kb = types.InlineKeyboardMarkup()

    row = []

    for package_uc, price in get_prices():

        row.append(
            types.InlineKeyboardButton(
                f"{package_uc} UC — {price} с.",
                callback_data=f"adduc:{package_uc}"
            )
        )

        if len(row) == 2:
            kb.row(*row)
            row = []

    if row:
        kb.row(*row)

    # Калькулятор
    kb.row(
        types.InlineKeyboardButton(
            f"📦 {total_uc} UC",
            callback_data="calculator"
        ),
        types.InlineKeyboardButton(
            f"💰 {total_amount} сомонӣ",
            callback_data="calculator"
        ),
        types.InlineKeyboardButton(
            f"🎁 +{total_bonus} бонус",
            callback_data="calculator"
        )
    )

    # Тугмаҳои поён
    kb.row(
        types.InlineKeyboardButton(
            "🗑 Тоза кардан",
            callback_data="clear_cart"
        ),
        types.InlineKeyboardButton(
            "🛒 Харидан",
            callback_data="buy"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    # ТАНҲО ҲАМИН ПАЁМ тағйир меёбад
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )
    except Exception as e:
        print("UC BUTTON ERROR:", e)

    # Паёми нав НЕФИРИСТАД
    bot.answer_callback_query(call.id)
    
# ============================================================
# CLEAR CART
# ============================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "clear_cart"
)
def clear_cart(call):

    user_id = call.from_user.id

    # Сабадро пурра тоза мекунем
    if user_id not in user_states:
        user_states[user_id] = {
            "state": "shopping",
            "cart": {}
        }
    else:
        user_states[user_id]["cart"] = {}

    # Ҳисобкунак аз нав 0 мешавад
    total_uc = 0
    total_amount = 0

    # Тугмаҳои UC аз нав сохта мешаванд
    kb = shop_keyboard()

    # Паёми кӯҳна тағйир дода мешавад
    try:
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=kb
        )

    except Exception as e:
        print("CLEAR CART ERROR:", e)

    bot.answer_callback_query(
        call.id,
        "🗑 Сабад тоза шуд."
    )

# ============================================================
# START PURCHASE
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "buy"
)
def start_purchase(call):

    user_id = call.from_user.id

    data = user_states.get(
        user_id,
        {}
    )

    cart = data.get(
        "cart",
        {}
    )

    if not cart:

        bot.answer_callback_query(
            call.id,
            "Аввал UC интихоб кунед."
        )

        return

    # Ҳисоб кардани UC
    total_uc = sum(
        uc * quantity
        for uc, quantity in cart.items()
    )

    # Ҳисоб кардани маблағ
    total_amount = sum(
        get_price(uc) * quantity
        for uc, quantity in cart.items()
        if get_price(uc) is not None
    )

    # ========================================================
    # Ҳисоб кардани бонуси заказ
    # ========================================================

    total_bonus = 0

    with db_lock:

        conn = get_db()

        for uc, quantity in cart.items():

            row = conn.execute(
                """
                SELECT bonus
                FROM bonus_settings
                WHERE uc=?
                """,
                (uc,)
            ).fetchone()

            if row:

                total_bonus += (
                    row["bonus"] * quantity
                )

        conn.close()

    # ========================================================
    # Нигоҳ доштани маълумоти харид
    # ========================================================

    user_states[user_id] = {

        "state": "waiting_pubg_id",

        "cart": cart,

        "total_uc": total_uc,

        "total_amount": total_amount,

        "total_bonus": total_bonus
    }

    bot.answer_callback_query(
        call.id
    )

    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None
    )

    bot.send_message(
        call.message.chat.id,

        "🎮 <b>PUBG ID-и худро дуруст равон кунед.</b>\n\n"

        "⚠️ Пеш аз фиристодан PUBG ID-ро бодиққат санҷед.\n"
        "Агар ID нодуруст бошад, маъмурият барои "
        "иштибоҳи корбар ҷавобгар нест.\n\n"

        "🎮 <b>PUBG ID-ро равон кунед:</b>",

        reply_markup=user_back_home()
    )
# ============================================================
# RECEIVE PUBG ID
# ============================================================

@bot.message_handler(
    func=lambda m:
    user_states.get(
        m.from_user.id,
        {}
    ).get("state")
    == "waiting_pubg_id"
)
def receive_pubg_id(message):

    user_id = message.from_user.id

    if not message.text:

        bot.send_message(
            message.chat.id,
            "⚠️ PUBG ID-ро ҳамчун рақам равон кунед."
        )

        return

    pubg_id = message.text.strip()

    if not pubg_id.isdigit():

        bot.send_message(
            message.chat.id,

            "❌ PUBG ID нодуруст аст.\n\n"
            "PUBG ID бояд танҳо аз рақамҳо иборат бошад."
        )

        return

    data = user_states[user_id]

    data["pubg_id"] = pubg_id
    data["state"] = "waiting_receipt"

    bot.send_message(
        message.chat.id,

        f"🎮 <b>PUBG ID:</b> "
        f"<code>{pubg_id}</code>\n\n"

        f"💎 <b>Миқдори UC:</b> "
        f"{data['total_uc']} UC\n"

        f"💰 <b>Миқдори маблағ:</b> "
        f"{data['total_amount']} сомонӣ\n\n"

        f"{PAYMENT_DETAILS}\n\n"

        "📸 <b>Баъд аз равон кардани маблағ, "
        "чеки пардохтро ҳамчун акс ё файл равон кунед.</b>",

        reply_markup=user_back_home()
    )


# ============================================================
# RECEIVE PUBG ID — BONUS PURCHASE
# ============================================================

@bot.message_handler(
    func=lambda m:
    user_states.get(
        m.from_user.id,
        {}
    ).get("state")
    == "waiting_bonus_pubg_id"
)
def receive_bonus_pubg_id(message):

    user_id = message.from_user.id

    if not message.text:

        bot.send_message(
            message.chat.id,
            "⚠️ PUBG ID-ро ҳамчун рақам равон кунед."
        )

        return

    pubg_id = message.text.strip()

    if not pubg_id.isdigit():

        bot.send_message(
            message.chat.id,

            "❌ PUBG ID нодуруст аст.\n\n"
            "PUBG ID бояд танҳо аз рақамҳо иборат бошад."
        )

        return

    data = user_states.get(
        user_id,
        {}
    )

    uc = data.get("uc")
    bonus_used = data.get("bonus_used")

    if not uc or not bonus_used:

        user_states.pop(
            user_id,
            None
        )

        bot.send_message(
            user_id,
            "❌ Маълумоти заказ ёфт нашуд. Лутфан аз нав кӯшиш кунед."
        )

        return

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ========================================================
    # ЗАКАЗ + КАМ КАРДАНИ БОНУС ДАР ЯК ТРАНЗАКСИЯ
    # ========================================================

    with db_lock:

        conn = get_db()

        # Бонуси воқеии корбар
        user_row = conn.execute(
            """
            SELECT bonus
            FROM users
            WHERE telegram_id=?
            """,
            (user_id,)
        ).fetchone()

        current_bonus = (
            user_row["bonus"]
            if user_row
            else 0
        )

        # Санҷиши бонус
        if current_bonus < bonus_used:

            conn.close()

            bot.send_message(
                user_id,

                f"❌ <b>Бонуси шумо намерасад.</b>\n\n"
                f"🎁 Бонуси лозим: <b>{bonus_used}</b>\n"
                f"💰 Бонуси шумо: <b>{current_bonus}</b>"
            )

            return

        # ====================================================
        # Барои закази бо бонус харидшуда
        # бонуси нав дода намешавад
        # ====================================================

        bonus_earned = 0

        # ====================================================
        # Сохтани заказ
        # ====================================================

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO orders
            (
                user_id,
                first_name,
                username,
                pubg_id,
                uc,
                amount,
                bonus_used,
                bonus_earned,
                receipt_file_id,
                receipt_type,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 'pending', ?)
            """,
            (
                user_id,
                message.from_user.first_name or "",
                message.from_user.username or "",
                pubg_id,
                uc,
                0,
                bonus_used,
                bonus_earned,
                now
            )
        )

        order_id = cur.lastrowid

        # ====================================================
        # Кам кардани бонус
        # ====================================================

        conn.execute(
            """
            UPDATE users
            SET bonus = COALESCE(bonus, 0) - ?
            WHERE telegram_id=?
            """,
            (
                bonus_used,
                user_id
            )
        )

        conn.commit()
        conn.close()

    # Ҳолати корбарро тоза мекунем
    user_states.pop(
        user_id,
        None
    )

    # ========================================================
    # ПАЁМ БА КОРБАР
    # ========================================================

    bot.send_message(
        user_id,

        f"✅ <b>Заказ №{order_id:06d} қабул шуд.</b>\n\n"

        f"🎮 <b>PUBG ID:</b> "
        f"<code>{pubg_id}</code>\n"

        f"💎 <b>UC:</b> {uc}\n"

        f"🎁 <b>Бонус истифода шуд:</b> "
        f"{bonus_used}\n\n"

        "⏳ Заказ ба админ равон карда шуд.\n"
        "🙏 Лутфан интизор шавед.",

        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(
                "🏠 Менюи асосӣ",
                callback_data="home"
            )
        )
    )

    # ========================================================
    # ПАЁМ БА АДМИН
    # ========================================================

    send_bonus_order_to_admin(
        order_id
    )
    
# ============================================================
# RECEIVE RECEIPT
# ============================================================

@bot.message_handler(
    content_types=[
        "photo",
        "document"
    ],
    func=lambda m:
    user_states.get(
        m.from_user.id,
        {}
    ).get("state")
    == "waiting_receipt"
)
def receive_receipt(message):

    user_id = message.from_user.id

    data = user_states[user_id]

    if message.photo:

        file_id = message.photo[-1].file_id
        receipt_type = "photo"

    else:

        file_id = message.document.file_id
        receipt_type = "document"

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with db_lock:

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
    """
    INSERT INTO orders
    (
        user_id,
        first_name,
        username,
        pubg_id,
        uc,
        amount,
        bonus_earned,
        receipt_file_id,
        receipt_type,
        status,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    """,
    (
        user_id,
        message.from_user.first_name or "",
        message.from_user.username or "",
        data["pubg_id"],
        data["total_uc"],
        data["total_amount"],
        data["total_bonus"],
        file_id,
        receipt_type,
        now
    )
)

        order_id = cur.lastrowid

        conn.commit()
        conn.close()

    user_states.pop(
        user_id,
        None
    )

    # Танҳо менюи асосӣ
    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    bot.send_message(
        message.chat.id,

        f"✅ <b>Заказ №{order_id:06d} қабул шуд.</b>\n\n"

        "⏳ Закази шумо ба админ барои санҷиш равон карда шуд.\n\n"

        "Дар муддати кӯтоҳтарин UC ба PUBG ID-и шумо "
        "ирсол карда мешавад.\n\n"

        "🙏 Лутфан интизор шавед.",

        reply_markup=kb
    )

    send_order_to_admin(
        order_id
    )


# ============================================================
# ORDER TEXT
# ============================================================

def order_text(order):

    return (
        f"📦 <b>ЗАКАЗ №{order['id']:06d}</b>\n\n"

        f"👤 <b>Корбар:</b> "
        f"{html.escape(order['first_name'])}\n"

        f"🔹 <b>Никнейм:</b> "
        f"{username_text(order)}\n"

        f"🎮 <b>PUBG ID:</b> "
        f"<code>{order['pubg_id']}</code>\n"

        f"💎 <b>Миқдори UC:</b> "
        f"{order['uc']} UC\n"

        f"💰 <b>Маблағ:</b> "
        f"{order['amount']} сомонӣ\n"

        f"📊 <b>Ҳолат:</b> "
        f"{status_text(order['status'])}\n"

        f"📅 <b>Сана:</b> "
        f"{order['created_at']}"
    )


# ============================================================
# SEND ORDER TO ADMIN
# ============================================================

def send_order_to_admin(order_id):

    order = get_order(
        order_id
    )

    if not order:
        return

    kb = types.InlineKeyboardMarkup()

    if order["status"] == "pending":

        kb.row(
            types.InlineKeyboardButton(
                "✅ Иҷро шуд",
                callback_data=f"order_done:{order_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Иҷро нашуд",
                callback_data=f"order_reject:{order_id}"
            )
        )

    text = order_text(order)

    if order["receipt_type"] == "photo":

        bot.send_photo(
            ADMIN_ID,
            order["receipt_file_id"],
            caption=text,
            reply_markup=kb
        )

    else:

        bot.send_document(
            ADMIN_ID,
            order["receipt_file_id"],
            caption=text,
            reply_markup=kb
        )


# ============================================================
# SEND BONUS ORDER TO ADMIN
# ============================================================

def send_bonus_order_to_admin(order_id):

    order = get_order(
        order_id
    )

    if not order:
        return

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "✅ Иҷро шуд",
            callback_data=f"order_done:{order_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Иҷро нашуд",
            callback_data=f"order_reject:{order_id}"
        )
    )

    text = (
        f"🎁 <b>ЗАКАЗ БО БОНУС №{order['id']:06d}</b>\n\n"

        f"👤 <b>Корбар:</b> "
        f"{html.escape(order['first_name'])}\n"

        f"🔹 <b>Никнейм:</b> "
        f"{username_text(order)}\n"

        f"🎮 <b>PUBG ID:</b> "
        f"<code>{order['pubg_id']}</code>\n"

        f"💎 <b>Миқдори UC:</b> "
        f"{order['uc']} UC\n"

        f"🎁 <b>Бонус истифода шуд:</b> "
        f"{order['bonus_used']} бонус\n\n"

        f"📊 <b>Ҳолат:</b> "
        f"{status_text(order['status'])}\n"

        f"📅 <b>Сана:</b> "
        f"{order['created_at']}"
    )

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=kb
    )
    
# ============================================================
# ORDER DONE
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("order_done:")
)
def order_done(call):

    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(
            call.id,
            "Дастрасӣ манъ аст."
        )
        return

    order_id = int(
        call.data.split(":")[1]
    )

    order = get_order(order_id)

    if not order:
        bot.answer_callback_query(
            call.id,
            "Заказ ёфт нашуд."
        )
        return

    if order["status"] != "pending":
        bot.answer_callback_query(
            call.id,
            "Ин заказ аллакай коркард шудааст."
        )
        return

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ========================================================
    # ТАНҲО ҲОЛАТИ ЗАКАЗРО ИҶРОШУДА МЕКУНЕМ
    # БОНУС ДИГАР ДАР ИН ҶО КАМ НАМЕШАВАД
    # ========================================================

    with db_lock:
        conn = get_db()

        conn.execute("""
            UPDATE orders
            SET status='completed',
                completed_at=?
            WHERE id=?
        """, (
            now,
            order_id
        ))
        
        conn.commit()
        conn.close()

    bot.answer_callback_query(
        call.id,
        "Заказ иҷро шуд."
    )

    # ========================================================
    # КНОПКАҲО БАРОИ КОРБАР
    # ========================================================

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "⭐ Гузоштани отзыв",
            callback_data=f"review:{order_id}"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    # ========================================================
    # АГАР ЗАКАЗ БО БОНУС БОШАД
    # ========================================================

    bonus_used = order["bonus_used"] or 0

    bonus_text = ""

    if bonus_used > 0:
        bonus_text = (
            f"\n\n🎁 <b>Бонуси истифода шуда:</b> "
            f"{bonus_used}"
        )

    # ========================================================
    # ПАЁМ БА КОРБАР
    # ========================================================

    bot.send_message(
    order["user_id"],
    f"🎉 <b>Закази Шумо иҷро шуд!</b>\n\n"
    f"💎 <b>{order['uc']} UC ба ID: {order['pubg_id']} ИРСОЛ КАРДА ШУД ✅</b>\n\n"
    f"🎁 Барои гирифтани <b>{order['bonus_earned'] or 0} бонус</b> "
    "Шумо ҳатман бояд отзыв гузоред.",
    reply_markup=kb
)

# ========================================================
# ПАЁМ БА АДМИН
# ========================================================

    admin_bonus_text = ""

    if bonus_used > 0:
        admin_bonus_text = (
            f"\n🎁 <b>Бонуси истифода шуда:</b> "
            f"{bonus_used}"
        )

    bot.send_message(
        ADMIN_ID,
        f"📦 <b>Заказ №{order_id:06d}</b>\n\n"
        f"🟢 <b>Ҳолат:</b> Иҷрошуда"
        f"{admin_bonus_text}",
        reply_markup=admin_back_home()
    )

# ============================================================
# ORDER REJECT
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("order_reject:")
)
def order_reject(call):

    if call.from_user.id != ADMIN_ID:

        bot.answer_callback_query(
            call.id,
            "Дастрасӣ манъ аст."
        )

        return

    order_id = int(
        call.data.split(":")[1]
    )

    order = get_order(
        order_id
    )

    if not order:

        bot.answer_callback_query(
            call.id,
            "Заказ ёфт нашуд."
        )

        return

    if order["status"] != "pending":

        bot.answer_callback_query(
            call.id,
            "Ин заказ аллакай коркард шудааст."
        )

        return

    admin_states[ADMIN_ID] = {
        "state": "reject_order",
        "order_id": order_id
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        f"❌ <b>Заказ №{order_id:06d}</b>\n\n"
        "✍️ Сабаби иҷро нашудани заказро нависед:"
    )


# ============================================================
# REJECT REASON
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "reject_order"
)
def reject_reason(message):

    data = admin_states[
        ADMIN_ID
    ]

    order_id = data[
        "order_id"
    ]

    reason = (
        message.text
        or
        "Сабаб нишон дода нашуд."
    )

    order = get_order(
        order_id
    )

    if not order:
        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.send_message(
            ADMIN_ID,
            "❌ Заказ ёфт нашуд."
        )

        return

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ========================================================
    # ЗАКАЗРО РАД КАРДАН ВА БАРГАРДОНИДАНИ БОНУС
    # ========================================================

    with db_lock:

        conn = get_db()

        # 1. Заказро радшуда мекунем
        conn.execute(
            """
            UPDATE orders
            SET status='rejected',
                reject_reason=?,
                completed_at=?
            WHERE id=?
            AND status='pending'
            """,
            (
                reason,
                now,
                order_id
            )
        )

        # 2. Агар заказ бо бонус бошад,
        #    бонуси истифодашударо бармегардонем
        bonus_used = order["bonus_used"] or 0

        if bonus_used > 0:

            conn.execute(
                """
                UPDATE users
                SET bonus = COALESCE(bonus, 0) + ?
                WHERE telegram_id=?
                """,
                (
                    bonus_used,
                    order["user_id"]
                )
            )

        conn.commit()
        conn.close()

    # ========================================================
    # ҲОЛАТИ АДМИНРО ТОЗА МЕКУНЕМ
    # ========================================================

    admin_states.pop(
        ADMIN_ID,
        None
    )

    # ========================================================
    # БА КОРБАР ХАБАР
    # ========================================================

    bot.send_message(
        order["user_id"],

        f"❌ <b>Закази шумо рад шуд.</b>\n\n"
        f"📝 <b>Сабаби рад шудан:</b>\n"
        f"{html.escape(reason)}",

        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(
                "🏠 Менюи асосӣ",
                callback_data="home"
            )
        )
    )

    # ========================================================
    # БА АДМИН ХАБАР
    # ========================================================

    bot.send_message(
        ADMIN_ID,

        f"📦 Заказ №{order_id:06d} ба ҳолати "
        f"<b>🔴 Радшуда</b> гузошта шуд.",

        reply_markup=admin_back_home()
    )


# ============================================================
# USER ORDERS
# ============================================================

@bot.message_handler(
      func=lambda m:
    m.text == "📦 Заказҳои ман"
)
def user_orders(message):

    if message.from_user.id == ADMIN_ID:

        show_admin_orders_menu(
            message.chat.id
        )

        return

    user_id = message.from_user.id

    with db_lock:

        conn = get_db()

        total = conn.execute(
            """
            SELECT COUNT(*)
            FROM orders
            WHERE user_id=?
            """,
            (user_id,)
        ).fetchone()[0]

        completed = conn.execute(
            """
            SELECT COUNT(*)
            FROM orders
            WHERE user_id=?
            AND status='completed'
            """,
            (user_id,)
        ).fetchone()[0]

        rejected = conn.execute(
            """
            SELECT COUNT(*)
            FROM orders
            WHERE user_id=?
            AND status='rejected'
            """,
            (user_id,)
        ).fetchone()[0]

        conn.close()

    text = (
        "📦 <b>ЗАКАЗҲОИ МАН</b>\n\n"

        f"📦 <b>Миқдори заказҳо:</b> "
        f"{total}\n"

        f"🟢 <b>Заказҳои иҷрошуда:</b> "
        f"{completed}\n"

        f"🔴 <b>Заказҳои радшуда:</b> "
        f"{rejected}"
    )

    if total == 0:

        text += (
            "\n\n📭 Ҳоло шумо ягон заказ надоред."
        )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=user_back_home()
    )


# ============================================================
# USER REVIEWS / CHANNEL
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text.startswith("⭐ Отзывы")
)
def user_reviews(message):

    if message.from_user.id == ADMIN_ID:

        admin_reviews(
            message
        )

        return

    text = (
        "⭐ <b>ОТЗЫВҲОИ МИЗОҶОНИ МО</b>\n\n"

        "Фикру назари харидорони моро метавонед "
        "дар канали отзывҳо бинед. ❤️\n\n"

        "📢 Барои дидани отзывҳо тугмаи зерро пахш кунед."
    )

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "📢 Канали Отзывҳо",
            url="https://t.me/otziv_ALI_US_SHOPP"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=kb
    )


# ============================================================
# START REVIEW
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("review:")
)
def start_review(call):

    user_id = call.from_user.id

    order_id = int(
        call.data.split(":")[1]
    )

    order = get_order(
        order_id
    )

    if not order:

        bot.answer_callback_query(
            call.id,
            "Заказ ёфт нашуд."
        )

        return

    if order["user_id"] != user_id:

        bot.answer_callback_query(
            call.id,
            "Ин заказ аз шумо нест."
        )

        return

    if order["status"] != "completed":

        bot.answer_callback_query(
            call.id,
            "Аввал заказ бояд иҷро шавад."
        )

        return

    user_states[user_id] = {
        "state": "waiting_review",
        "order_id": order_id
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
    user_id,

    f"🎁 Барои гирифтани <b>{order['bonus_earned'] or 0} бонус</b> "
    f"Шумо ҳатман бояд отзыв гузоред.\n\n"
    "⭐ Лутфан отзывро ҳамчун 📝 матн, 📸 расм ё 🎤 овоз равон кунед:",

    reply_markup=user_back_home()
)


# ============================================================
# RECEIVE REVIEW
# ============================================================

@bot.message_handler(
    func=lambda m:
    user_states.get(
        m.from_user.id,
        {}
    ).get("state")
    == "waiting_review"
)
def receive_review(message):

    user_id = message.from_user.id

    data = user_states[user_id]

    order_id = data["order_id"]

    order = get_order(order_id)

    if not order:

        user_states.pop(user_id, None)

        bot.send_message(
            user_id,
            "❌ Заказ ёфт нашуд."
        )

        return

        # Муайян кардани намуди отзыв

    review_text = message.text or message.caption or ""

    review_file_id = None
    review_file_type = None

    if message.photo:

        review_file_id = message.photo[-1].file_id
        review_file_type = "photo"

    elif message.voice:

        review_file_id = message.voice.file_id
        review_file_type = "voice"

    elif message.video:

        review_file_id = message.video.file_id
        review_file_type = "video"

    elif message.document:

        review_file_id = message.document.file_id
        review_file_type = "document"

    elif not review_text:

        bot.send_message(
            user_id,
            "⚠️ Лутфан отзывро ҳамчун 📝 матн, 📸 расм ё 🎤 овоз равон кунед."
        )

        return

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with db_lock:

        conn = get_db()

        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO reviews
            (
                order_id,
                user_id,
                first_name,
                username,
                uc,
                amount,
                text,
                review_file_id,
                review_file_type,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                order_id,
                user_id,
                message.from_user.first_name or "",
                message.from_user.username or "",
                order["uc"],
                order["amount"],
                review_text,
                review_file_id,
                review_file_type,
                now
            )
        )

        review_id = cur.lastrowid

        conn.commit()
        conn.close()

    user_states.pop(
        user_id,
        None
    )

    bot.send_message(
        user_id,

        "✅ <b>Отзыви шумо қабул шуд.</b>\n\n"
        "⏳ Он барои санҷиш ба админ равон карда шуд.",

        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(
                "🏠 Менюи асосӣ",
                callback_data="home"
            )
        )
    )

    send_review_to_admin(
        review_id
    )


# ============================================================
# SEND REVIEW TO ADMIN
# ============================================================

def send_review_to_admin(review_id):

    review = get_review(review_id)

    if not review:
        return

    print(
        "REVIEW DEBUG:",
        review["review_file_id"],
        review["review_file_type"]
    )

    text = (
        f"⭐ <b>ОТЗЫВ №{review_id:06d}</b>\n\n"

        f"👤 <b>Корбар:</b> "
        f"{html.escape(review['first_name'] or '')}\n"

        f"🔹 <b>Никнейм:</b> "
        f"{username_text(review)}\n"

        f"📦 <b>Заказ:</b> "
        f"№{review['order_id']:06d}\n"

        f"💎 <b>UC:</b> "
        f"{review['uc']} UC\n"

        f"💰 <b>Маблағ:</b> "
        f"{review['amount']} сомонӣ\n\n"

        f"📝 <b>Отзыви корбар:</b>\n"
        f"{html.escape(review['text'] or '—')}"
    )

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "✅ Қабул шуд",
            callback_data=f"review_accept:{review_id}"
        ),
        types.InlineKeyboardButton(
            "❌ Қабул нашуд",
            callback_data=f"review_reject:{review_id}"
        )
    )

    try:

        # Агар отзыв расм бошад
        if review["review_file_id"] and review["review_file_type"] == "photo":

            bot.send_photo(
                ADMIN_ID,
                review["review_file_id"]
            )

            bot.send_message(
                ADMIN_ID,
                text,
                reply_markup=kb
            )

        # Агар отзыв овоз бошад
        elif review["review_file_id"] and review["review_file_type"] == "voice":

            bot.send_voice(
                ADMIN_ID,
                review["review_file_id"]
            )

            bot.send_message(
                ADMIN_ID,
                text,
                reply_markup=kb
            )

        # Агар видео бошад
        elif review["review_file_id"] and review["review_file_type"] == "video":

            bot.send_video(
                ADMIN_ID,
                review["review_file_id"]
            )

            bot.send_message(
                ADMIN_ID,
                text,
                reply_markup=kb
            )

        # Агар файл бошад
        elif review["review_file_id"] and review["review_file_type"] == "document":

            bot.send_document(
                ADMIN_ID,
                review["review_file_id"]
            )

            bot.send_message(
                ADMIN_ID,
                text,
                reply_markup=kb
            )

        # Агар танҳо матн бошад
        else:

            bot.send_message(
                ADMIN_ID,
                text,
                reply_markup=kb
            )

    except Exception as e:

        print(
            "SEND REVIEW ADMIN ERROR:",
            e
        )

        # Агар фиристодани расм хато шавад,
        # ҳадди ақал матни отзыв ба админ меравад
        try:

            bot.send_message(
                ADMIN_ID,
                text,
                reply_markup=kb
            )

        except Exception as e2:

            print(
                "SEND REVIEW TEXT ERROR:",
                e2
            )


# ============================================================
# ADMIN REVIEWS MENU
# ============================================================

def admin_reviews(message):

    if message.from_user.id != ADMIN_ID:
        return

    with db_lock:

        conn = get_db()

        rows = conn.execute(
            """
            SELECT *
            FROM reviews
            ORDER BY id DESC
            """
        ).fetchall()

        conn.close()

    text = "⭐ <b>ОТЗЫВҲО</b>\n\n"

    kb = types.InlineKeyboardMarkup()

    if not rows:

        text += "Ҳоло отзыв нест."

    else:

        for review in rows:

            icon = {
                "pending": "🟡",
                "accepted": "🟢",
                "rejected": "🔴"
            }.get(
                review["status"],
                "⚪"
            )

            kb.add(
                types.InlineKeyboardButton(
                    f"⭐ Отзыв №{review['id']:06d} {icon}",
                    callback_data=f"admin_review:{review['id']}"
                )
            )

    # ========================================================
    # DELETE REVIEWS BUTTON
    # ========================================================

    kb.add(
        types.InlineKeyboardButton(
            "🗑 Нест кардани отзывҳо",
            callback_data="admin_delete_reviews"
        )
    )
    
    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=kb
    )


# ============================================================
# ADMIN REVIEW DETAILS
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("admin_review:")
)
def admin_review_details(call):

    if call.from_user.id != ADMIN_ID:
        return

    review_id = int(
        call.data.split(":")[1]
    )

    review = get_review(
        review_id
    )

    if not review:

        bot.answer_callback_query(
            call.id,
            "Отзыв ёфт нашуд."
        )

        return

    text = (
        f"⭐ <b>ОТЗЫВ №{review_id:06d}</b>\n\n"

        f"👤 <b>Корбар:</b> "
        f"{html.escape(review['first_name'])}\n"

        f"🔹 <b>Никнейм:</b> "
        f"{username_text(review)}\n"

        f"📦 <b>Заказ:</b> "
        f"№{review['order_id']:06d}\n"

        f"💎 <b>UC:</b> "
        f"{review['uc']} UC\n"

        f"💰 <b>Маблағ:</b> "
        f"{review['amount']} сомонӣ\n"

        f"📊 <b>Ҳолат:</b> "
        f"{review['status']}\n\n"

        f"📝 <b>Отзыв:</b>\n"
        f"{html.escape(review['text'])}"
    )

    kb = types.InlineKeyboardMarkup()

    if review["status"] == "pending":

        kb.row(
            types.InlineKeyboardButton(
                "✅ Қабул шуд",
                callback_data=f"review_accept:{review_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Қабул нашуд",
                callback_data=f"review_reject:{review_id}"
            )
        )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_reviews"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=kb
    )

    bot.answer_callback_query(
        call.id
    )


# ============================================================
# REVIEW ACCEPT
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("review_accept:")
)
def review_accept(call):

    if call.from_user.id != ADMIN_ID:
        return

    review_id = int(
        call.data.split(":")[1]
    )

    review = get_review(review_id)

    if not review:
        bot.answer_callback_query(
            call.id,
            "Отзыв ёфт нашуд."
        )
        return

    user_id = review["user_id"]

    with db_lock:

        conn = get_db()

        # 1. Заказро мегирем
        order = conn.execute(
            """
            SELECT bonus_earned
            FROM orders
            WHERE id=?
            """,
            (review["order_id"],)
        ).fetchone()

        if not order:
            conn.close()

            bot.answer_callback_query(
                call.id,
                "Заказ ёфт нашуд."
            )
            return

        bonus_to_add = order["bonus_earned"] or 0

        # 2. Отзывро танҳо агар pending бошад, қабул мекунем
        cur = conn.execute(
            """
            UPDATE reviews
            SET status='accepted'
            WHERE id=?
            AND status='pending'
            """,
            (review_id,)
        )

        # Агар аллакай қабул шуда бошад,
        # бонуси дуюм дода намешавад
        if cur.rowcount != 1:

            conn.close()

            bot.answer_callback_query(
                call.id,
                "Ин отзыв аллакай коркард шудааст."
            )
            return

        # 3. Бонуси тамоми заказро якбора илова мекунем
        if bonus_to_add > 0:

            conn.execute(
                """
                UPDATE users
                SET bonus = COALESCE(bonus, 0) + ?
                WHERE telegram_id=?
                """,
                (
                    bonus_to_add,
                    user_id
                )
            )

        conn.commit()
        conn.close()

    # 4. Ба админ хабар
    bot.answer_callback_query(
        call.id,
        f"Отзыв қабул шуд. +{bonus_to_add} бонус"
    )

    # 5. Ба корбар хабар
    bot.send_message(
    user_id,

    f"⭐ <b>Ташаккур барои отзыватон!</b>\n\n"
    f"✅ Отзыви шумо қабул шуд.\n"
    f"🎁 Ба шумо <b>+{bonus_to_add} бонус</b> илова шуд.\n\n"
    "❤️ Ташаккур барои боварӣ ва дастгирӣ!",

    reply_markup=user_back_home()
)


    # ========================================================
    # БА КАНАЛ — ЧЕК + РАСМИ ОТЗЫВ + МАТНИ ОТЗЫВ
    # ========================================================

    channel_text = (
        "⭐ <b>ОТЗЫВИ НАВ</b>\n\n"

        f"💎 <b>{review['uc']} UC "
        f"ИРСОЛ КАРДА ШУД ✅</b>\n\n"

        f"📝 <b>Отзыви корбар:</b>\n"
        f"{html.escape(review['text'] or '—')}\n\n"

        "🛒 <b>Шумо ҳам хоҳед зуд ва бо боварӣ UC харед?</b>\n"
        "Ба @ALI_UC_SHOP_BOT муроҷиат кунед. ❤️"
    )

    try:

        # ----------------------------------------------------
        # 1. ЧЕКИ КОРБАР
        # ----------------------------------------------------

        with db_lock:

            conn = get_db()

            order = conn.execute(
                """
                SELECT receipt_file_id, receipt_type
                FROM orders
                WHERE id=?
                """,
                (review["order_id"],)
            ).fetchone()

            conn.close()

        if order and order["receipt_file_id"]:

            if order["receipt_type"] == "photo":

                bot.send_photo(
                    REVIEWS_CHANNEL,
                    order["receipt_file_id"],
                    caption="🧾 <b>ЧЕКИ КОРБАР</b>"
                )

            elif order["receipt_type"] == "document":

                bot.send_document(
                    REVIEWS_CHANNEL,
                    order["receipt_file_id"],
                    caption="🧾 <b>ЧЕКИ КОРБАР</b>"
                )

        # ----------------------------------------------------
        # 2. РАСМИ ОТЗЫВ
        # ----------------------------------------------------

        if (
            review["review_file_id"]
            and review["review_file_type"] == "photo"
        ):

            bot.send_photo(
                REVIEWS_CHANNEL,
                review["review_file_id"],
                caption="📸 <b>ЧЕКИ ОТЗЫВ</b>"
            )

        # ----------------------------------------------------
        # 3. МАТНИ ОТЗЫВ + UC + МАТНИ ОХИР
        # ----------------------------------------------------

        bot.send_message(
            REVIEWS_CHANNEL,
            channel_text
        )

    except Exception as e:

        print(
            "CHANNEL REVIEW ERROR:",
            e
        )

    # Паём ба админ
    bot.send_message(
        ADMIN_ID,

        f"⭐ Отзыв №{review_id:06d} "
        f"ба ҳолати <b>🟢 Қабулшуда</b> гузошта шуд.",

        reply_markup=admin_back_home()
    )


# ============================================================
# REVIEW REJECT
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("review_reject:")
)
def review_reject(call):

    if call.from_user.id != ADMIN_ID:
        return

    review_id = int(
        call.data.split(":")[1]
    )

    review = get_review(
        review_id
    )

    if not review:

        bot.answer_callback_query(
            call.id,
            "Отзыв ёфт нашуд."
        )

        return

    if review["status"] != "pending":

        bot.answer_callback_query(
            call.id,
            "Ин отзыв аллакай коркард шудааст."
        )

        return

    admin_states[ADMIN_ID] = {
        "state": "reject_review",
        "review_id": review_id
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        f"❌ <b>Отзыв №{review_id:06d}</b>\n\n"
        "✍️ Сабаби қабул нашудани отзывро нависед:"
    )


# ============================================================
# REVIEW REJECT REASON
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "reject_review"
)
def reject_review_reason(message):

    review_id = admin_states[
        ADMIN_ID
    ]["review_id"]

    reason = (
        message.text
        or
        "Сабаб нишон дода нашуд."
    )

    review = get_review(
        review_id
    )

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            UPDATE reviews
            SET status='rejected',
                reject_reason=?
            WHERE id=?
            """,
            (
                reason,
                review_id
            )
        )

        conn.commit()
        conn.close()

    admin_states.pop(
        ADMIN_ID,
        None
    )

    # Ба корбар
    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "⭐ Дубора отзыв гузоштан",
            callback_data=f"review:{review['order_id']}"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="home"
        )
    )

    bot.send_message(
        review["user_id"],

        "❌ <b>Отзыви шумо қабул нашуд.</b>\n\n"

        f"📝 <b>Сабаб:</b>\n"
        f"{html.escape(reason)}\n\n"

        "Шумо метавонед дубора отзыв гузоред.",

        reply_markup=kb
    )

    bot.send_message(
        ADMIN_ID,

        f"⭐ Отзыв №{review_id:06d} ба ҳолати "
        f"<b>🔴 Қабулнашуда</b> гузошта шуд.",

        reply_markup=admin_back_home()
    )


# ============================================================
# ADMIN ORDERS MENU
# ============================================================

def show_admin_orders_menu(chat_id):

    # ========================================================
    # ҲИСОБИ ЗАКАЗҲО
    # ========================================================

    with db_lock:
        conn = get_db()

        total_orders = conn.execute("""
            SELECT COUNT(*)
            FROM orders
        """).fetchone()[0]

        pending_orders = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status='pending'
        """).fetchone()[0]

        completed_orders = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status='completed'
        """).fetchone()[0]

        rejected_orders = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE status='rejected'
        """).fetchone()[0]

        conn.close()

    # ========================================================
    # МЕНЮ
    # ========================================================

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            f"🆕 Заказҳои нав ({pending_orders})",
            callback_data="admin_new_orders"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            f"📋 Ҳамаи заказҳо ({total_orders})",
            callback_data="admin_all_orders"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            f"🟢 Заказҳои иҷрошуда ({completed_orders})",
            callback_data="admin_completed_orders"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            f"🔴 Заказҳои радшуда ({rejected_orders})",
            callback_data="admin_rejected_orders"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_home"
        )
    )

    bot.send_message(
        chat_id,
        "📦 <b>ЗАКАЗҲО</b>\n\n"
        "Категорияи заказро интихоб кунед:",
        reply_markup=kb
    )


# ============================================================
# ADMIN ORDERS BUTTON
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text.startswith("📦 Заказҳо")
)
def admin_orders_button(message):

    if message.from_user.id != ADMIN_ID:
        return

    show_admin_orders_menu(
        message.chat.id
    )


# ============================================================
# ADMIN ORDER LIST
# ============================================================

def show_admin_orders(
    chat_id,
    mode
):

    if mode == "pending":

        title = "🆕 <b>ЗАКАЗҲОИ НАВ</b>"
        where = "status='pending'"

    elif mode == "all":

        title = "📋 <b>ҲАМАИ ЗАКАЗҲО</b>"
        where = "1=1"

    elif mode == "completed":

        title = "🟢 <b>ЗАКАЗҲОИ ИҶРОШУДА</b>"
        where = "status='completed'"

    else:

        title = "🔴 <b>ЗАКАЗҲОИ РАДШУДА</b>"
        where = "status='rejected'"

    with db_lock:

        conn = get_db()

        rows = conn.execute(
            f"""
            SELECT *
            FROM orders
            WHERE {where}
            ORDER BY id DESC
            """
        ).fetchall()

        conn.close()

    kb = types.InlineKeyboardMarkup()

    text = title + "\n\n"

    if not rows:

        text += "📭 Ягон заказ ёфт нашуд."

    else:

        for order in rows:

            icon = {
                "pending": "🟡",
                "completed": "🟢",
                "rejected": "🔴"
            }.get(
                order["status"],
                "⚪"
            )

            kb.add(
                types.InlineKeyboardButton(
                    f"📦 Заказ №{order['id']:06d} {icon}",
                    callback_data=f"admin_order:{order['id']}"
                )
            )

    if mode == "all":

        kb.add(
            types.InlineKeyboardButton(
                 "🗑 Нест кардани заказҳо",
                callback_data="admin_delete_orders"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_orders"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.send_message(
        chat_id,
        text,
        reply_markup=kb
    )


# ============================================================
# ADMIN DELETE ORDERS CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "admin_delete_orders"
)
def admin_delete_orders(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states[ADMIN_ID] = {
        "state": "delete_orders"
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        call.message.chat.id,
        "🗑 <b>Нест кардани заказҳо</b>\n\n"
        "Чанд закази охиринро нест кардан мехоҳед?\n\n"
        "🔢 Танҳо рақамро нависед.\n"
        "Масалан: <code>5</code>",
        parse_mode="HTML"
    )


# ============================================================
# ADMIN ORDERS LIST CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data in [
        "admin_new_orders",
        "admin_all_orders",
        "admin_completed_orders",
        "admin_rejected_orders"
    ]
)
def admin_orders_list(call):

    if call.from_user.id != ADMIN_ID:
        return

    mapping = {
        "admin_new_orders": "pending",
        "admin_all_orders": "all",
        "admin_completed_orders": "completed",
        "admin_rejected_orders": "rejected"
    }

    bot.answer_callback_query(
        call.id
    )

    show_admin_orders(
        call.message.chat.id,
        mapping[call.data]
    )


# ============================================================
# ADMIN ORDERS BACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "admin_orders"
)
def admin_orders_back(call):

    if call.from_user.id != ADMIN_ID:
        return

    bot.answer_callback_query(
        call.id
    )

    show_admin_orders_menu(
        call.message.chat.id
    )


# ============================================================
# ADMIN ORDER DETAILS
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("admin_order:")
)
def admin_order_details(call):

    if call.from_user.id != ADMIN_ID:
        return

    order_id = int(
        call.data.split(":")[1]
    )

    order = get_order(
        order_id
    )

    if not order:

        bot.answer_callback_query(
            call.id,
            "Заказ ёфт нашуд."
        )

        return

    text = order_text(
        order
    )

    if order["status"] == "rejected" and order["reject_reason"]:

        text += (
            "\n\n📝 <b>Сабаби рад шудан:</b>\n"
            f"{html.escape(order['reject_reason'])}"
        )

    kb = types.InlineKeyboardMarkup()

    if order["status"] == "pending":

        kb.row(
            types.InlineKeyboardButton(
                "✅ Иҷро шуд",
                callback_data=f"order_done:{order_id}"
            ),
            types.InlineKeyboardButton(
                "❌ Иҷро нашуд",
                callback_data=f"order_reject:{order_id}"
            )
        )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_all_orders"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    # Маълумот
    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=kb
    )

    # Агар чек бошад, дар дохили маълумот боз чекро нишон медиҳем
    if order["receipt_type"] == "photo":

        try:

            bot.send_photo(
                ADMIN_ID,
                order["receipt_file_id"],
                caption="🧾 <b>ЧЕКИ ПАРДОХТ</b>"
            )

        except Exception:
            pass

    else:

        try:

            bot.send_document(
                ADMIN_ID,
                order["receipt_file_id"],
                caption="🧾 <b>ЧЕКИ ПАРДОХТ</b>"
            )

        except Exception:
            pass

    bot.answer_callback_query(
        call.id
    )


# ============================================================
# ADMIN REVIEWS BUTTON
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text == "⭐ Отзывы"
    and m.from_user.id == ADMIN_ID
)
def admin_reviews_button(message):

    admin_reviews(
        message
    )


# ============================================================
# ACTIVE USERS
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text.startswith("👥 Корбарони фаъол")
)
def active_users(message):

    if message.from_user.id != ADMIN_ID:
        return

    with db_lock:
        conn = get_db()

        rows = conn.execute("""
            SELECT
                u.telegram_id,
                u.first_name,
                u.username,
                COUNT(o.id) AS total_orders,
                COALESCE(SUM(
                    CASE
                        WHEN o.status = 'completed'
                        THEN o.uc
                        ELSE 0
                    END
                ), 0) AS total_uc,
                COALESCE(SUM(
                    CASE
                        WHEN o.status = 'completed'
                        THEN o.amount
                        ELSE 0
                    END
                ), 0) AS total_amount
            FROM users u
            LEFT JOIN orders o
                ON u.telegram_id = o.user_id
            GROUP BY
                u.telegram_id,
                u.first_name,
                u.username
            ORDER BY total_orders DESC
        """).fetchall()

        conn.close()

    text = "👥 <b>КОРБАРОНИ ФАЪОЛ</b>\n\n"

    kb = types.InlineKeyboardMarkup()

    if not rows:
        text += "Ҳоло корбар нест."

    else:
        for i, user in enumerate(rows, 1):

            name = html.escape(
                user["first_name"] or "Беном"
            )

            username = (
                "@" + html.escape(user["username"])
                if user["username"]
                else "Нест"
            )

            kb.add(
                types.InlineKeyboardButton(
                    f"👤 {name} | 📦 {user['total_orders']} | "
                    f"💎 {user['total_uc']} UC | "
                    f"💰 {user['total_amount']} с.",
                    callback_data=f"active_user:{user['telegram_id']}"
                )
            )

    # Паём ба ҳамаи корбарон
    kb.add(
        types.InlineKeyboardButton(
            "📢 Паём ба ҳамаи корбарон",
            callback_data="message_all_users"
        )
    )

    # Қафо ва менюи асосӣ
    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=kb
    )
    
    
# ============================================================
# ACTIVE USER DETAILS
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("active_user:")
)
def active_user_details(call):

    if call.from_user.id != ADMIN_ID:
        return

    user_id = int(
        call.data.split(":")[1]
    )

    with db_lock:
        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE telegram_id=?
        """, (user_id,)).fetchone()

        # Ҳамаи заказҳо
        total = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE user_id=?
        """, (user_id,)).fetchone()[0]

        # Иҷрошуда
        completed = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE user_id=?
            AND status='completed'
        """, (user_id,)).fetchone()[0]

        # Радшуда
        rejected = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE user_id=?
            AND status='rejected'
        """, (user_id,)).fetchone()[0]

        # Дар интизорӣ
        pending = conn.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE user_id=?
            AND status='pending'
        """, (user_id,)).fetchone()[0]

        # UC-и воқеан харидашуда
        total_uc = conn.execute("""
            SELECT COALESCE(SUM(uc), 0)
            FROM orders
            WHERE user_id=?
            AND status='completed'
        """, (user_id,)).fetchone()[0]

        # Маблағи воқеан харҷшуда
        total_amount = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM orders
            WHERE user_id=?
            AND status='completed'
        """, (user_id,)).fetchone()[0]

        conn.close()

    if not user:
        bot.answer_callback_query(
            call.id,
            "Корбар ёфт нашуд."
        )
        return

    username = (
        "@" + html.escape(user["username"])
        if user["username"]
        else "Нест"
    )

    text = (
        "👤 <b>МАЪЛУМОТИ КОРБАР</b>\n\n"

        f"👤 <b>Ном:</b> "
        f"{html.escape(user['first_name'] or 'Беном')}\n"

        f"🔹 <b>Никнейм:</b> "
        f"{username}\n\n"

        f"📦 <b>Ҳамаи заказҳо:</b> "
        f"{total}\n"

        f"🟢 <b>Заказҳои иҷрошуда:</b> "
        f"{completed}\n"

        f"🔴 <b>Заказҳои радшуда:</b> "
        f"{rejected}\n"

        f"🟡 <b>Заказҳои дар интизорӣ:</b> "
        f"{pending}\n\n"

        f"💎 <b>UC-и харидашуда:</b> "
        f"{total_uc} UC\n"

        f"💰 <b>Маблағи харҷшуда:</b> "
        f"{total_amount} сомонӣ"
    )

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "💬 Паём ба корбар",
            callback_data=f"message_user:{user_id}"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="active_users_back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=kb
    )

    bot.answer_callback_query(
        call.id
    )


# ============================================================
# ACTIVE USERS BACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "active_users_back"
)
def active_users_back(call):

    bot.answer_callback_query(
        call.id
    )

    # Боз сохтани рӯйхати корбарон
    fake_message = call.message
    active_users(
        fake_message
    )


# ============================================================
# MESSAGE USER
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("message_user:")
)
def message_user(call):

    if call.from_user.id != ADMIN_ID:
        return

    user_id = int(
        call.data.split(":")[1]
    )

    admin_states[ADMIN_ID] = {
        "state": "message_user",
        "user_id": user_id
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        "✍️ <b>Паёмро барои корбар нависед.</b>\n\n"
        "Матн, акс ё voice фиристода метавонед."
    )


# ============================================================
# SEND MESSAGE TO USER
# ============================================================

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "voice"
    ],
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "message_user"
)
def send_message_user(message):

    data = admin_states[
        ADMIN_ID
    ]

    user_id = data[
        "user_id"
    ]

    try:

        if message.text:

            bot.send_message(
                user_id,

                "📩 <b>Паём аз админ:</b>\n\n"
                f"{html.escape(message.text)}"
            )

        elif message.photo:

            bot.send_photo(
                user_id,
                message.photo[-1].file_id,
                caption="📩 <b>Паём аз админ</b>"
            )

        elif message.voice:

            bot.send_voice(
                user_id,
                message.voice.file_id,
                caption="📩 <b>Паём аз админ</b>"
            )

        bot.send_message(
            ADMIN_ID,
            "✅ Паём ба корбар фиристода шуд.",
            reply_markup=admin_back_home()
        )

    except Exception as e:

        bot.send_message(
            ADMIN_ID,
            "❌ Паём фиристода нашуд."
        )

    admin_states.pop(
        ADMIN_ID,
        None
    )


# ============================================================
# BROADCAST
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "message_all_users"
)
def broadcast(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states[ADMIN_ID] = {
        "state": "broadcast"
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        "📢 <b>ПАЁМ БА ҲАМАИ КОРБАРОН</b>\n\n"
        "Матн, акс ё voice фиристед."
    )


# ============================================================
# DO BROADCAST
# ============================================================

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "voice"
    ],
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "broadcast"
)
def do_broadcast(message):

    with db_lock:

        conn = get_db()

        users = conn.execute(
            "SELECT telegram_id FROM users"
        ).fetchall()

        conn.close()

    success = 0
    failed = 0

    for row in users:

        try:

            user_id = row[
                "telegram_id"
            ]

            if message.text:

                bot.send_message(
                    user_id,
                    f"📢 <b>Паёми админ:</b>\n\n"
                    f"{html.escape(message.text)}"
                )

            elif message.photo:

                bot.send_photo(
                    user_id,
                    message.photo[-1].file_id,
                    caption="📢 <b>Паёми админ</b>"
                )

            elif message.voice:

                bot.send_voice(
                    user_id,
                    message.voice.file_id,
                    caption="📢 <b>Паёми админ</b>"
                )

            success += 1

        except Exception:

            failed += 1

    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.send_message(
        ADMIN_ID,

        "📢 <b>НАТИҶА</b>\n\n"

        f"📤 Муваффақ: {success}\n"
        f"❌ Ноком: {failed}",

        reply_markup=admin_back_home()
    )


# ============================================================
# CONTACT ADMIN - USER
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text == "👨‍💻 Алоқа бо админ"
)
def contact_admin(message):

    if message.from_user.id == ADMIN_ID:

        return

    user_states[
        message.from_user.id
    ] = {
        "state": "contact_admin"
    }

    bot.send_message(
        message.chat.id,

        "👨‍💻 <b>АЛОҚА БО АДМИН</b>\n\n"

        "💬 Паёми худро ҳамин ҷо нависед.\n"
        "Админ ҳатман ба шумо ҷавоб медиҳад.\n\n"

        "Шумо метавонед матн, акс ё паёми овозӣ равон кунед.",

        reply_markup=user_back_home()
    )


# ============================================================
# CONTACT MESSAGE
# ============================================================

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "voice"
    ],
    func=lambda m:
    user_states.get(
        m.from_user.id,
        {}
    ).get("state")
    == "contact_admin"
)
def contact_message(message):

    user_id = message.from_user.id

    user = message.from_user

    name = html.escape(
        user.first_name or "Номаълум"
    )

    username = (
        "@" + html.escape(
            user.username
        )
        if user.username
        else
        "Нест"
    )

    info = (
        "📩 <b>ПАЁМИ НАВ АЗ КОРБАР</b>\n\n"

        f"👤 <b>Ном:</b> {name}\n"
        f"🔹 <b>Никнейм:</b> {username}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n\n"
    )

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "💬 Ҷавоб додан",
            callback_data=f"reply_user:{user_id}"
        )
    )

    try:

        if message.text:

            bot.send_message(
                ADMIN_ID,
                info +
                "📝 <b>Паём:</b>\n" +
                html.escape(message.text),
                reply_markup=kb
            )

        elif message.photo:

            bot.send_photo(
                ADMIN_ID,
                message.photo[-1].file_id,
                caption=info +
                "📷 <b>Корбар акс фиристод.</b>",
                reply_markup=kb
            )

        elif message.voice:

            bot.send_voice(
                ADMIN_ID,
                message.voice.file_id,
                caption=info +
                "🎤 <b>Корбар voice фиристод.</b>",
                reply_markup=kb
            )

        bot.send_message(
            user_id,

            "✅ Паёми шумо ба админ равон карда шуд.\n\n"
            "⏳ Админ ба шумо ҷавоб медиҳад.",

            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    "🏠 Менюи асосӣ",
                    callback_data="home"
                )
            )
        )

        user_states.pop(
            user_id,
            None
        )

    except Exception:

        bot.send_message(
            user_id,
            "❌ Паём фиристода нашуд."
        )


# ============================================================
# ADMIN REPLY TO USER
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("reply_user:")
)
def reply_user(call):

    if call.from_user.id != ADMIN_ID:
        return

    user_id = int(
        call.data.split(":")[1]
    )

    admin_states[ADMIN_ID] = {
        "state": "reply_user",
        "user_id": user_id
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        "✍️ <b>Ҷавоби худро ба корбар равон кунед.</b>\n\n"
        "Матн, акс ё voice мумкин аст."
    )


# ============================================================
# SEND ADMIN REPLY
# ============================================================

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "voice"
    ],
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "reply_user"
)
def send_admin_reply(message):

    user_id = admin_states[
        ADMIN_ID
    ]["user_id"]

    try:

        if message.text:

            bot.send_message(
                user_id,

                "👨‍💻 <b>Ҷавоби админ:</b>\n\n"
                f"{html.escape(message.text)}"
            )

        elif message.photo:

            bot.send_photo(
                user_id,
                message.photo[-1].file_id,
                caption="👨‍💻 <b>Ҷавоби админ</b>"
            )

        elif message.voice:

            bot.send_voice(
                user_id,
                message.voice.file_id,
                caption="👨‍💻 <b>Ҷавоби админ</b>"
            )

        bot.send_message(
            ADMIN_ID,

            "✅ Ҷавоб ба корбар фиристода шуд.",

            reply_markup=admin_back_home()
        )

    except Exception:

        bot.send_message(
            ADMIN_ID,
            "❌ Ҷавоб фиристода нашуд."
        )

    admin_states.pop(
        ADMIN_ID,
        None
    )


# ============================================================
# BONUS SETTINGS
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text == "🎁 Танзими бонус"
)
def bonus_settings(message):

    if message.from_user.id != ADMIN_ID:
        return

    show_bonus_settings(
        ADMIN_ID
    )


def show_bonus_settings(chat_id):

    with db_lock:
        conn = get_db()

        rows = conn.execute("""
            SELECT uc, bonus
            FROM bonus_settings
            ORDER BY uc ASC
        """).fetchall()

        conn.close()

    text = (
        "🎁 <b>ТАНЗИМИ БОНУС</b>\n\n"
        "📋 <b>ҚОИДАҲОИ БОНУС:</b>\n\n"
    )

    for row in rows:
        text += (
            f"💎 <b>{row['uc']} UC</b> → "
            f"🎁 <b>{row['bonus']} бонус</b>\n"
        )

    text += (
        "\n💵 <b>1 бонус = 1 сомонӣ</b>"
    )

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "🔄 Иваз кардани бонус",
            callback_data="bonus_edit"
        )
    )
    
    kb.add(
        types.InlineKeyboardButton(
            "🏆 Рейтинги корбарон",
            callback_data="bonus_ranking"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.send_message(
        chat_id,
        text,
        reply_markup=kb
    )


# ============================================================
# BONUS EDIT
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "bonus_edit"
)
def bonus_edit(call):

    if call.from_user.id != ADMIN_ID:
        return

    with db_lock:
        conn = get_db()

        rows = conn.execute("""
            SELECT uc, bonus
            FROM bonus_settings
            ORDER BY uc ASC
        """).fetchall()

        conn.close()

    kb = types.InlineKeyboardMarkup()

    for row in rows:

        kb.add(
            types.InlineKeyboardButton(
                f"💎 {row['uc']} UC → 🎁 {row['bonus']}",
                callback_data=f"bonus_select:{row['uc']}"
            )
        )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="bonus_settings_back"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        "🔄 <b>ИВАЗ КАРДАНИ БОНУС</b>\n\n"
        "Кадом UC-ро бонусашро иваз кардан мехоҳед?\n\n"
        "Яке аз пакетҳоро интихоб кунед:",

        reply_markup=kb
    )


# ============================================================
# SELECT BONUS UC
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("bonus_select:")
)
def bonus_select(call):

    if call.from_user.id != ADMIN_ID:
        return

    try:
        uc = int(
            call.data.split(":")[1]
        )
    except Exception:

        bot.answer_callback_query(
            call.id,
            "❌ UC нодуруст аст."
        )

        return

    # Сабт мекунем, ки ҳоло аз админ бонуси нав интизорем
    admin_states[ADMIN_ID] = {
        "state": "edit_bonus",
        "uc": uc
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        f"💎 <b>{uc} UC</b> интихоб шуд.\n\n"
        "🎁 <b>Бонуси навро ворид кунед.</b>\n\n"
        "Мисол: <code>10</code>\n\n"
        "⚠️ Танҳо рақам ворид кунед."
    )


# ============================================================
# SAVE NEW BONUS
# ============================================================

@bot.message_handler(
    content_types=["text"],
    func=lambda m:
        m.from_user.id == ADMIN_ID
        and admin_states.get(
            ADMIN_ID,
            {}
        ).get("state") == "edit_bonus"
)
def save_new_bonus(message):

    text = (message.text or "").strip()

    # Танҳо рақам қабул мекунем
    if not text.isdigit():

        bot.send_message(
            ADMIN_ID,
            "❌ Миқдори бонус нодуруст аст.\n\n"
            "Лутфан танҳо рақам ворид кунед.\n"
            "Мисол: 5"
        )

        return

    new_bonus = int(text)

    uc = admin_states.get(
        ADMIN_ID,
        {}
    ).get("uc")

    if uc is None:

        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.send_message(
            ADMIN_ID,
            "❌ Хатогӣ: UC интихоб нашудааст."
        )

        return

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            UPDATE bonus_settings
            SET bonus=?
            WHERE uc=?
            """,
            (
                new_bonus,
                uc
            )
        )

        conn.commit()
        conn.close()

    # Ҳолати интизориро тоза мекунем
    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.send_message(
        ADMIN_ID,

        f"✅ <b>Бонус иваз шуд!</b>\n\n"
        f"💎 {uc} UC → 🎁 {new_bonus} бонус"
    )

    # Танзими бонусро аз нав нишон медиҳем
    show_bonus_settings(
        ADMIN_ID
    )


# ============================================================
# BONUS SETTINGS BACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "bonus_settings_back"
)
def bonus_settings_back(call):

    if call.from_user.id != ADMIN_ID:
        return

    bot.answer_callback_query(
        call.id
    )

    show_bonus_settings(
        ADMIN_ID
    )
    
    
# ============================================================
# BONUS USER RANKING
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "bonus_ranking"
)
def bonus_ranking(call):

    if call.from_user.id != ADMIN_ID:
        return

    with db_lock:
        conn = get_db()

        users = conn.execute("""
            SELECT
                telegram_id,
                first_name,
                username,
                COALESCE(bonus, 0) AS bonus
            FROM users
            WHERE COALESCE(bonus, 0) > 0
            ORDER BY bonus DESC
        """).fetchall()

        conn.close()

    kb = types.InlineKeyboardMarkup()

    if not users:

        text = (
            "🏆 <b>РЕЙТИНГИ КОРБАРОН</b>\n\n"
            "📭 Корбар бо бонус нест."
        )

    else:

        text = (
            "🏆 <b>РЕЙТИНГИ КОРБАРОН</b>\n\n"
            "👤 Корбарро интихоб кунед:\n"
        )

        for i, user in enumerate(users, 1):

            name = user["first_name"] or "Беном"

            if user["username"]:
                name += f" (@{user['username']})"
            kb.add(
                types.InlineKeyboardButton(
                    f"#{i} 👤 {name} — 🎁 {user['bonus']}",
                    callback_data=(
    f"bonus_rank_user:"
    f"{user['telegram_id']}"
)
                )
            )

    kb.add(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="bonus_ranking_back"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.answer_callback_query(call.id)

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=kb
    )

# ============================================================
# BONUS RANKING USER INFO
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("bonus_rank_user:")
)
def bonus_rank_user(call):

    if call.from_user.id != ADMIN_ID:
        return

    user_id = int(
        call.data.split(":")[1]
    )

    with db_lock:
        conn = get_db()

        user = conn.execute("""
            SELECT
                telegram_id,
                first_name,
                username,
                COALESCE(bonus, 0) AS bonus
            FROM users
            WHERE telegram_id=?
        """, (user_id,)).fetchone()

        if user:
            rank = conn.execute("""
                SELECT COUNT(*) + 1
                FROM users
                WHERE COALESCE(bonus, 0) >
                      COALESCE(
                          (
                              SELECT bonus
                              FROM users
                              WHERE telegram_id=?
                          ),
                          0
                      )
            """, (user_id,)).fetchone()[0]
        else:
            rank = None

        conn.close()

    if not user:
        bot.answer_callback_query(
            call.id,
            "❌ Корбар ёфт нашуд."
        )
        return

    name = html.escape(
        user["first_name"] or "Беном"
    )

    username = (
        "@" + html.escape(user["username"])
        if user["username"]
        else "Нест"
    )

    text = (
        "👤 <b>МАЪЛУМОТИ КОРБАР</b>\n\n"
        f"🏆 <b>Рейтинг:</b> #{rank}\n\n"
        f"👤 <b>Ном:</b> {name}\n"
        f"🔹 <b>Никнейм:</b> {username}\n"
        f"🎁 <b>Миқдори бонус:</b> {user['bonus']}"
    )

    kb = types.InlineKeyboardMarkup()

    # ➕ ИЛОВА КАРДАНИ БОНУС
    kb.add(
        types.InlineKeyboardButton(
            "➕ Илова кардани бонус",
            callback_data=f"bonus_add_user:{user_id}"
        )
    )

    # ➖ КАМ КАРДАНИ БОНУС
    kb.add(
        types.InlineKeyboardButton(
            "➖ Кам кардани бонус",
            callback_data=f"bonus_reduce_user:{user_id}"
        )
    )

    # ◀️ БА ҚАФО
    kb.add(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="bonus_ranking_back"
        )
    )

    # 🏠 МЕНЮИ АСОСӢ
    kb.add(
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=kb
    )


# ============================================================
# REDUCE USER BONUS
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("bonus_reduce_user:")
)
def bonus_reduce_user(call):

    if call.from_user.id != ADMIN_ID:
        return

    user_id = int(
        call.data.split(":")[1]
    )

    with db_lock:
        conn = get_db()

        user = conn.execute("""
            SELECT
                first_name,
                username,
                COALESCE(bonus, 0) AS bonus
            FROM users
            WHERE telegram_id=?
        """, (user_id,)).fetchone()

        conn.close()

    if not user:
        bot.answer_callback_query(
            call.id,
            "❌ Корбар ёфт нашуд."
        )
        return

    admin_states[ADMIN_ID] = {
        "state": "reduce_bonus_amount",
        "user_id": user_id
    }

    bot.answer_callback_query(call.id)

    bot.send_message(
        ADMIN_ID,

        f"➖ <b>КАМ КАРДАНИ БОНУС</b>\n\n"
        f"👤 Корбар: "
        f"<b>{html.escape(user['first_name'] or 'Беном')}</b>\n"
        f"🎁 Бонуси ҳозира: "
        f"<b>{user['bonus']}</b>\n\n"
        "✍️ Чӣ қадар бонус кам кардан лозим?\n\n"
        "Мисол: <code>5</code>"
    )

# ============================================================
# REDUCE BONUS AMOUNT
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "reduce_bonus_amount"
)
def reduce_bonus_amount(message):

    try:
        amount = int(
            message.text.strip()
        )

        if amount <= 0:
            raise ValueError

    except:
        bot.send_message(
            ADMIN_ID,
            "❌ Миқдори бонус нодуруст аст.\n\n"
            "Мисол: <code>5</code>"
        )
        return

    user_id = admin_states[
        ADMIN_ID
    ]["user_id"]

    with db_lock:
        conn = get_db()

        row = conn.execute("""
            SELECT
                COALESCE(bonus, 0) AS bonus
            FROM users
            WHERE telegram_id=?
        """, (user_id,)).fetchone()

        conn.close()

    if not row:
        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.send_message(
            ADMIN_ID,
            "❌ Корбар ёфт нашуд."
        )
        return

    current_bonus = row["bonus"]

    if amount > current_bonus:

        bot.send_message(
            ADMIN_ID,

            f"❌ Бонуси корбар кофӣ нест.\n\n"
            f"🎁 Бонуси ҳозира: <b>{current_bonus}</b>\n"
            f"➖ Шумо мехоҳед: <b>{amount}</b>\n\n"
            "Миқдори камшавӣ аз бонуси ҳозира зиёд буда наметавонад."
        )

        return

    admin_states[ADMIN_ID] = {
        "state": "reduce_bonus_reason",
        "user_id": user_id,
        "amount": amount
    }

    bot.send_message(
        ADMIN_ID,

        f"✅ Миқдори камшавӣ: <b>{amount}</b> бонус.\n\n"
        "📝 <b>Сабаби кам кардани бонусро нависед:</b>\n\n"
        "Мисол: <i>Бонус бо сабаби бекор кардани фармоиш кам карда шуд.</i>"
    )
    
# ============================================================
# REDUCE BONUS REASON
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "reduce_bonus_reason"
)
def reduce_bonus_reason(message):

    reason = (message.text or "").strip()

    if not reason:
        bot.send_message(
            ADMIN_ID,
            "❌ Сабаб холӣ буда наметавонад.\n\n"
            "📝 Сабаби кам кардани бонусро нависед:"
        )
        return

    state = admin_states.get(
        ADMIN_ID,
        {}
    )

    user_id = state.get("user_id")
    amount = state.get("amount")

    if not user_id or not amount:
        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.send_message(
            ADMIN_ID,
            "❌ Маълумоти амалиёт ёфт нашуд. Аз нав оғоз кунед."
        )
        return

    with db_lock:
        conn = get_db()

        user = conn.execute("""
            SELECT
                first_name,
                username,
                COALESCE(bonus, 0) AS bonus
            FROM users
            WHERE telegram_id=?
        """, (user_id,)).fetchone()

        if not user:
            conn.close()

            admin_states.pop(
                ADMIN_ID,
                None
            )

            bot.send_message(
                ADMIN_ID,
                "❌ Корбар ёфт нашуд."
            )
            return

        current_bonus = user["bonus"]

        if amount > current_bonus:
            conn.close()

            admin_states.pop(
                ADMIN_ID,
                None
            )

            bot.send_message(
                ADMIN_ID,
                f"❌ Бонуси корбар дигар кофӣ нест.\n\n"
                f"🎁 Бонуси ҳозира: <b>{current_bonus}</b>\n"
                f"➖ Миқдори камшавӣ: <b>{amount}</b>"
            )
            return

        new_bonus = current_bonus - amount

        conn.execute("""
            UPDATE users
            SET bonus=?
            WHERE telegram_id=?
        """, (
            new_bonus,
            user_id
        ))

        conn.commit()
        conn.close()

    admin_states.pop(
        ADMIN_ID,
        None
    )

    # Паём ба корбар
    try:
        bot.send_message(
            user_id,

            f"➖ <b>Аз бонусҳои шумо "
            f"{amount} бонус кам карда шуд.</b>\n\n"
            f"📝 <b>Сабаб:</b> "
            f"{html.escape(reason)}\n\n"
            f"🎁 <b>Бонусҳои боқимонда:</b> "
            f"{new_bonus}"
        )
    except Exception:
        pass

    # Паём ба админ
    bot.send_message(
        ADMIN_ID,

        f"✅ <b>Бонус бомуваффақият кам карда шуд.</b>\n\n"
        f"👤 Корбар: "
        f"<b>{html.escape(user['first_name'] or 'Беном')}</b>\n"
        f"➖ Кам шуд: <b>{amount}</b>\n"
        f"🎁 Боқӣ монд: <b>{new_bonus}</b>\n"
        f"📝 Сабаб: <i>{html.escape(reason)}</i>"
    )
    
# ============================================================
# ADD USER BONUS
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data.startswith("bonus_add_user:")
)
def bonus_add_user(call):

    if call.from_user.id != ADMIN_ID:
        return

    user_id = int(
        call.data.split(":")[1]
    )

    with db_lock:
        conn = get_db()

        user = conn.execute("""
            SELECT
                first_name,
                username,
                COALESCE(bonus, 0) AS bonus
            FROM users
            WHERE telegram_id=?
        """, (user_id,)).fetchone()

        conn.close()

    if not user:
        bot.answer_callback_query(
            call.id,
            "❌ Корбар ёфт нашуд."
        )
        return

    admin_states[ADMIN_ID] = {
        "state": "add_bonus_amount",
        "user_id": user_id
    }

    bot.answer_callback_query(call.id)

    bot.send_message(
        ADMIN_ID,

        f"➕ <b>ИЛОВА КАРДАНИ БОНУС</b>\n\n"
        f"👤 Корбар: "
        f"<b>{html.escape(user['first_name'] or 'Беном')}</b>\n"
        f"🎁 Бонуси ҳозира: "
        f"<b>{user['bonus']}</b>\n\n"
        "✍️ Чӣ қадар бонус илова кардан лозим?\n\n"
        "Мисол: <code>5</code>"
    )


# ============================================================
# ADD BONUS AMOUNT
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "add_bonus_amount"
)
def add_bonus_amount(message):

    try:
        amount = int(
            message.text.strip()
        )

        if amount <= 0:
            raise ValueError

    except:
        bot.send_message(
            ADMIN_ID,
            "❌ Миқдори бонус нодуруст аст.\n\n"
            "Мисол: <code>5</code>"
        )
        return

    user_id = admin_states[
        ADMIN_ID
    ]["user_id"]

    with db_lock:
        conn = get_db()

        row = conn.execute("""
            SELECT
                COALESCE(bonus, 0) AS bonus
            FROM users
            WHERE telegram_id=?
        """, (user_id,)).fetchone()

        conn.close()

    if not row:
        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.send_message(
            ADMIN_ID,
            "❌ Корбар ёфт нашуд."
        )
        return

    admin_states[ADMIN_ID] = {
        "state": "add_bonus_reason",
        "user_id": user_id,
        "amount": amount
    }

    bot.send_message(
        ADMIN_ID,

        f"✅ Миқдори илова: "
        f"<b>{amount}</b> бонус.\n\n"

        "📝 <b>Сабаби илова кардани бонусро нависед:</b>\n\n"

        "Мисол: "
        "<i>Бонус барои хариди зиёд илова карда шуд.</i>"
    )


# ============================================================
# ADD BONUS REASON
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "add_bonus_reason"
)
def add_bonus_reason(message):

    reason = (
        message.text or ""
    ).strip()

    if not reason:

        bot.send_message(
            ADMIN_ID,

            "❌ Сабаб холӣ буда наметавонад.\n\n"
            "📝 Сабаби илова кардани бонусро нависед:"
        )

        return

    state = admin_states.get(
        ADMIN_ID,
        {}
    )

    user_id = state.get(
        "user_id"
    )

    amount = state.get(
        "amount"
    )

    if not user_id or not amount:

        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.send_message(
            ADMIN_ID,
            "❌ Маълумоти амалиёт ёфт нашуд. "
            "Аз нав оғоз кунед."
        )

        return

    with db_lock:

        conn = get_db()

        user = conn.execute("""
            SELECT
                first_name,
                username,
                COALESCE(bonus, 0) AS bonus
            FROM users
            WHERE telegram_id=?
        """, (user_id,)).fetchone()

        if not user:

            conn.close()

            admin_states.pop(
                ADMIN_ID,
                None
            )

            bot.send_message(
                ADMIN_ID,
                "❌ Корбар ёфт нашуд."
            )

            return

        current_bonus = user["bonus"]

        new_bonus = (
            current_bonus + amount
        )

        conn.execute("""
            UPDATE users
            SET bonus=?
            WHERE telegram_id=?
        """, (
            new_bonus,
            user_id
        ))

        conn.commit()
        conn.close()

    admin_states.pop(
        ADMIN_ID,
        None
    )

    # ========================================================
    # ПАЁМ БА КОРБАР
    # ========================================================

    try:

        bot.send_message(
            user_id,

            f"➕ <b>Ба бонусҳои шумо "
            f"{amount} бонус илова карда шуд.</b>\n\n"

            f"📝 <b>Сабаб:</b> "
            f"{html.escape(reason)}\n\n"

            f"🎁 <b>Бонусҳои шумо:</b> "
            f"{new_bonus}"
        )

    except Exception:
        pass

    # ========================================================
    # ПАЁМ БА АДМИН
    # ========================================================

    bot.send_message(
        ADMIN_ID,

        f"✅ <b>Бонус бомуваффақият илова карда шуд.</b>\n\n"

        f"👤 Корбар: "
        f"<b>{html.escape(user['first_name'] or 'Беном')}</b>\n"

        f"➕ Илова шуд: "
        f"<b>{amount}</b>\n"

        f"🎁 Бонуси нав: "
        f"<b>{new_bonus}</b>\n"

        f"📝 Сабаб: "
        f"<i>{html.escape(reason)}</i>"
    )
    
# ============================================================
# BONUS RANKING BACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "bonus_ranking_back"
)
def bonus_ranking_back(call):

    if call.from_user.id != ADMIN_ID:
        return

    bot.answer_callback_query(call.id)

    show_bonus_settings(
        ADMIN_ID
    )
    
# ============================================================
# UC SETTINGS
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text == "💰 Танзими UC"
)
def uc_settings(message):

    if message.from_user.id != ADMIN_ID:
        return

    show_uc_settings(
        ADMIN_ID
    )


def show_uc_settings(chat_id):

    prices = get_prices()

    text = (
        "💰 <b>ТАНЗИМИ UC</b>\n\n"
        "📋 <b>НАРХНОМА:</b>\n\n"
    )

    for uc, price in prices:

        text += (
            f"💎 {uc} UC — "
            f"{price} сомонӣ\n"
        )

    kb = types.InlineKeyboardMarkup()

    kb.add(
        types.InlineKeyboardButton(
            "➕ Илова кардани пакет",
            callback_data="add_package"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "🗑 Нест кардани пакет",
            callback_data="delete_package"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "✏️ Иваз кардани пакет",
            callback_data="edit_package"
        )
    )

    kb.add(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_home"
        )
    )

    bot.send_message(
        chat_id,
        text,
        reply_markup=kb
    )


# ============================================================
# ADD PACKAGE
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "add_package"
)
def add_package(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states[ADMIN_ID] = {
        "state": "add_uc"
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        "➕ <b>ИЛОВА КАРДАНИ ПАКЕТ</b>\n\n"
        "Миқдори UC-ро нависед.\n\n"
        "Мисол: <code>90</code>"
    )


@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "add_uc"
)
def add_uc_admin(message):

    try:

        uc = int(
            message.text.strip()
        )

        if uc <= 0:
            raise ValueError

    except:

        bot.send_message(
            ADMIN_ID,
            "❌ Миқдори UC нодуруст аст."
        )

        return

    if get_price(uc) is not None:

        bot.send_message(
            ADMIN_ID,
            "⚠️ Ин пакет аллакай вуҷуд дорад."
        )

        return

    admin_states[ADMIN_ID] = {
        "state": "add_price",
        "uc": uc
    }

    bot.send_message(
        ADMIN_ID,

        f"✅ <b>{uc} UC</b> қабул шуд.\n\n"
        "💰 Нархи пакетро бо сомонӣ нависед:"
    )


@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "add_price"
)
def add_price_admin(message):

    try:

        price = int(
            message.text.strip()
        )

        if price <= 0:
            raise ValueError

    except:

        bot.send_message(
            ADMIN_ID,
            "❌ Нарх нодуруст аст."
        )

        return

    uc = admin_states[
        ADMIN_ID
    ]["uc"]

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            INSERT INTO prices
            (uc, price)
            VALUES (?, ?)
            """,
            (
                uc,
                price
            )
        )

        conn.commit()
        conn.close()

    admin_states.pop(
        ADMIN_ID,
        None
    )

    text = (
        "✅ <b>Пакет бомуваффақият илова шуд!</b>\n\n"
        f"💎 <b>{uc} UC — {price} сомонӣ</b>\n\n"
        "📋 <b>Нархномаи нав:</b>\n\n"
    )

    for x, p in get_prices():

        text += (
            f"{x} UC — "
            f"{p} сомонӣ\n"
        )

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=admin_back_home()
    )


# ============================================================
# DELETE PACKAGE
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "delete_package"
)
def delete_package(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states[ADMIN_ID] = {
        "state": "delete_uc"
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        "🗑 <b>НЕСТ КАРДАНИ ПАКЕТ</b>\n\n"
        "Миқдори UC-и пакетро нависед.\n\n"
        "Мисол: <code>120</code>"
    )


@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "delete_uc"
)
def delete_uc_admin(message):

    try:

        uc = int(
            message.text.strip()
        )

    except:

        bot.send_message(
            ADMIN_ID,
            "❌ Миқдори UC нодуруст аст."
        )

        return

    price = get_price(
        uc
    )

    if price is None:

        bot.send_message(
            ADMIN_ID,
            "❌ Ин пакет ёфт нашуд."
        )

        return

    admin_states[ADMIN_ID] = {
        "state": "confirm_delete",
        "uc": uc
    }

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "✅ Ҳа, нест кардан",
            callback_data="confirm_delete_yes"
        ),
        types.InlineKeyboardButton(
            "❌ Не",
            callback_data="confirm_delete_no"
        )
    )

    kb.row(
        types.InlineKeyboardButton(
            "◀️ Ба қафо",
            callback_data="admin_uc"
        ),
        types.InlineKeyboardButton(
            "🏠 Менюи асосӣ",
            callback_data="admin_home"
        )
    )

    bot.send_message(
        ADMIN_ID,

        f"🗑 Пакети <b>{uc} UC — "
        f"{price} сомонӣ</b> ёфт шуд.\n\n"
        "Оё мутмаин ҳастед?",

        reply_markup=kb
    )


# ============================================================
# CONFIRM DELETE YES
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "confirm_delete_yes"
)
def confirm_delete_yes(call):

    if call.from_user.id != ADMIN_ID:
        return

    uc = admin_states.get(
        ADMIN_ID,
        {}
    ).get("uc")

    if not uc:

        bot.answer_callback_query(
            call.id
        )

        return

    with db_lock:

        conn = get_db()

        conn.execute(
            "DELETE FROM prices WHERE uc=?",
            (uc,)
        )

        conn.commit()
        conn.close()

    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.answer_callback_query(
        call.id,
        "Пакет нест карда шуд."
    )

    text = (
        f"✅ Пакети <b>{uc} UC</b> "
        "бомуваффақият нест карда шуд.\n\n"

        "📋 <b>Нархномаи нав:</b>\n\n"
    )

    for x, p in get_prices():

        text += (
            f"{x} UC — "
            f"{p} сомонӣ\n"
        )

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=admin_back_home()
    )


# ============================================================
# CONFIRM DELETE NO
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "confirm_delete_no"
)
def confirm_delete_no(call):

    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.answer_callback_query(
        call.id,
        "Бекор шуд."
    )

    show_uc_settings(
        ADMIN_ID
    )


# ============================================================
# EDIT PACKAGE
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "edit_package"
)
def edit_package(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states[ADMIN_ID] = {
        "state": "edit_old_uc"
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        "✏️ <b>ИВАЗ КАРДАНИ ПАКЕТ</b>\n\n"
        "Аввал миқдори UC-и кӯҳнаро нависед.\n\n"
        "Мисол: <code>120</code>"
    )


@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "edit_old_uc"
)
def edit_old_uc(message):

    try:

        old_uc = int(
            message.text.strip()
        )

    except:

        bot.send_message(
            ADMIN_ID,
            "❌ Миқдори UC нодуруст аст."
        )

        return

    old_price = get_price(
        old_uc
    )

    if old_price is None:

        bot.send_message(
            ADMIN_ID,
            "❌ Ин пакет ёфт нашуд."
        )

        return

    admin_states[ADMIN_ID] = {
        "state": "edit_new_uc",
        "old_uc": old_uc,
        "old_price": old_price
    }

    bot.send_message(
        ADMIN_ID,

        f"📦 Пакети кӯҳна:\n\n"
        f"<b>{old_uc} UC — "
        f"{old_price} сомонӣ</b>\n\n"

        "💎 Миқдори нави UC-ро нависед:"
    )


@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "edit_new_uc"
)
def edit_new_uc(message):

    try:

        new_uc = int(
            message.text.strip()
        )

        if new_uc <= 0:
            raise ValueError

    except:

        bot.send_message(
            ADMIN_ID,
            "❌ Миқдори UC нодуруст аст."
        )

        return

    data = admin_states[
        ADMIN_ID
    ]

    if (
        new_uc != data["old_uc"]
        and
        get_price(new_uc) is not None
    ):

        bot.send_message(
            ADMIN_ID,
            "⚠️ Ин UC аллакай вуҷуд дорад."
        )

        return

    data["new_uc"] = new_uc
    data["state"] = "edit_new_price"

    bot.send_message(
        ADMIN_ID,

        f"✅ Миқдори нав: "
        f"<b>{new_uc} UC</b>\n\n"

        f"💰 Нархи нави пакетро нависед:"
    )


@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state")
    == "edit_new_price"
)
def edit_new_price(message):

    try:

        new_price = int(
            message.text.strip()
        )

        if new_price <= 0:
            raise ValueError

    except:

        bot.send_message(
            ADMIN_ID,
            "❌ Нарх нодуруст аст."
        )

        return

    data = admin_states[
        ADMIN_ID
    ]

    with db_lock:

        conn = get_db()

        conn.execute(
            """
            DELETE FROM prices
            WHERE uc=?
            """,
            (
                data["old_uc"],
            )
        )

        conn.execute(
            """
            INSERT OR REPLACE INTO prices
            (uc, price)
            VALUES (?, ?)
            """,
            (
                data["new_uc"],
                new_price
            )
        )

        conn.commit()
        conn.close()

    admin_states.pop(
        ADMIN_ID,
        None
    )

    text = (
        "✅ <b>Пакет бомуваффақият иваз шуд!</b>\n\n"

        f"📦 Пештар: "
        f"{data['old_uc']} UC — "
        f"{data['old_price']} сомонӣ\n"

        f"➡️ Акнун: "
        f"{data['new_uc']} UC — "
        f"{new_price} сомонӣ\n\n"

        "📋 <b>Нархномаи нав:</b>\n\n"
    )

    for x, p in get_prices():

        text += (
            f"{x} UC — "
            f"{p} сомонӣ\n"
        )

    bot.send_message(
        ADMIN_ID,
        text,
        reply_markup=admin_back_home()
    )


# ============================================================
# USER HOME
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "home"
)
def user_home_callback(call):

    user_states.pop(
        call.from_user.id,
        None
    )

    shop_messages.pop(
        call.from_user.id,
        None
    )

    bot.answer_callback_query(
        call.id
    )

    if call.from_user.id == ADMIN_ID:

        bot.send_message(
            ADMIN_ID,

            "👨‍💻 <b>ПАНЕЛИ АДМИН</b>\n\n"
            "🏠 <b>МЕНЮИ АСОСӢ</b>",

            reply_markup=admin_menu()
        )

        return

    bot.send_message(
        call.message.chat.id,

        "🏠 <b>МЕНЮИ АСОСӢ</b>\n\n"
        " 👋 Хуш омадед!\n\n"
        "Лутфан яке аз имкониятҳоро интихоб кунед: 👇",

        reply_markup=main_menu()
    )


# ============================================================
# USER BACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "back"
)
def user_back_callback(call):

    user_states.pop(
        call.from_user.id,
        None
    )

    bot.answer_callback_query(
        call.id
    )

    if call.from_user.id == ADMIN_ID:

        bot.send_message(
            ADMIN_ID,
            "👨‍💻 <b>ПАНЕЛИ АДМИН</b>",
            reply_markup=admin_menu()
        )

        return

    bot.send_message(
        call.message.chat.id,

        "🏠 <b>МЕНЮИ АСОСӢ</b>\n\n"
        "Салом! 👋 Хуш омадед!",

        reply_markup=main_menu()
    )


# ============================================================
# ADMIN HOME
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "admin_home"
)
def admin_home_callback(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        "👨‍💻 <b>ПАНЕЛИ АДМИН</b>\n\n"
        "🏠 <b>МЕНЮИ АСОСӢ</b>",

        reply_markup=admin_menu()
    )


# ============================================================
# ADMIN BACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "admin_back"
)
def admin_back_callback(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        ADMIN_ID,

        "👨‍💻 <b>ПАНЕЛИ АДМИН</b>\n\n"
        "🏠 <b>МЕНЮИ АСОСӢ</b>",

        reply_markup=admin_menu()
    )


# ============================================================
# ADMIN UC CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "admin_uc"
)
def admin_uc_callback(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.answer_callback_query(
        call.id
    )

    show_uc_settings(
        ADMIN_ID
    )


# ============================================================
# ADMIN REVIEWS CALLBACK
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "admin_reviews"
)
def admin_reviews_callback(call):

    if call.from_user.id != ADMIN_ID:
        return

    bot.answer_callback_query(
        call.id
    )

    admin_reviews(
        call.message
    )


# ============================================================
# TEXT HOME
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.text == "🏠 Менюи асосӣ"
)
def text_home(message):

    if message.from_user.id == ADMIN_ID:

        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.send_message(
            message.chat.id,

            "👨‍💻 <b>ПАНЕЛИ АДМИН</b>\n\n"
            "🏠 <b>МЕНЮИ АСОСӢ</b>",

            reply_markup=admin_menu()
        )

    else:

        user_states.pop(
            message.from_user.id,
            None
        )

        bot.send_message(
            message.chat.id,

            "🏠 <b>МЕНЮИ АСОСӢ</b>\n\n"
            "Салом! 👋 Хуш омадед!",

            reply_markup=main_menu()
        )


# ============================================================
# ADMIN DELETE ORDERS — RECEIVE COUNT
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state") == "delete_orders"
)
def receive_delete_orders_count(message):

    text = message.text.strip()

    if not text.isdigit():

        bot.send_message(
            message.chat.id,

            "❌ Танҳо рақам нависед.\n\n"
            "Масалан: <code>5</code>",

            parse_mode="HTML"
        )

        return

    count = int(text)

    if count <= 0:

        bot.send_message(
            message.chat.id,

            "❌ Рақам бояд аз 0 калон бошад.\n\n"
            "Масалан: <code>5</code>",

            parse_mode="HTML"
        )

        return

    # Санҷидани шумораи умумии заказҳо
    with db_lock:

        conn = get_db()

        total_orders = conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        conn.close()

    if total_orders == 0:

        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.send_message(
            message.chat.id,
            "📦 Ҳоло ягон заказ вуҷуд надорад."
        )

        return

    if count > total_orders:

        bot.send_message(
            message.chat.id,

            f"❌ Ҳамагӣ <b>{total_orders}</b> заказ вуҷуд дорад.\n\n"
            f"🔢 Рақами аз <b>1</b> то <b>{total_orders}</b>-ро нависед.",

            parse_mode="HTML"
        )

        return

    # Гирифтани заказҳои охирин
    with db_lock:

        conn = get_db()

        rows = conn.execute(
            """
            SELECT id
            FROM orders
            ORDER BY id DESC
            LIMIT ?
            """,
            (count,)
        ).fetchall()

        conn.close()

    order_ids = [
        row["id"]
        for row in rows
    ]

    # Нигоҳ доштани заказҳо барои тасдиқ
    admin_states[ADMIN_ID] = {
        "state": "delete_orders_confirm",
        "count": count,
        "order_ids": order_ids
    }

    first_id = order_ids[-1]
    last_id = order_ids[0]

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "✅ Ҳа",
            callback_data="confirm_delete_orders"
        ),
        types.InlineKeyboardButton(
            "❌ Не",
            callback_data="cancel_delete_orders"
        )
    )

    bot.send_message(
        message.chat.id,

        "⚠️ <b>Тасдиқи несткунӣ</b>\n\n"

        f"🗑 Нест кардани <b>{count}</b> закази охирин.\n\n"

        f"📦 Аз №{first_id:06d} то №{last_id:06d}\n\n"

        "❗️Танҳо заказҳо нест мешаванд.\n"
        "🔢 Рақамгузорӣ тағйир намеёбад.\n\n"

        "Оё мутмаин ҳастед?",

        parse_mode="HTML",
        reply_markup=kb
    )


# ============================================================
# ADMIN DELETE ORDERS — CONFIRM
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "confirm_delete_orders"
)
def confirm_delete_orders(call):

    if call.from_user.id != ADMIN_ID:
        return

    state = admin_states.get(
        ADMIN_ID,
        {}
    )

    if state.get("state") != "delete_orders_confirm":

        bot.answer_callback_query(
            call.id,
            "❌ Амалиёт ёфт нашуд.",
            show_alert=True
        )

        return

    order_ids = state.get(
        "order_ids",
        []
    )

    if not order_ids:

        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.answer_callback_query(
            call.id,
            "❌ Заказҳо ёфт нашуданд.",
            show_alert=True
        )

        return

    # Нест кардани танҳо заказҳо
    with db_lock:

        conn = get_db()

        placeholders = ",".join(
            ["?"] * len(order_ids)
        )

        conn.execute(
            f"""
            DELETE FROM orders
            WHERE id IN ({placeholders})
            """,
            order_ids
        )

        conn.commit()
        conn.close()

    deleted_count = len(order_ids)

    # Тоза кардани ҳолати админ
    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.answer_callback_query(
        call.id,
        "✅ Заказҳо нест карда шуданд."
    )

    bot.edit_message_text(
        "✅ <b>Заказҳо нест карда шуданд!</b>\n\n"

        f"🗑 Шумораи нестшуда: <b>{deleted_count}</b>\n\n"

        "🔢 Рақамгузории заказҳо тағйир дода нашуд.",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML"
    )


# ============================================================
# ADMIN DELETE ORDERS — CANCEL
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "cancel_delete_orders"
)
def cancel_delete_orders(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.answer_callback_query(
        call.id,
        "❌ Несткунӣ бекор карда шуд."
    )

    bot.edit_message_text(
        "❌ <b>Нест кардани заказҳо бекор карда шуд.</b>",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML"
    )


# ============================================================
# ADMIN DELETE REVIEWS — START
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "admin_delete_reviews"
)
def admin_delete_reviews(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states[ADMIN_ID] = {
        "state": "delete_reviews"
    }

    bot.answer_callback_query(
        call.id
    )

    bot.send_message(
        call.message.chat.id,

        "🗑 <b>НЕСТ КАРДАНИ ОТЗЫВҲО</b>\n\n"
        "Чанд отзыви охиринро нест кунам?\n\n"
        "🔢 Масалан: <code>5</code>",

        parse_mode="HTML"
    )
    
# ============================================================
# ADMIN DELETE REVIEWS — RECEIVE COUNT
# ============================================================

@bot.message_handler(
    func=lambda m:
    m.from_user.id == ADMIN_ID
    and admin_states.get(
        ADMIN_ID,
        {}
    ).get("state") == "delete_reviews"
)
def receive_delete_reviews_count(message):

    text = message.text.strip()

    if not text.isdigit():

        bot.send_message(
            message.chat.id,

            "❌ Танҳо рақам нависед.\n\n"
            "Масалан: <code>5</code>",

            parse_mode="HTML"
        )

        return

    count = int(text)

    if count <= 0:

        bot.send_message(
            message.chat.id,

            "❌ Рақам бояд аз 0 калон бошад.\n\n"
            "Масалан: <code>5</code>",

            parse_mode="HTML"
        )

        return

    # Санҷидани шумораи умумии отзывҳо
    with db_lock:

        conn = get_db()

        total_reviews = conn.execute(
            "SELECT COUNT(*) FROM reviews"
        ).fetchone()[0]

        conn.close()

    if total_reviews == 0:

        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.send_message(
            message.chat.id,
            "⭐ Ҳоло ягон отзыв вуҷуд надорад."
        )

        return

    if count > total_reviews:

        bot.send_message(
            message.chat.id,

            f"❌ Ҳамагӣ <b>{total_reviews}</b> отзыв вуҷуд дорад.\n\n"
            f"🔢 Рақами аз <b>1</b> то <b>{total_reviews}</b>-ро нависед.",

            parse_mode="HTML"
        )

        return

    # Гирифтани отзывҳои охирин
    with db_lock:

        conn = get_db()

        rows = conn.execute(
            """
            SELECT id
            FROM reviews
            ORDER BY id DESC
            LIMIT ?
            """,
            (count,)
        ).fetchall()

        conn.close()

    review_ids = [
        row["id"]
        for row in rows
    ]

    # Нигоҳ доштани отзывҳо барои тасдиқ
    admin_states[ADMIN_ID] = {
        "state": "delete_reviews_confirm",
        "count": count,
        "review_ids": review_ids
    }

    first_id = review_ids[-1]
    last_id = review_ids[0]

    kb = types.InlineKeyboardMarkup()

    kb.row(
        types.InlineKeyboardButton(
            "✅ Ҳа",
            callback_data="confirm_delete_reviews"
        ),
        types.InlineKeyboardButton(
            "❌ Не",
            callback_data="cancel_delete_reviews"
        )
    )

    bot.send_message(
        message.chat.id,

        "⚠️ <b>Тасдиқи несткунӣ</b>\n\n"

        f"🗑 Нест кардани <b>{count}</b> отзыви охирин.\n\n"

        f"⭐ Аз №{first_id:06d} то №{last_id:06d}\n\n"

        "❗️Танҳо отзывҳо нест мешаванд.\n"
        "🔢 Рақамгузорӣ тағйир намеёбад.\n\n"

        "Оё мутмаин ҳастед?",

        parse_mode="HTML",
        reply_markup=kb
    )
    
# ============================================================
# ADMIN DELETE REVIEWS — CONFIRM
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "confirm_delete_reviews"
)
def confirm_delete_reviews(call):

    if call.from_user.id != ADMIN_ID:
        return

    state = admin_states.get(
        ADMIN_ID,
        {}
    )

    if state.get("state") != "delete_reviews_confirm":

        bot.answer_callback_query(
            call.id,
            "❌ Амалиёт ёфт нашуд.",
            show_alert=True
        )

        return

    review_ids = state.get(
        "review_ids",
        []
    )

    if not review_ids:

        admin_states.pop(
            ADMIN_ID,
            None
        )

        bot.answer_callback_query(
            call.id,
            "❌ Отзывҳо ёфт нашуданд.",
            show_alert=True
        )

        return

    # Нест кардани танҳо отзывҳо
    with db_lock:

        conn = get_db()

        placeholders = ",".join(
            ["?"] * len(review_ids)
        )

        conn.execute(
            f"""
            DELETE FROM reviews
            WHERE id IN ({placeholders})
            """,
            review_ids
        )

        conn.commit()
        conn.close()

    deleted_count = len(review_ids)

    # Тоза кардани ҳолати админ
    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.answer_callback_query(
        call.id,
        "✅ Отзывҳо нест карда шуданд."
    )

    bot.edit_message_text(
        "✅ <b>Отзывҳо нест карда шуданд!</b>\n\n"
        f"🗑 Шумораи нестшуда: <b>{deleted_count}</b>\n\n"
        "🔢 Рақамгузории отзывҳо тағйир дода нашуд.",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML"
    )


# ============================================================
# ADMIN DELETE REVIEWS — CANCEL
# ============================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "cancel_delete_reviews"
)
def cancel_delete_reviews(call):

    if call.from_user.id != ADMIN_ID:
        return

    admin_states.pop(
        ADMIN_ID,
        None
    )

    bot.answer_callback_query(
        call.id,
        "❌ Несткунӣ бекор карда шуд."
    )

    bot.edit_message_text(
        "❌ <b>Нест кардани отзывҳо бекор карда шуд.</b>",

        call.message.chat.id,
        call.message.message_id,

        parse_mode="HTML"
    )
    
# ============================================================
# AUTO ADD USERS
# ============================================================

@bot.message_handler(
    func=lambda m: True
)
def auto_add_user(message):

    add_user(
        message.from_user
    )


# ============================================================
# START BOT
# ============================================================

print(
    "========================================"
)

print(
    "ALI UC SHOP BOT"
)

print(
    "Бот оғоз шуд..."
)

print(
    "========================================"
)


# ============================================================
# START WEB SERVER
# ============================================================

web_thread = threading.Thread(
    target=run_web_server,
    daemon=True
)
web_thread.start()


# ============================================================
# START TELEGRAM POLLING
# ============================================================

try:
    # Агар webhook боқӣ монда бошад, аввал онро тоза мекунем.
    bot.delete_webhook(drop_pending_updates=True)
except Exception as e:
    print("WEBHOOK RESET ERROR:", e)


while True:

    try:

        print("Telegram polling оғоз шуд...")

        bot.infinity_polling(
            timeout=60,
            long_polling_timeout=60,
            skip_pending=True
        )

    except Exception as e:

        print(
            "BOT ERROR:",
            e
        )

        # Пешгирӣ аз restart-и хеле зуд ҳангоми хатои Telegram/Network.
        time.sleep(5)
