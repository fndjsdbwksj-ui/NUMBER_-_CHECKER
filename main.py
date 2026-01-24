import telebot
from telebot import types
from io import BytesIO
import re

# YOUR BOT TOKEN
API_TOKEN = '8493753474:AAGifjXjyimF4GkxjfaIuGTVX9a0mkHXsS0'
bot = telebot.TeleBot(API_TOKEN)

# DICTIONARIES TO STORE SESSION DATA
user_prefixes = {}
user_collected_numbers = {}

def get_main_markup():
    markup = types.InlineKeyboardMarkup()
    btn_gen = types.InlineKeyboardButton("✅ GENERATE FILE", callback_data="generate_file")
    btn_reset = types.InlineKeyboardButton("🔄 START OVER", callback_data="reset_prefix")
    markup.add(btn_gen, btn_reset)
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    user_prefixes.pop(user_id, None)
    user_collected_numbers.pop(user_id, None)

    welcome_text = (
        "<b>🎉 Welcome To BUBALULA BOT 🤖✨</b>\n\n"
        "<b>📥 SEND THE PREFIX(ES) YOU WANT TO FILTER</b>\n"
        "<i>(Example: 01785, 01965)</i>"
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    
    if call.data == "reset_prefix":
        user_prefixes.pop(user_id, None)
        user_collected_numbers.pop(user_id, None)
        bot.answer_callback_query(call.id, "CLEARED")
        bot.send_message(call.message.chat.id, "<b>🔄 SETTINGS RESET. SEND NEW PREFIX(ES).</b>", parse_mode="HTML")

    elif call.data == "generate_file":
        collected = user_collected_numbers.get(user_id, [])
        if not collected:
            bot.answer_callback_query(call.id, "No numbers collected yet!", show_alert=True)
            return

        # Unique and Sorted
        processed = sorted(list(set(collected)))
        result_data = "\n".join(processed)
        
        bio = BytesIO(result_data.encode('utf-8'))
        bio.name = "Filtered_Numbers.txt"

        bot.send_document(
            call.message.chat.id,
            bio,
            caption=f"<b>✅ COMPLETED!\nTOTAL UNIQUE NUMBERS: {len(processed)}</b>",
            parse_mode="HTML",
            reply_markup=get_main_markup()
        )
        # Clear data after generating to prevent duplicates in next batch
        user_collected_numbers[user_id] = []

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'): return

    user_id = message.from_user.id
    text = message.text.strip()

    # STEP 1: SETTING PREFIXES
    if user_id not in user_prefixes or (len(text) < 15 and "\n" not in text):
        raw_prefixes = re.split(r'[ ,]+', text)
        clean_prefixes = [p.replace('+', '').strip() for p in raw_prefixes if p.strip()]
        
        if clean_prefixes:
            user_prefixes[user_id] = clean_prefixes
            user_collected_numbers[user_id] = [] # Reset collection for new prefix set
            bot.reply_to(
                message, 
                f"<b>🎯 PREFIXES SET TO: {', '.join(clean_prefixes)}</b>\n\n"
                f"<b>📥 SEND YOUR LIST(S). YOU CAN SEND MULTIPLE MESSAGES.</b>\n"
                f"<i>When finished, click 'GENERATE FILE' below.</i>",
                parse_mode="HTML"
            )
            return

    # STEP 2: COLLECTING NUMBERS
    target_prefixes = user_prefixes.get(user_id, [])
    lines = text.split('\n')
    count_added = 0

    for num in lines:
        clean_num = num.strip()
        search_num = clean_num.replace('+', '')
        
        match = any(search_num.startswith(pref) for pref in target_prefixes)
        
        if match:
            formatted_num = clean_num if clean_num.startswith('+') else "+" + clean_num
            user_collected_numbers[user_id].append(formatted_num)
            count_added += 1

    bot.reply_to(
        message,
        f"<b>📥 Added {count_added} numbers to the queue.</b>\n"
        f"Current Total: {len(set(user_collected_numbers[user_id]))} unique numbers.\n\n"
        f"<i>Send more lists or click Generate.</i>",
        parse_mode="HTML",
        reply_markup=get_main_markup()
    )

if __name__ == "__main__":
    print("--- SYSTEM STARTING ---")
    bot.infinity_polling()
