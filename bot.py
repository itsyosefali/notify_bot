import logging
import re
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import Database
from config import BOT_TOKEN

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

class ExamBot:
    def __init__(self):
        self.db = Database()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        welcome_message = """
🎓 مرحباً بك في بوت التذكيرات!

📋 الأوامر:
• /add التاريخ العنوان الوصف
• /list عرض المواعيد  
• /remove رقم حذف موعد
• /help المساعدة

💡 مثال: /add 2024-03-15 امتحان الرياضيات

🔔 سيرسل لك تذكير قبل يوم واحد من كل موعد
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send help information."""
        help_text = """
📚 دليل الاستخدام

🎯 إضافة موعد:
/add التاريخ العنوان الوصف

📅 عرض المواعيد:
/list

🗑️ حذف موعد:
/remove رقم الموعد

💡 أمثلة:
• /add 2024-03-15 امتحان الرياضيات
• /add 2024-03-20 موعد طبيب
• /remove 1

🔔 البوت يذكرك قبل يوم واحد من كل موعد
        """
        await update.message.reply_text(help_text)
    
    async def add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a new event."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Parse command arguments
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ خطأ في الاستخدام!\n\n"
                "📝 الطريقة الصحيحة:\n"
                "/add التاريخ العنوان الوصف\n\n"
                "💡 أمثلة:\n"
                "• /add 2024-03-15 امتحان الرياضيات\n"
                "• /add 2024-03-20 موعد طبيب"
            )
            return
        
        # Extract date, title, and description
        date_str = context.args[0]
        title = context.args[1]
        description = " ".join(context.args[2:]) if len(context.args) > 2 else ""
        
        # Validate date format
        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if event_date < datetime.now().date():
                await update.message.reply_text(
                    "❌ لا يمكن إضافة مواعيد في الماضي!\n"
                    "💡 استخدم تاريخ اليوم أو مستقبلي"
                )
                return
        except ValueError:
            await update.message.reply_text(
                "❌ تنسيق التاريخ غير صحيح!\n"
                "💡 استخدم: YYYY-MM-DD\n"
                "مثال: 2024-03-15"
            )
            return
        
        # Determine if this is a group event (if in a group chat)
        is_group_event = chat_id != user_id
        
        # Add event to database
        event_id = self.db.add_exam(
            user_id=user_id,
            chat_id=chat_id,
            exam_date=date_str,
            title=title,
            description=description,
            is_group_exam=is_group_event
        )
        
        # Send confirmation
        scope = "مجموعة" if is_group_event else "شخصي"
        scope_emoji = "👥" if is_group_event else "👤"
        
        message = f"✅ تم إضافة الموعد بنجاح!\n\n"
        message += f"📅 التاريخ: {date_str}\n"
        message += f"📝 العنوان: {title}\n"
        if description:
            message += f"📄 الوصف: {description}\n"
        message += f"🆔 الرقم: {event_id}\n"
        message += f"{scope_emoji} النطاق: {scope}\n\n"
        message += f"💡 استخدم /list لرؤية جميع مواعيدك"
        
        await update.message.reply_text(message)
    
    async def list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List upcoming events."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if this is a group chat
        is_group = chat_id != user_id
        
        if is_group:
            # In group: show only group events
            group_events = self.db.get_exams_for_group(chat_id)
            
            if not group_events:
                await update.message.reply_text(
                    "📅 لا توجد مواعيد قادمة في المجموعة!\n"
                    "💡 استخدم /add لإضافة موعد جديد"
                )
                return
            
            message = "👥 مواعيد المجموعة:\n\n"
            for i, event in enumerate(group_events, 1):
                message += f"🎯 {i}. {event['title']}\n"
                message += f"📅 {event['exam_date']}\n"
                if event['description']:
                    message += f"📝 {event['description']}\n"
                message += "\n\n"
        else:
            # In private chat: show only personal events
            personal_events = self.db.get_exams_for_user(user_id, chat_id)
            
            if not personal_events:
                await update.message.reply_text(
                    "📅 لا توجد مواعيد قادمة!\n"
                    "💡 استخدم /add لإضافة موعدك الأول"
                )
                return
            
            message = "👤 مواعيدك الشخصية:\n\n"
            for i, event in enumerate(personal_events, 1):
                message += f"🎯 {i}. {event['title']}\n"
                message += f"📅 {event['exam_date']}\n"
                if event['description']:
                    message += f"📝 {event['description']}\n"
                message += "\n\n"
        
        message += "💡 استخدم /remove <رقم> لحذف موعد"
        
        await update.message.reply_text(message)
    
    async def remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove an event by ID."""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "❌ خطأ في الاستخدام!\n"
                "💡 مثال: /remove 1\n"
                "🔍 استخدم /list لرؤية أرقام المواعيد"
            )
            return
        
        try:
            event_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "❌ رقم الموعد غير صحيح!\n"
                "💡 مثال: /remove 1"
            )
            return
        
        # Check if event exists and user owns it
        event = self.db.get_exam_by_id(event_id)
        if not event:
            await update.message.reply_text(
                "❌ لم يتم العثور على الموعد!\n"
                "💡 استخدم /list لرؤية المواعيد المتاحة"
            )
            return
        
        if event['user_id'] != user_id:
            await update.message.reply_text(
                "❌ لا يمكنك حذف مواعيد الآخرين!\n"
                "👤 يمكنك حذف مواعيدك فقط"
            )
            return
        
        # Remove event
        if self.db.remove_exam(event_id, user_id):
            await update.message.reply_text(
                f"✅ تم حذف الموعد بنجاح!\n\n"
                f"📝 العنوان: {event['title']}\n"
                f"📅 التاريخ: {event['exam_date']}\n\n"
                f"💡 استخدم /list لرؤية المواعيد المتبقية"
            )
        else:
            await update.message.reply_text(
                "❌ فشل في حذف الموعد!\n"
                "🔄 حاول مرة أخرى"
            )
    
    async def send_notifications(self, context: ContextTypes.DEFAULT_TYPE):
        """Send notifications for events happening tomorrow."""
        events = self.db.get_exams_for_notification(days_ahead=1)
        
        for event in events:
            try:
                scope_emoji = "👥" if event['is_group_exam'] else "👤"
                scope_text = "مجموعة" if event['is_group_exam'] else "شخصي"
                
                message = f"🔔 تذكير بالموعد!\n\n"
                message += f"📅 غداً: {event['exam_date']}\n"
                message += f"📝 العنوان: {event['title']}\n"
                if event['description']:
                    message += f"📄 الوصف: {event['description']}\n"
                message += f"{scope_emoji} النطاق: {scope_text}\n\n"
                message += f"🎯 لا تنس الاستعداد للموعد!"
                
                await context.bot.send_message(
                    chat_id=event['chat_id'],
                    text=message
                )
                
                logger.info(f"Sent notification for event {event['id']} to chat {event['chat_id']}")
                
            except Exception as e:
                logger.error(f"Failed to send notification for event {event['id']}: {e}")

def main():
    """Start the bot."""
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create bot instance
    exam_bot = ExamBot()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", exam_bot.start))
    application.add_handler(CommandHandler("help", exam_bot.help_command))
    application.add_handler(CommandHandler("add", exam_bot.add))
    application.add_handler(CommandHandler("list", exam_bot.list))
    application.add_handler(CommandHandler("remove", exam_bot.remove))
    
    # Schedule daily notifications
    job_queue = application.job_queue
    job_queue.run_daily(
        exam_bot.send_notifications,
        time=time(hour=9, minute=0),  # 9:00 AM daily
        name="daily_notifications"
    )
    
    # Start the bot
    logger.info("Starting Exam Notification Bot...")
    application.run_polling()

if __name__ == '__main__':
    main()
