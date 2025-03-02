from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
import uuid
import sqlite3
import re

# Create DateBase
conn = sqlite3.connect('music_bot.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, unique_link TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS music
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              sender_id INTEGER,
              recipient_id INTEGER,
              file_id TEXT)''')
conn.commit()

# Function to handle start command
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    if context.args:
        unique_id = context.args[0]
        c.execute("SELECT user_id FROM users WHERE unique_link=?", (unique_id,))
        result = c.fetchone()

        if result:
            recipient_id = result[0]
            if recipient_id == user_id:
                await update.message.reply_text("نمی‌شه که برای خودت آهنگ بفرستی عزیزم ☹️")
                return 0

            # ذخیره sender و recipient در دیتابیس
            c.execute("INSERT OR REPLACE INTO pending_senders (sender_id, recipient_id) VALUES (?, ?)", 
                      (user_id, recipient_id))
            conn.commit()

            recipient_info = await context.bot.get_chat(recipient_id)
            recipient_username = recipient_info.username
            recipient_name = recipient_info.first_name

            await update.message.reply_text(
            "🎵 به ربات موزیک ناشناس خوش اومدی!\n\n"
            f"مثل اینکه می‌خوای به آیدی {f"[@{recipient_username}]"} موزیک بفرستی 😌 \n\n"
            "⚠️ فقط حواست باشه که اینجا فقط میتونی با موزیک ارتباط برقرار کنی!\n")
            await update.message.reply_text("✅ حالا یه موزیک بفرست تا ناشناس براش بفرستیم.")
            return 0
    
# If user start bot without another user's special link
    user_id = update.effective_user.id
    keyboard = [[InlineKeyboardButton("🎵 ارسال موزیک", callback_data='send_music')],
                [InlineKeyboardButton("🔗 ساخت لینک", callback_data='create_link')],
                [InlineKeyboardButton("📎 دریافت لینک", callback_data='get_link')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎵 به ربات موزیک ناشناس خوش اومدی!\n\n"
        "اینجا می‌تونی ناشناس برای هرکسی که می‌خوای موزیک بفرستی 😍\n\n"
        "یکی از گزینه‌ها رو انتخاب کن:", reply_markup=reply_markup)

# Function to handle user's choice button
async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'send_music':
        await query.message.reply_text("لینک اونی که می‌خوای براش موزیک بفرستید رو بفرست برامون 😍.")
        context.user_data['awaiting_recipient'] = True
    
    if query.data == 'create_link':
        c.execute("SELECT unique_link FROM users WHERE user_id=?", (user_id,))
        result = c.fetchone()
        
        if not result:
            unique_id = str(uuid.uuid4())
            unique_link = f"https://t.me/tekeMusicbot?start={unique_id}"
            c.execute("INSERT INTO users VALUES (?, ?)", (user_id, unique_id))
            conn.commit()
        else:
            unique_id = result[0]
            unique_link = f"https://t.me/tekeMusicbot?start={unique_id}"
        
        await query.message.reply_text("به جمع ما خوش اومدی!\n\n"
            "این لینکی که ساختیم برات رو بفرست برای رفیقات تا برات آهنگای خوشگل بفرستن 😉\n"
            f"🔗 اینم از لینک مخصوص خودت:\n {unique_link}")

    elif query.data == 'get_link':
        c.execute("SELECT unique_link FROM users WHERE user_id=?", (user_id,))
        result = c.fetchone()
        
        if result:
            unique_link = f"https://t.me/tekeMusicbot?start={result[0]}"
            await query.message.reply_text("ای وای انگاری لینک موزیک مخصوص خودت رو یادت رفته ☹️\n"
                "اصلا اشکال نداره و نگران نباش. بفرما اینم از لینک مخصوصت😍: \n"
                f"{unique_link}")
        else:
            await query.message.reply_text("اوپس انگاری هنوز عضو خانواده ما نشدی! 😢 \n"
                "اشکالی نداره اصلا. روی گزینه ساخت لینک بزن تا عضو جدید خانواده‌مون بشی 😉")

# Function to get another user's link and save it to send music
async def receive_recipient_by_bot_link(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message_text = update.message.text

    match = re.search(r"https://t\.me/tekeMusicbot\?start=([a-zA-Z0-9\-]+)", message_text)
    
    if not match:
        await update.message.reply_text("⚠️ اوپس! انگاری لینکی که فرستادی نامعتبره! یه لینک معتبر برامون بفرست.")
        return

    unique_id = match.group(1)

    c.execute("SELECT user_id FROM users WHERE unique_link=?", (unique_id,))
    result = c.fetchone()

    if result:
        recipient_id = result[0]
        if recipient_id == user_id:
            await update.message.reply_text("نمی‌شه که برای خودت آهنگ بفرستی عزیزم ☹️")
            return

        c.execute("INSERT OR REPLACE INTO pending_senders (sender_id, recipient_id) VALUES (?, ?)", 
                  (user_id, recipient_id))
        conn.commit()

        recipient_info = await context.bot.get_chat(recipient_id)
        recipient_username = recipient_info.username
        recipient_name = recipient_info.first_name

        await update.message.reply_text(
            f"مثل اینکه می‌خوای به آیدی {f"[@{recipient_username}]"} موزیک بفرستی 😌 \n\n"
            "⚠️ فقط حواست باشه که اینجا فقط میتونی با موزیک ارتباط برقرار کنی!\n"
            "✅ حالا یه موزیک بفرست تا ناشناس براش بفرستیم."
        )
    else:
        await update.message.reply_text("⚠️ لینک نامعتبر است! لطفا یک لینک معتبر ارسال کنید.")

# Function to send the music
async def music_sender(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    if update.message.audio:
        c.execute("SELECT recipient_id FROM pending_senders WHERE sender_id=?", (user_id,))
        result = c.fetchone()

        if result:
            recipient_id = result[0]
            file_id = update.message.audio.file_id

            recipient_info = await context.bot.get_chat(recipient_id)
            recipient_username = recipient_info.username
            recipient_name = recipient_info.first_name

            c.execute("INSERT INTO music (sender_id, recipient_id, file_id) VALUES (?, ?, ?)",
                     (user_id, recipient_id, file_id))
            conn.commit()

            await context.bot.send_audio(
                chat_id=recipient_id,
                audio=file_id,
                caption="🎧 😍 سلام سلام! یکی از دوستات برات یه آهنگ جدید فرستاده!"
            )
            if recipient_username:
                    recipient_text = f"[@{recipient_username}](https://t.me/{recipient_username})"
            else:
                    recipient_text = f"`{recipient_name}`"

            await update.message.reply_text( f"✅ موزیکت رو با موفقیت بهش فرستادیم {recipient_text}", parse_mode="Markdown")

            c.execute("DELETE FROM pending_senders WHERE sender_id=?", (user_id,))
            conn.commit()
        else:
            await update.message.reply_text("⚠️ اول لینک اختصاصی اونی که می‌خوای موزیک براش بفرستی برامون بفرست.")
    else:
        await update.message.reply_text("❌ فقط باید فایل موزیک برامون بفرستی!")
    
# Function to handle invalid user's messages
async def invalid_message(update: Update, context: CallbackContext):
    await update.message.reply_text("اوپس! انگار یه چیز اشتباهی فرستادی ☹️")

# Main function
def main():
    TOKEN = "Your Bot TOken"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.AUDIO, music_sender))
    app.add_handler(MessageHandler(filters.Regex(r"^https://t\.me/tekeMusicbot\?start=[\w\d\-]+$"), receive_recipient_by_bot_link))
    app.add_handler(MessageHandler(~filters.COMMAND & ~filters.AUDIO & ~filters.Regex(r"^https://t\.me/tekeMusicbot\?start=[\w\d\-]+$") , invalid_message))
    
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
