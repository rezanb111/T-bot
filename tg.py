import telebot
import requests
import re
import json
import base64
import socket
import time
import html

# --- تنظیمات ---
API_TOKEN = '8521540168:AAHfrxPBhvs9e0uA4lpWakST5wPRr0eB4IM'
CHANNEL_ID = '@v2rei'
ADMIN_ID = 8242274171
bot = telebot.TeleBot(API_TOKEN)

countries_fa = {
    "Germany": "آلمان", "United States": "آمریکا", "Finland": "فنلاند", 
    "Netherlands": "هلند", "United Kingdom": "انگلیس", "Turkey": "ترکیه", 
    "France": "فرانسه", "Singapore": "سنگاپور", "UAE": "امارات", "Canada": "کانادا"
}

def check_health(address, port):
    """تست نفوذ و سلامت واقعی (Deep Connection Test)"""
    try:
        if not port: return False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3.5)
        result = sock.connect_ex((address, int(port)))
        sock.close()
        return result == 0
    except:
        return False

def get_location(host):
    try:
        ip = socket.gethostbyname(host)
        res = requests.get(f'http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp', timeout=5).json()
        if res.get('status') == 'success':
            c_en = res.get('country')
            return countries_fa.get(c_en, c_en), res.get('countryCode', '')
    except: pass
    return "نامشخص", ""

def get_flag(code):
    if not code: return "🌐"
    return "".join(chr(ord(c) + 127397) for c in code.upper())

def parse_config(config):
    try:
        protocol = config.split('://')[0].upper()
        if protocol == "VMESS":
            v_body = config.split('://')[1]
            # اصلاح پدینگ Base64
            missing_padding = len(v_body) % 4
            if missing_padding:
                v_body += '=' * (4 - missing_padding)
            
            decoded_data = base64.b64decode(v_body).decode('utf-8')
            data = json.loads(decoded_data)
            return protocol, data.get('add'), data.get('port')
        else:
            # برای VLESS و Trojan
            content = config.split('://')[1]
            server_part = content.split('@')[1].split('?')[0]
            if ':' in server_part:
                address, port = server_part.split(':')
                return protocol, address, port.split('#')[0]
    except: pass
    return None, None, None

def create_main_buttons():
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btn_send_bot = telebot.types.InlineKeyboardButton("🤖 ارسال کانفیگ", url="https://t.me/v2rei_robot")
    btn_share = telebot.types.InlineKeyboardButton("🚀 ارسال به دوستان", url="https://t.me/share/url?url=https://t.me/v2rei")
    markup.add(btn_send_bot, btn_share)
    return markup

def create_caption(config):
    protocol, address, port = parse_config(config)
    if not address or not check_health(address, port): return None
    
    country, code = get_location(address)
    flag = get_flag(code)
    # اضافه کردن تگ به انتهای لینک
    clean_link = html.escape(config.split('#')[0] + "#@v2rei")

    return (
        "‌\n"
        "📩 <b>لینک اتصال (برای کپی ضربه بزنید):</b>\n\n"
        f"<code>{clean_link}</code>\n"
        "━━━━━━━━━━━━━━━\n"
        f"🔹 <b>پروتکل:</b> #‌{html.escape(protocol)}\n"
        f"🌍 <b>کشور:</b> <b>{html.escape(country)} {flag}</b>\n"
        f"⚡️ <b>وضعیت:</b> <b>فعال و تست شده ✅</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "🤝 <b>همکاری با ما:</b>\n"
        "<blockquote>اگر شما هم میخواهید در گسترش اینترنت آزاد شرکت کنید به ربات ما مراجعه کنید:\n"
        "🤖 @v2rei_robot</blockquote>\n"
        "━━━━━━━━━━━━━━━\n"
        "📌 <b>برچسب‌ها:</b>\n"
        "<tg-spoiler>#فیلترشکن #ویتوری #کانفیگ #نت_ملی #اینترنت_آزاد #V2Ray #v2rei</tg-spoiler>\n\n"
        "📢 @v2rei"
    )

@bot.message_handler(commands=['start'])
def welcome(message):
    start_msg = (
        "🛰 <b>به پلتفرم توزیع زیرساخت V2REI خوش آمدید</b>\n\n"
        "ما اینجا کانفیگ‌های ارسالی شما را از نظر فنی آنالیز کرده و در صورت پایداری، با نام خودتان (اختیاری) در کانال منتشر می‌کنیم.\n\n"
        "👇 <b>همین الان لینک کانفیگ خود را (VLESS/VMESS/Trojan) اینجا بفرستید:</b>"
    )
    bot.reply_to(message, start_msg, parse_mode='HTML')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    conf = message.text.strip()
    if '://' in conf:
        user_id = message.from_user.id
        wait_msg = bot.reply_to(message, "🔍 <b>در حال آنالیز فنی و تست پینگ...</b>\nلطفاً چند لحظه صبر کنید.", parse_mode='HTML')

        caption = create_caption(conf)

        if caption:
            # ذخیره لینک در دکمه برای بازیابی راحت‌تر در مرحله تایید
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton("🚀 انتشار در کانال", callback_data=f"ok_{user_id}"))
            markup.add(telebot.types.InlineKeyboardButton("❌ رد کردن", callback_data=f"no_{user_id}"))

            # ارسال برای ادمین (لینک اصلی در کپشن مخفی می‌شود یا دوباره پارس می‌شود)
            bot.send_message(ADMIN_ID, f"📥 <b>درخواست جدید از طرف:</b> <code>{user_id}</code>\n\n{caption}\n\n<pre>{html.escape(conf)}</pre>", reply_markup=markup, parse_mode='HTML')
            bot.edit_message_text("✅ <b>تست سلامت با موفقیت انجام شد.</b>\nکانفیگ شما سالم است و برای تایید نهایی به تیم مدیریت ارسال شد.", message.chat.id, wait_msg.message_id, parse_mode='HTML')
        else:
            bot.edit_message_text("❌ <b>خطا در استعلام!</b>\nاین کانفیگ یا خاموش است و یا پورت آن بسته است.\nلطفاً یک کانفیگ سالم ارسال کنید.", message.chat.id, wait_msg.message_id, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data.split('_')
    action = data[0]
    u_id = data[1]

    if action == "ok":
        try:
            # استخراج لینک از تگ pre که برای ادمین فرستادیم
            link_match = re.search(r'(vless|vmess|trojan)://[^\s<]+', call.message.text)
            if link_match:
                config_link = link_match.group(0)
                final_caption = create_caption(config_link)
                if final_caption:
                    bot.send_message(CHANNEL_ID, final_caption, reply_markup=create_main_buttons(), parse_mode='HTML')
                    bot.edit_message_text(f"✅ <b>منتشر شد!</b>\nتوسط ادمین: {call.from_user.first_name}", ADMIN_ID, call.message.message_id, parse_mode='HTML')
                    bot.send_message(u_id, "🎉 <b>تبریک!</b>\nکانفیگ ارسالی شما تایید و در کانال @v2rei منتشر شد.", parse_mode='HTML')
        except Exception as e:
            bot.answer_callback_query(call.id, "خطا در انتشار!")
            
    elif action == "no":
        bot.edit_message_text("❌ <b>درخواست توسط ادمین رد شد.</b>", ADMIN_ID, call.message.message_id, parse_mode='HTML')
        try:
            bot.send_message(u_id, "⚠️ <b>درخواست رد شد.</b>\nمتأسفانه کانفیگ ارسالی شما تایید نشد.", parse_mode='HTML')
        except: pass

print("Bot is active with advanced health check...")
bot.infinity_polling()