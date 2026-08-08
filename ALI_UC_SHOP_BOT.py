from threading import Thread
from flask import Flask
import telebot
from telebot import types

# --- ВЕБ-СЕРВЕР БАРОИ UPTIMEROBOT ---
app = Flask("")


@app.route("/")
def home():
  return "Бот фаъол аст!"


def run_http():
  app.run(host="0.0.0.0", port=8080)


def keep_alive():
  t = Thread(target=run_http)
  t.start()


# --- НАЗМОТИ БОТ ---
TOKEN = "8660164143:AAGL13-xIC2pln1JKKYiPQagb2dzn6N9hhQ"
ADMIN_CHAT_ID = 6871575684
BANK_CARD = "555050093 \n(Душанбе Сити / Алиф Банк / Бонки Эсхата)"

bot = telebot.TeleBot(TOKEN)

PRICES = {
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
    "8100": "870 сомонӣ",
}

user_data = {}
orders_db = {}
order_counter = 1


# --- ФАРМОНИ СТАРТ ВА ТУГМАИ ОҒОЗ ---
@bot.message_handler(commands=["start"])
def start(message):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  btn = types.KeyboardButton("ОҒОЗ")
  markup.add(btn)
  bot.send_message(
      message.chat.id,
      f"Салом, {message.from_user.first_name}!\nБа боти харидории UC хуш омадед.",
      reply_markup=markup,
  )


@bot.message_handler(func=lambda message: message.text in ["ОҒОЗ", "🛍 Закази нав"])
def handle_start_button(message):
  if message.from_user.id == ADMIN_CHAT_ID:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("📥 Заказҳои нав")
    btn2 = types.KeyboardButton("✅ Заказҳои Иҷрошуда")
    btn3 = types.KeyboardButton("❌ Заказҳои Иҷронашуда")
    btn4 = types.KeyboardButton("📊 Статистика")
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(
        message.chat.id,
        "<b>Хушомадед!</b>\nЛутфан бахшро интихоб кунед:",
        reply_markup=markup,
        parse_mode="HTML",
    )
  else:
    select_uc(message)


# --- ТУГМАИ "ЗАКАЗҲОИ МАН" ---
@bot.message_handler(func=lambda message: message.text == "📦 Заказҳои ман")
def show_my_orders(message):
  user_id = message.from_user.id
  my_orders = [o for o in orders_db.values() if o["user_id"] == user_id]

  if not my_orders:
    bot.send_message(message.chat.id, "Шумо то ҳол ҳеҷ заказе надоред.")
    return

  total = len(my_orders)
  done = sum(1 for o in my_orders if o["status"] == "done")
  rejected = sum(1 for o in my_orders if o["status"] == "rejected")
  pending = sum(1 for o in my_orders if o["status"] == "new")

  text = (
      f"📋 <b>ОМОРИ ЗАКАЗҲОИ ШУМО:</b>\n\n"
      f"📦 <b>Ҷамъи заказҳо:</b> {total}\n"
      f"⏳ <b>Дар интизорӣ:</b> {pending}\n"
      f"✅ <b>Иҷрошуда:</b> {done}\n"
      f"❌ <b>Иҷронашуда:</b> {rejected}"
  )

  bot.send_message(message.chat.id, text, parse_mode="HTML")


# --- РАВАНДИ ХАРИДОРИИ UC ---
def select_uc(message):
  markup = types.InlineKeyboardMarkup(row_width=2)
  btns = [
      types.InlineKeyboardButton(
          f"{uc} UC — {price}", callback_data=f"uc_{uc}"
      )
      for uc, price in PRICES.items()
  ]
  markup.add(*btns)

  bot.send_message(
      message.chat.id,
      "Лутфан, миқдори UC-ро интихоб кунед:",
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("uc_"))
def get_uc_amount(call):
  uc_amount = call.data.split("_")[1]
  price = PRICES.get(uc_amount, "")
  user_data[call.from_user.id] = {"uc": uc_amount, "price": price}

  msg = bot.send_message(
      call.message.chat.id,
      f"Шумо <b>{uc_amount} UC</b>-ро интихоб кардед.\n💰 Нарх: <b>{price}</b>\n\n"
      f"⚠️ <b>ДИҚҚАТ:</b> Лутфан <b>PUBG ID</b>-и худро бодиққат ворид кунед.\n"
      f"Агар ID хато бошад, UC ба аккаунти дигар меравад!",
      parse_mode="HTML",
  )
  bot.register_next_step_handler(msg, process_id)


