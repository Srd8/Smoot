import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# إعدادات التسجيل (Logging)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تصفية التوكن (تأكد من وضع التوكن الصحيح الخاص بك هنا بدون روابط خارجية)
BOT_TOKEN = "6997673290:AAF-b9_QQ0MyyXFd8Rqis1cIViccqRq5kjQ"

# تحديد معرف الأدمن الخاص بالبوت
ADMIN_USERNAME = "@njr10r"

# أمر البدء /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    username = f"@{user.username}" if user.username else "مستخدم"
    
    welcome_text = (
        f"👋 أهلاً بك يا {user.first_name} في بوت التحميل الذكي!\n\n"
        "أرسل لي أي رابط فيديو (TikTok, Instagram, Facebook, X, YouTube) "
        "وسأقوم بجلب الفيديو الأصلي لك مباشرة وبأعلى جودة وبدون علامة مائية. 🚀"
    )
    
    # رسالة ترحيبية خاصة إذا كان المستخدم هو الأدمن
    if username.lower() == ADMIN_USERNAME.lower():
        welcome_text += "\n\n👑 مرحباً بك يا مطور البوت! يمكنك استخدام الأمر /admin لعرض خيارات التحكم."
        
    await update.message.reply_text(welcome_text)

# أمر خاص بالأدمن فقط /admin
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    username = f"@{user.username}" if user.username else ""
    
    # التحقق مما إذا كان المستخدم هو الأدمن المعتمد
    if username.lower() != ADMIN_USERNAME.lower():
        await update.message.reply_text("❌ عذراً، هذا الأمر مخصص فقط لأدمن البوت الرسمي.")
        return
        
    await update.message.reply_text(
        f"⚙️ **لوحة تحكم الأدمن ({ADMIN_USERNAME})**\n\n"
        "• البوت يعمل حالياً بنجاح وبدون مشاكل.\n"
        "• يستقبل الروابط من جميع المستخدمين ويحملها بدون علامات مائية."
    )

# دالة مخصصة لتحميل فيديوهات تيك توك بدون علامة مائية
def download_tiktok_without_watermark(tiktok_url, output_path):
    try:
        api_url = f"https://www.tikwm.com/api/?url={tiktok_url}"
        response = requests.get(api_url).json()
        
        if response.get("code") == 0:
            video_url = response["data"]["play"]
            title = response["data"].get("title", "TikTok_Video")
            
            video_data = requests.get(video_url).content
            with open(output_path, 'wb') as f:
                f.write(video_data)
            return True, title
        return False, "لم نتمكن من جلب الفيديو بدون علامة مائية."
    except Exception as e:
        logger.error(f"TikTok API Error: {e}")
        return False, str(e)

# دالة معالجة الروابط والتحميل
async def handle_video_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text
    chat_id = update.message.chat_id
    
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ يرجى إرسال رابط صحيح.")
        return

    status_message = await update.message.reply_text("⏳ جاري فحص الرابط ومعالجته بدون علامة مائية...")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    actual_filename = f"downloads/{chat_id}_video.mp4"
    video_title = "فيديو من وسائل التواصل"

    try:
        if "tiktok.com" in url:
            await status_message.edit_text("📥 جاري تنظيف وتحميل فيديو TikTok بدون علامة مائية...")
            success, result = download_tiktok_without_watermark(url, actual_filename)
            if success:
                video_title = result
            else:
                raise Exception(result)
        
        else:
            await status_message.edit_text("📥 جاري استخراج الفيديو الأصلي بأعلى جودة...")
            ydl_opts = {
                'format': 'best[ext=mp4]/best', 
                'outtmpl': f'downloads/{chat_id}_%(title)s.%(ext)s',
                'restrictfilenames': True,
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                base, _ = os.path.splitext(filename)
                if os.path.exists(filename):
                    actual_filename = filename
                else:
                    for f in os.listdir('downloads'):
                        if f.startswith(os.path.basename(base)):
                            actual_filename = os.path.join('downloads', f)
                            break
                video_title = info.get('title', 'فيديو مترجم')

        await status_message.edit_text("📤 جاري إرسال الفيديو إليك...")
        with open(actual_filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"✨ تم التحميل بنجاح وبدون علامات مائية!\n\n📝: {video_title}"
            )
            
        await status_message.delete()
        if os.path.exists(actual_filename):
            os.remove(actual_filename)

    except Exception as e:
        logger.error(f"Error during processing: {e}")
        await status_message.edit_text("❌ نعتذر، تعذر تحميل هذا الفيديو. تأكد من أن الرابط عام وليس لحساب خاص (Private).")
        if os.path.exists(actual_filename):
            os.remove(actual_filename)

def main() -> None:
    # تعديل طفيف لتهيئة الحروف الكبيرة في البداية لتجنب أخطاء SyntaxError في بعض نسخ بايثون
    application = Application.builder().token(BOT_TOKEN).build()
    
    # تسجيل الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_download))
    
    print("🤖 البوت يعمل الآن وبانتظار الروابط...")
    application.run_polling()

if __name__ == '__main__':
    main()
