import telebot
from telebot import types
from io import BytesIO
import re

# আপনার বট টোকেন এখানে দিন
API_TOKEN = '8493753474:AAGifjXjyimF4GkxjfaIuGTVX9a0mkHXsS0'
bot = telebot.TeleBot(API_TOKEN)

# ডাটা স্টোর করার জন্য ডিকশনারি
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
        "<i>(Example: 017, 018, +88017)</i>"
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    
    if call.data == "reset_prefix":
        user_prefixes.pop(user_id, None)
        user_collected_numbers.pop(user_id, None)
        bot.answer_callback_query(call.id, "All Cleared!")
        bot.send_message(call.message.chat.id, "<b>🔄 SETTINGS RESET. SEND NEW PREFIX(ES).</b>", parse_mode="HTML")

    elif call.data == "generate_file":
        collected = user_collected_numbers.get(user_id, [])
        if not collected:
            bot.answer_callback_query(call.id, "No numbers found with matching prefixes!", show_alert=True)
            return

        # ডুপ্লিকেট রিমুভ এবং সর্টিং
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
        # ফাইল দেওয়ার পর ডাটা ক্লিয়ার হবে যাতে নতুন করে কাজ শুরু করা যায়
        user_collected_numbers[user_id] = []

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/'): return

    user_id = message.from_user.id
    text = message.text.strip()

    # ধাপ ১: প্রিফিক্স সেট করা (যদি আগে থেকে সেট করা না থাকে)
    if user_id not in user_prefixes:
        raw_prefixes = re.split(r'[ ,]+', text)
        clean_prefixes = [p.replace('+', '').strip() for p in raw_prefixes if p.strip()]
        
        if clean_prefixes:
            user_prefixes[user_id] = clean_prefixes
            user_collected_numbers[user_id] = []
            bot.reply_to(
                message, 
                f"<b>🎯 PREFIXES SET TO: {', '.join(clean_prefixes)}</b>\n\n"
                f"<b>📥 NOW SEND YOUR NUMBER LISTS.</b>\n"
                f"<i>You can send multiple messages for big lists.</i>",
                parse_mode="HTML"
            )
            return

    # ধাপ ২: নাম্বার কালেক্ট করা
    target_prefixes = user_prefixes.get(user_id, [])
    # নাম্বার সেপারেটর হিসেবে কমা, স্পেস বা নিউ লাইন হ্যান্ডেল করবে
    lines = re.split(r'[ ,\n]+', text)
    count_added_this_time = 0

    if user_id not in user_collected_numbers:
        user_collected_numbers[user_id] = []

    for num in lines:
        clean_num = num.strip()
        if not clean_num: continue
        
        search_num = clean_num.replace('+', '')
        
        # প্রিফিক্স ম্যাচ চেক
        if any(search_num.startswith(pref) for pref in target_prefixes):
            # ফরমেট ঠিক রাখা
            formatted_num = clean_num if clean_num.startswith('+') else "+" + clean_num
            user_collected_numbers[user_id].append(formatted_num)
            count_added_this_time += 1

    current_total = len(set(user_collected_numbers[user_id]))
    
    bot.reply_to(
        message,
        f"<b>📥 Added {count_added_this_time} numbers from this message.</b>\n"
        f"<b>📊 Total Unique Numbers in Queue: {current_total}</b>\n\n"
        f"<i>Keep sending more or click Generate.</i>",
        parse_mode="HTML",
        reply_markup=get_main_markup()
    )

if __name__ == "__main__":
    print("--- BOT IS RUNNING ---")
    bot.infinity_polling()