def process_id(message):
  user_id = message.from_user.id
  pubg_id = message.text.strip()

  if not pubg_id.isdigit():
    msg = bot.send_message(
        message.chat.id,
        "❌ ID бояд танҳо аз рақамҳо иборат бошад! ID-ро дуруст нависед:",
    )
    bot.register_next_step_handler(msg, process_id)
    return

  user_data[user_id]["pubg_id"] = pubg_id
  uc = user_data[user_id]["uc"]
  price = user_data[user_id]["price"]

  text = (
      f"📋 <b>Маълумоти фармоиш:</b>\n\n"
      f"🎮 <b>PUBG ID:</b> <code>{pubg_id}</code>\n"
      f"📦 <b>Заказ:</b> {uc} UC ({price})\n\n"
      f"💳 <b>Реквизит барои пардохт:</b>\n<code>{BANK_CARD}</code>\n\n"
      f"⚠️ Маблағро гузаронед ва <b>акси чек (скриншот)</b>-ро фиристед:"
  )
  msg = bot.send_message(message.chat.id, text, parse_mode="HTML")
  bot.register_next_step_handler(msg, process_receipt)


def process_receipt(message):
  global order_counter
  user_id = message.from_user.id

  if message.content_type != "photo":
    msg = bot.send_message(
        message.chat.id,
        "❌ Лутфан, танҳо <b>акси чек (скриншот)</b>-ро фиристед:",
        parse_mode="HTML",
    )
    bot.register_next_step_handler(msg, process_receipt)
    return

  if user_id in user_data:
    uc_amount = user_data[user_id]["uc"]
    price = user_data[user_id]["price"]
    pubg_id = user_data[user_id]["pubg_id"]
    photo_id = message.photo[-1].file_id

    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "Юзернейм надорад"
    )

    order_id = order_counter
    orders_db[order_id] = {
        "user_id": user_id,
        "username": username,
        "uc": uc_amount,
        "price": price,
        "pubg_id": pubg_id,
        "photo_id": photo_id,
        "status": "new",
    }
    order_counter += 1

    try:
      bot.send_message(
          ADMIN_CHAT_ID,
          f"🔔 <b>Закази нав қабул шуд!</b> (Закази №{order_id})",
          parse_mode="HTML",
      )

      markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
      btn_new = types.KeyboardButton("🛍 Закази нав")
      btn_my = types.KeyboardButton("📦 Заказҳои ман")
      markup.add(btn_new, btn_my)

      bot.send_message(
          message.chat.id,
          "✅ <b>Фармоиш ва чеки шумо қабул шуд!</b>\nЧек санҷида мешавад ва"
          " ба зудӣ UC ирсол мегардад.",
          reply_markup=markup,
          parse_mode="HTML",
      )
    except Exception as e:
      bot.send_message(message.chat.id, f"❌ Хатогӣ ҳангоми фиристодан: {e}")

    del user_data[user_id]


# --- ПАНЕЛИ ИДОРАКУНИИ БОТ ---
@bot.message_handler(func=lambda message: message.text == "📥 Заказҳои нав")
def show_new_orders(message):
  if message.from_user.id != ADMIN_CHAT_ID:
    return

  new_orders = {k: v for k, v in orders_db.items() if v["status"] == "new"}
  if not new_orders:
    bot.send_message(message.chat.id, "Ҳоло ҳеҷ закази нав нест.")
    return

  markup = types.InlineKeyboardMarkup(row_width=1)
  for o_id, o_data in new_orders.items():
    btn = types.InlineKeyboardButton(
        f"📦 Закази №{o_id} — {o_data['uc']} UC ({o_data['pubg_id']})",
        callback_data=f"view_order_{o_id}",
    )
    markup.add(btn)

  bot.send_message(
      message.chat.id,
      "📥 <b>Рӯйхати заказҳои нав:</b>",
      reply_markup=markup,
      parse_mode="HTML",
  )


