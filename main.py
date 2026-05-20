import os
import logging
import requests
import wikipedia
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعدادات التسجيل (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# ضبط لغة ويكيبيديا إلى العربية
wikipedia.set_lang("ar")

# التوكن والأدمن
BOT_TOKEN = "6997673290:AAF-b9_QQ0MyyXFd8Rqis1cIViccqRq5kjQ"
ADMIN_USERNAME = "@njr10r"

# الأزرار الرئيسية للتسهيل على المستخدم
MAIN_KEYBOARD = [['📥 تحميل فيديو', '🔍 بحث عن حساب'], ['🎭 معلومات فنان', '👑 الأدمن']]

# أمر البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reply_markup = ReplyKeyboardMarkup(MAIN_KEYBOARD, resize_keyboard=True)
    await update.message.reply_text(
        f"👋 أهلاً بك يا {update.effective_user.first_name} في بوت الخدمات الشامل!\n\n"
        "🌟 **مميزات البوت الحالية:**\n"
        "1️⃣ تحميل الفيديوهات من (TikTok, Instagram, YouTube) بدون علامة مائية.\n"
        "2️⃣ البحث عن الحسابات في إنستغرام وتيك توك عبر اسم المستخدم.\n"
        "3️⃣ جلب تفاصيل الفنانين (العمر، السكن، بداية المسيرة).\n\n"
        "الرجاء اختيار الخدمة من الأزرار بالأسفل 👇",
        reply_markup=reply_markup
    )

# معالجة الأزرار والرسائل النصية
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    chat_id = update.message.chat_id
    user_context = context.user_data.get('action')

    # 1. قائمة الأدمن
    if text == '👑 الأدمن':
        username = f"@{update.effective_user.username}" if update.effective_user.username else ""
        if username.lower() == ADMIN_USERNAME.lower():
            await update.message.reply_text(f"⚙️ لوحة تحكم الأدمن ({ADMIN_USERNAME})\n\n• البوت يعمل بكفاءة عالية والميزات الجديدة مفعّلة!")
        else:
            await update.message.reply_text(f"❌ عذراً، هذا الأمر مخصص فقط لأدمن البوت الرسمي: {ADMIN_USERNAME}")
        return

    # 2. الضغط على زر التحميل
    elif text == '📥 تحميل فيديو':
        context.user_data['action'] = 'download'
        await update.message.reply_text("📥 من فضلك أرسل لي رابط الفيديو الآن (TikTok, Instagram, YouTube...):")
        return

    # 3. الضغط على زر البحث عن حساب
    elif text == '🔍 بحث عن حساب':
        context.user_data['action'] = 'search_user'
        await update.message.reply_text("🔍 من فضلك أرسل اسم المستخدم (Username) المراد البحث عنه (بدون علامة @):")
        return

    # 4. الضغط على زر معلومات فنان
    elif text == '🎭 معلومات فنان':
        context.user_data['action'] = 'artist_info'
        await update.message.reply_text("🎭 من فضلك أرسل اسم الفنان أو الشخصية العامة التي تريد معلومات عنها:")
        return

    # === معالجة المدخلات بناءً على الاختيار السابق ===
    
    # أ. تنفيذ عملية التحميل
    if user_context == 'download' or text.startswith(("http://", "https://")):
        context.user_data['action'] = None # تصفية الحالة
        await download_video_logic(update, text, chat_id)

    # ب. تنفيذ عملية البحث عن الحساب
    elif user_context == 'search_user':
        context.user_data['action'] = None
        username_input = text.strip().replace("@", "")
        status_msg = await update.message.reply_text("⏳ جاري فحص الحسابات على المنصات...")
        
        insta_url = f"https://instagram.com/{username_input}"
        tiktok_url = f"https://www.tiktok.com/@{username_input}"
        
        result_text = (
            f"🔍 **نتائج البحث عن المستخدم:** `@{username_input}`\n\n"
            f"📸 **Instagram:**\n🔗 {insta_url}\n\n"
            f"🎵 **TikTok:**\n🔗 {tiktok_url}\n\n"
            f"ℹ️ اضغط على الروابط أعلاه لزيارة الحسابات مباشرة والتأكد من وجودها."
        )
        await status_msg.edit_text(result_text, parse_mode="Markdown")

    # ج. تنفيذ جلب معلومات الفنانين
    elif user_context == 'artist_info':
        context.user_data['action'] = None
        status_msg = await update.message.reply_text(f"⏳ جاري البحث في قاعدة البيانات عن '{text}'...")
        
        try:
            # البحث عن الصفحة
            search_results = wikipedia.search(text)
            if not search_results:
                await status_msg.edit_text("❌ لم يتم العثور على معلومات حول هذا الفنان. تأكد من كتابة الاسم الصحيح.")
                return
            
            # جلب ملخص الصفحة الأولى
            page = wikipedia.page(search_results[0])
            summary = wikipedia.summary(search_results[0], sentences=5)
            
            info_reply = (
                f"🎭 **المعلومات المستخرجة للفنان: {page.title}**\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"📝 **نبذة عامة:**\n{summary}\n\n"
                f"🔗 **للمزيد من التفاصيل:** [اضغط هنا للقراءة بالكامل]({page.url})"
            )
            await status_msg.edit_text(info_reply, parse_mode="Markdown", disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Wikipedia Error: {e}")
            await status_msg.edit_text("⚠️ حدث خطأ أثناء جلب البيانات أو أن الاسم يحتمل أكثر من شخصية، يرجى كتابة الاسم أكثر دقة (مثال: عادل إمام).")

# دالة تحميل تيك توك المعتمدة
def download_tiktok_without_watermark(tiktok_url, output_path):
    try:
        api_url = f"https://www.tikwm.com/api/?url={tiktok_url}"
        response = requests.get(api_url).json()
        if response.get("code") == 0:
            video_url = response["data"]["play"]
            title = response["data"].get("title", "TikTok_Video")
            with open(output_path, 'wb') as f:
                f.write(requests.get(video_url).content)
            return True, title
        return False, "لم نتمكن من جلب الفيديو بدون علامة مائية."
    except Exception as e:
        return False, str(e)

# منطق تحميل الفيديوهات الأساسي (نفس الميزة السابقة)
async def download_video_logic(update, url, chat_id):
    import yt_dlp
    status_message = await update.message.reply_text("⏳ جاري معالجة رابط الفيديو...")
    if not os.path.exists('downloads'): os.makedirs('downloads')
    actual_filename = f"downloads/{chat_id}_video.mp4"
    video_title = "فيديو وسائل التواصل"
    
    try:
        if "tiktok.com" in url:
            success, result = download_tiktok_without_watermark(url, actual_filename)
            if success: video_title = result
            else: raise Exception(result)
        else:
            ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': f'downloads/{chat_id}_%(title)s.%(ext)s', 'restrictfilenames': True, 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base, _ = os.path.splitext(filename)
                actual_filename = filename if os.path.exists(filename) else os.path.join('downloads', os.listdir('downloads')[0])
                video_title = info.get('title', 'فيديو')

        await status_message.edit_text("📤 جاري إرسال الفيديو...")
        with open(actual_filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file, caption=f"✨ تم التحميل بنجاح!\n\n📝: {video_title}")
        await status_message.delete()
        if os.path.exists(actual_filename): os.remove(actual_filename)
    except Exception as e:
        logger.error(e)
        await status_message.edit_text("❌ تعذر تحميل الفيديو. تأكد من أن الرابط صحيح وعام.")
        if os.path.exists(actual_filename): os.remove(actual_filename)

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    print("🤖 البوت المطور يعمل الآن بنجاح...")
    application.run_polling()

if __name__ == '__main__':
    main()
