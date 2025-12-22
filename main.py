import telebot
from telebot import types
from io import BytesIO
from keep_alive import keep_alive  # <--- ADDED THIS

# Start the web server to keep the bot alive
keep_alive()  # <--- ADDED THIS

# YOUR BOT TOKEN
API_TOKEN = '8493753474:AAGifjXjyimF4GkxjfaIuGTVX9a0mkHXsS0'
bot = telebot.TeleBot(API_TOKEN)

# DICTIONARY TO STORE THE PREFIX CHOICE
user_prefixes = {}

def get_reset_markup():
    """CREATES THE START OVER BUTTON"""
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🔄 START OVER",
                                     callback_data="reset_prefix")
    markup.add(btn)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    user_prefixes.pop(user_id, None)

    welcome_text = (
        "<b>🎉 Welcome To BUBALULA BOT 🤖✨</b>\n\n"
        "<b>💥 Bot Created By @Lohit_69💎</b>\n\n"
        "<b>📥 PLEASE SEND THE PREFIX YOU WANT TO FILTER 🔥 (EXAMPLE: 01785, 01965 )</b>"
    )

    bot.reply_to(message, welcome_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "reset_prefix")
def reset_prefix_callback(call):
    user_id = call.from_user.id
    user_prefixes.pop(user_id, None)
    bot.answer_callback_query(call.id, "CLEARED")
    bot.send_message(call.message.chat.id,
                     "<b>🔄 SETTINGS RESET. PLEASE SEND A NEW PREFIX.</b>",
                     parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    # PREVENT BOT FROM TREATING COMMANDS AS PREFIXES
    if message.text.startswith('/'):
        return

    user_id = message.from_user.id
    text = message.text.strip()

    # STEP 1: SETTING THE PREFIX
    if user_id not in user_prefixes or len(text) < 7:
        prefix = text.replace('+', '').replace(' ', '')
        user_prefixes[user_id] = prefix
        bot.reply_to(
            message, f"<b>🎯 PREFIX SET TO: {prefix}</b>\n\n"
            f"<b>📥 NOW PASTE YOUR NUMBER LIST. I WILL KEEP ONLY NUMBERS STARTING WITH {prefix}.</b>",
            parse_mode="HTML")
        return

    # STEP 2: PROCESSING THE LIST
    target_prefix = user_prefixes.get(user_id)
    lines = text.split('\n')

    processed = [
        "+" + num.strip() for num in lines
        if num.strip().startswith(target_prefix)
    ]

    if processed:
        result_data = "\n".join(processed)
        bio = BytesIO(result_data.encode('utf-8'))
        bio.name = f"Filtered_{target_prefix}.txt"

        bot.send_document(
            message.chat.id,
            bio,
            caption=f"<b>✅ DONE! FOUND {len(processed)} NUMBERS.</b>",
            parse_mode="HTML",
            reply_markup=get_reset_markup())
    else:
        bot.reply_to(
            message,
            f"<b>❌ NO NUMBERS STARTING WITH {target_prefix} WERE FOUND.</b>",
            parse_mode="HTML",
            reply_markup=get_reset_markup())

print("BOT IS RUNNING...")
bot.infinity_polling()