@bot.message_handler(func=lambda message: message.text == "✅ Заказҳои Иҷрошуда")
def show_done_orders(message):
  if message.from_user.id != ADMIN_CHAT_ID:
    return

  done_orders = {k: v for k, v in orders_db.items() if v["status"] == "done"}
  if not done_orders:
    bot.send_message(message.chat.id, "Ҳеҷ закази иҷрошуда нест.")
    return

  markup = types.InlineKeyboardMarkup(row_width=1)
  for o_id, o_data in done_orders.items():
    btn = types.InlineKeyboardButton(
        f"✅ Закази №{o_id} — {o_data['uc']} UC ({o_data['pubg_id']})",
        callback_data=f"view_order_{o_id}",
    )
    markup.add(btn)

  bot.send_message(
      message.chat.id,
      "✅ <b>Рӯйхати заказҳои иҷрошуда:</b>",
      reply_markup=markup,
      parse_mode="HTML",
  )


@bot.message_handler(
    func=lambda message: message.text == "❌ Заказҳои Иҷронашуда"
)
def show_rejected_orders(message):
  if message.from_user.id != ADMIN_CHAT_ID:
    return

  rejected_orders = {
      k: v for k, v in orders_db.items() if v["status"] == "rejected"
  }
  if not rejected_orders:
    bot.send_message(message.chat.id, "Ҳеҷ закази иҷронашуда нест.")
    return

  markup = types.InlineKeyboardMarkup(row_width=1)
  for o_id, o_data in rejected_orders.items():
    btn = types.InlineKeyboardButton(
        f"❌ Закази №{o_id} — {o_data['uc']} UC ({o_data['pubg_id']})",
        callback_data=f"view_order_{o_id}",
    )
    markup.add(btn)

  bot.send_message(
      message.chat.id,
      "❌ <b>Рӯйхати заказҳои иҷронашуда:</b>",
      reply_markup=markup,
      parse_mode="HTML",
  )


@bot.message_handler(func=lambda message: message.text == "📊 Статистика")
def show_stats(message):
  if message.from_user.id != ADMIN_CHAT_ID:
    return

  pending_count = sum(1 for o in orders_db.values() if o["status"] == "new")
  done_count = sum(1 for o in orders_db.values() if o["status"] == "done")
  rejected_count = sum(
      1 for o in orders_db.values() if o["status"] == "rejected"
  )
  total_count = len(orders_db)

  stats_text = (
      f"📊 <b>АМАЛИЁТ ВА СТАТИСТИКАИ БОТ:</b>\n\n"
      f"⏳ <b>Заказҳои интизорӣ (нав):</b> {pending_count}\n"
      f"✅ <b>Заказҳои иҷрошуда:</b> {done_count}\n"
      f"❌ <b>Заказҳои иҷронашуда (радшуда):</b> {rejected_count}\n"
      f"━━━━━━━━━━━━━━━━━━\n"
      f"📈 <b>Ҷамъи ҳамаи заказҳо:</b> {total_count}"
  )

  bot.send_message(message.chat.id, stats_text, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("view_order_"))
