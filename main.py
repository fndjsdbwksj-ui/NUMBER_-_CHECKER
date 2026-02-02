import telebot
from telebot import types
import re
from io import BytesIO

# আপনার বট টোকেন
API_TOKEN = '8493753474:AAGifjXjyimF4GkxjfaIuGTVX9a0mkHXsS0'
bot = telebot.TeleBot(API_TOKEN)

# ডাটা স্টোর করার জন্য ডিকশনারি
user_prefixes = {}
session_results = {} # প্রতিটা ছোট রেজাল্ট এখানে জমা থাকবে কম্বাইন করার জন্য

def get_combine_markup():
    markup = types.InlineKeyboardMarkup()
    btn_combine = types.InlineKeyboardButton("📥 COMBINE ALL FILES", callback_data="combine_now")
    btn_reset = types.InlineKeyboardButton("🔄 RESET ALL", callback_data="reset_all")
    markup.add(btn_combine)
    markup.add(btn_reset)
    return markup

def filter_logic(input_text, prefixes):
    raw_data = re.split(r'[ ,\n\r\t]+', input_text)
    results = []
    clean_prefixes = [p.replace('+', '').strip() for p in prefixes]
    
    for item in raw_data:
        num = item.strip()
        if not num: continue
        search_num = num.replace('+', '')
        if any(search_num.startswith(pref) for pref in clean_prefixes):
            final_num = num if num.startswith('+') else "+" + num
            results.append(final_num)
    return sorted(list(set(results)))

@bot.message_handler(commands=['start', 'reset'])
def welcome(message):
    user_id = message.from_user.id
    user_prefixes.pop(user_id, None)
    session_results.pop(user_id, None)
    
    msg = (
        "<b>🚀 BUBALULA PRO FILTER & COMBINER</b>\n\n"
        "<b>1. প্রথমে প্রিফিক্স পাঠান।</b>\n"
        "<b>2. এরপর নাম্বার বা .txt ফাইল পাঠান।</b>\n\n"
        "<i>বট প্রতিবার ফাইল দিবে এবং শেষে সব ফাইল এক করার অপশন দিবে।</i>"
    )
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    
    if call.data == "combine_now":
        all_data = session_results.get(user_id, [])
        if not all_data:
            bot.answer_callback_query(call.id, "No data to combine!", show_alert=True)
            return
        
        # সব ফাইল থেকে ইউনিক নাম্বার বের করা
        final_unique = sorted(list(set(all_data)))
        output = "\n".join(final_unique)
        bio = BytesIO(output.encode('utf-8'))
        bio.name = f"Final_Master_File_{len(final_unique)}.txt"
        
        bot.send_document(
            call.message.chat.id, 
            bio, 
            caption=f"✅ <b>MASTER FILE GENERATED!</b>\n📊 Total Unique Numbers: {len(final_unique)}",
            parse_mode="HTML"
        )
        bot.answer_callback_query(call.id, "Combined Successfully!")

    elif call.data == "reset_all":
        user_prefixes.pop(user_id, None)
        session_results.pop(user_id, None)
        bot.edit_message_text("🔄 সব ডাটা ক্লিয়ার করা হয়েছে। নতুন প্রিফিক্স পাঠান।", call.message.chat.id, call.message.message_id)

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    user_id = message.from_user.id
    if user_id not in user_prefixes:
        bot.reply_to(message, "❌ আগে প্রিফিক্স পাঠান!")
        return

    if message.document.file_name.endswith('.txt'):
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        try: content = downloaded.decode('utf-8')
        except: content = downloaded.decode('latin-1')
        process_and_send(message, content)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    text = message.text.strip()

    if user_id not in user_prefixes:
        raw_p = re.split(r'[ ,]+', text)
        user_prefixes[user_id] = [p.strip() for p in raw_p if p.strip()]
        session_results[user_id] = []
        bot.reply_to(message, f"✅ প্রিফিক্স সেট: <b>{', '.join(user_prefixes[user_id])}</b>\nএখন নাম্বার বা ফাইল পাঠান।", parse_mode="HTML")
        return

    process_and_send(message, text)

def process_and_send(message, data):
    user_id = message.from_user.id
    prefixes = user_prefixes.get(user_id, [])
    
    filtered = filter_logic(data, prefixes)
    
    if not filtered:
        bot.reply_to(message, "❌ এই প্রিফিক্সের সাথে কোনো নাম্বার মেলেনি।")
        return

    # সেশন স্টোরেজে জমা রাখা (কম্বাইন করার জন্য)
    session_results[user_id].extend(filtered)
    
    # বর্তমান মেসেজের জন্য ফাইল তৈরি
    output = "\n".join(filtered)
    bio = BytesIO(output.encode('utf-8'))
    bio.name = f"Result_{len(filtered)}.txt"

    bot.send_document(
        message.chat.id, 
        bio, 
        caption=f"📄 <b>File generated for this batch.</b>\n📊 Numbers: {len(filtered)}\n\n<i>সব ফাইল একসাথে পেতে নিচের বাটনে ক্লিক করুন।</i>",
        parse_mode="HTML",
        reply_markup=get_combine_markup()
    )

if __name__ == "__main__":
    print("--- BOT RUNNING WITH COMBINE BUTTON ---")
    bot.infinity_polling()
