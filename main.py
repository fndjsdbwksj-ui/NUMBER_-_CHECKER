import telebot
import re
from io import BytesIO

# আপনার বট টোকেন
API_TOKEN = '8493753474:AAGifjXjyimF4GkxjfaIuGTVX9a0mkHXsS0'
bot = telebot.TeleBot(API_TOKEN)

# ইউজার প্রিফিক্স স্টোর করার জন্য ডিকশনারি
user_prefixes = {}

def filter_logic(input_text, prefixes):
    """নাম্বার ফিল্টার করার মূল ফাংশন"""
    # কমা, স্পেস বা নিউ লাইন অনুযায়ী ডাটা আলাদা করা
    raw_data = re.split(r'[ ,\n\r\t]+', input_text)
    results = []
    
    # প্রিফিক্স থেকে + সরিয়ে ক্লিন করা যাতে ম্যাচিং সহজ হয়
    clean_prefixes = [p.replace('+', '').strip() for p in prefixes]
    
    for item in raw_data:
        num = item.strip()
        if not num: continue
        
        # নাম্বার থেকে + সরিয়ে চেক করা
        search_num = num.replace('+', '')
        
        if any(search_num.startswith(pref) for pref in clean_prefixes):
            # আউটপুটে সব সময় + ফরম্যাট বজায় রাখা
            final_num = num if num.startswith('+') else "+" + num
            results.append(final_num)
            
    # ডুপ্লিকেট রিমুভ এবং সর্ট করা
    return sorted(list(set(results)))

@bot.message_handler(commands=['start', 'reset'])
def welcome_or_reset(message):
    user_id = message.from_user.id
    user_prefixes.pop(user_id, None)
    
    msg = (
        "<b>🚀 BUBALULA AUTO-FILTER ACTIVE</b>\n\n"
        "<b>1. প্রথমে প্রিফিক্স পাঠান</b> (যেমন: 017, 88018)\n"
        "<b>2. এরপর নাম্বার বা .txt ফাইল পাঠান</b>\n\n"
        "<i>প্রিফিক্স বদলাতে /reset লিখুন।</i>"
    )
    bot.reply_to(message, msg, parse_mode="HTML")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    user_id = message.from_user.id
    
    if user_id not in user_prefixes:
        bot.reply_to(message, "❌ আগে প্রিফিক্স লিখে পাঠান!")
        return

    if message.document.file_name.endswith('.txt'):
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        try:
            content = downloaded.decode('utf-8')
        except UnicodeDecodeError:
            content = downloaded.decode('latin-1')
        
        process_and_send(message, content)
    else:
        bot.reply_to(message, "❌ দুঃখিত, শুধু .txt ফাইল সাপোর্ট করে।")

@bot.message_handler(func=lambda message: True)
def handle_all_text(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # যদি ইউজারের প্রিফিক্স সেট না থাকে, তবে প্রথম মেসেজটিই প্রিফিক্স
    if user_id not in user_prefixes:
        raw_p = re.split(r'[ ,]+', text)
        user_prefixes[user_id] = [p.strip() for p in raw_p if p.strip()]
        bot.reply_to(message, f"✅ প্রিফিক্স সেট হয়েছে: <b>{', '.join(user_prefixes[user_id])}</b>\nএখন নাম্বার বা ফাইল পাঠান।", parse_mode="HTML")
        return

    # প্রিফিক্স সেট থাকলে সরাসরি ফিল্টারিং
    process_and_send(message, text)

def process_and_send(message, data):
    user_id = message.from_user.id
    prefixes = user_prefixes.get(user_id, [])
    
    # প্রসেসিং মেসেজ
    wait_msg = bot.reply_to(message, "⏳ প্রসেসিং চলছে...")
    
    filtered_list = filter_logic(data, prefixes)
    
    if not filtered_list:
        bot.edit_message_text("❌ কোনো নাম্বার ম্যাচ করেনি!", message.chat.id, wait_msg.message_id)
        return

    # আউটপুট ফাইল তৈরি
    output = "\n".join(filtered_list)
    bio = BytesIO(output.encode('utf-8'))
    bio.name = f"Result_{len(filtered_list)}.txt"

    bot.delete_message(message.chat.id, wait_msg.message_id)
    bot.send_document(
        message.chat.id, 
        bio, 
        caption=f"✅ <b>ফিল্টার সম্পন্ন!</b>\n📊 মোট ইউনিক নাম্বার: {len(filtered_list)}",
        parse_mode="HTML"
    )

if __name__ == "__main__":
    print("--- BOT STARTED (NO BUTTON MODE) ---")
    bot.infinity_polling()