def view_order_details(call):
  order_id = int(call.data.split("_")[2])
  order = orders_db.get(order_id)

  if not order:
    bot.answer_callback_query(call.id, "Заказ ёфт нашуд!")
    return

  status_map = {
      "new": "⏳ Интизорӣ",
      "done": "✅ Иҷро шуд",
      "rejected": "❌ Иҷро нашуд",
  }

  caption = (
      f"📦 <b>ЗАКАЗИ №{order_id}</b>\n\n"
      f"👤 <b>Корбар:</b> {order['username']}\n"
      f"🆔 <b>User ID:</b> <code>{order['user_id']}</code>\n"
      f"🎮 <b>PUBG ID:</b> <code>{order['pubg_id']}</code>\n"
      f"💎 <b>Миқдор:</b> <b>{order['uc']} UC</b>\n"
      f"💰 <b>Сумма:</b> <b>{order['price']}</b>\n"
      f"📊 <b>Статус:</b> {status_map.get(order['status'])}"
  )

  markup = types.InlineKeyboardMarkup()
  btn_done = types.InlineKeyboardButton(
      "1. Иҷро шуд", callback_data=f"act_done_{order_id}"
  )
  btn_reject = types.InlineKeyboardButton(
      "2. Иҷро нашуд", callback_data=f"act_reject_{order_id}"
  )
  btn_back = types.InlineKeyboardButton(
      "3. ⬅️ Ба қафо", callback_data=f"back_list_{order['status']}"
  )

  markup.row(btn_done, btn_reject)
  markup.add(btn_back)

  bot.send_photo(
      call.message.chat.id,
      order["photo_id"],
      caption=caption,
      reply_markup=markup,
      parse_mode="HTML",
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("act_done_"))
def process_order_done(call):
  order_id = int(call.data.split("_")[2])
  order = orders_db.get(order_id)

  if order:
    order["status"] = "done"

    msg_to_user = (
        f"✅ <b>Закази шумо ({order['uc']} UC) иҷро шуд!</b>\n\n"
        f"Лутфан, баҳо ё отзыв гузоред 👇"
    )
    try:
      bot.send_message(order["user_id"], msg_to_user, parse_mode="HTML")
      bot.answer_callback_query(
          call.id, "Паёми тасдиқ ба корбар фиристода шуд!"
      )
    except Exception:
      bot.answer_callback_query(call.id, "Хабар ба корбар нарафт.")

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton(
        "3. ⬅️ Ба қафо", callback_data="back_list_done"
    )
    markup.add(btn_back)

    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=call.message.caption.replace(
            "Статус:</b> ⏳ Интизорӣ", "Статус:</b> ✅ Иҷро шуд"
        ),
        reply_markup=markup,
        parse_mode="HTML",
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("act_reject_")
)
def process_order_reject(call):
  order_id = int(call.data.split("_")[2])
  order = orders_db.get(order_id)

  if order:
    order["status"] = "rejected"

    msg_to_user = f"❌ <b>Закази шумо ({order['uc']} UC) иҷро нашуд!</b>"
    try:
      bot.send_message(order["user_id"], msg_to_user, parse_mode="HTML")
      bot.answer_callback_query(call.id, "Хабар ба корбар фиристода шуд!")
    except Exception:
      bot.answer_callback_query(call.id, "Хабар ба корбар нарафт.")

    markup = types.InlineKeyboardMarkup()
    btn_back = types.InlineKeyboardButton(
        "3. ⬅️ Ба қафо", callback_data="back_list_rejected"
    )
    markup.add(btn_back)

    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=call.message.caption.replace(
            "Статус:</b> ⏳ Интизорӣ", "Статус:</b> ❌ Иҷро нашуд"
        ),
        reply_markup=markup,
        parse_mode="HTML",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("back_list_"))
def back_to_order_list(call):
  status = call.data.split("_")[2]

  if status == "new":
    show_new_orders(call.message)
  elif status == "done":
    show_done_orders(call.message)
  elif status == "rejected":
    show_rejected_orders(call.message)
  else:
    bot.send_message(call.message.chat.id, "Бахш аниқ нашуд.")


# --- ИШОРА ВА ИҶРОИ БОТ ---
if __name__ == "__main__":
  keep_alive()  # Оғози веб-сервер
  print("Бот ба кор даромад...")
  bot.infinity_polling()
