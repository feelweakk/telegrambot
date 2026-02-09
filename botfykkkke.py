import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8527392204:AAHnEJCzj2d5iFyxbBFP5o1xHkP-5Oire6Y"

# Подключение к базе данных
conn = sqlite3.connect('tasks.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_text TEXT,
        done INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        habit_text TEXT,
        streak INTEGER DEFAULT 0,
        last_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
''')
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user.id, user.username))
    conn.commit()
    
    keyboard = [
        [InlineKeyboardButton("📝 Мои задачи", callback_data='tasks')],
        [InlineKeyboardButton("🔥 Мои привычки", callback_data='habits')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats')],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! Я TaskMaster — твой помощник по задачам и привычкам.\n\n"
        "Выбери действие:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == 'tasks':
        cursor.execute("SELECT id, task_text, done FROM tasks WHERE user_id = ?", (user_id,))
        tasks = cursor.fetchall()
        
        if not tasks:
            text = "📝 Список задач пуст.\n\nОтправь мне текст задачи, чтобы добавить её!"
        else:
            text = "📝 Твои задачи:\n"
            for task_id, task_text, done in tasks:
                status = "✅" if done else "⏳"
                text += f"\n{task_id}. {status} {task_text}"
            text += "\n\nОтправь текст новой задачи или напиши 'Удалить [номер]'"
        
        await query.edit_message_text(text)
    
    elif query.data == 'habits':
        cursor.execute("SELECT id, habit_text, streak FROM habits WHERE user_id = ?", (user_id,))
        habits = cursor.fetchall()
        
        if not habits:
            text = "🔥 У тебя пока нет привычек.\n\nНапиши 'Привычка [название]', чтобы добавить!"
        else:
            text = "🔥 Твои привычки:\n"
            for habit_id, habit_text, streak in habits:
                text += f"\n{habit_id}. {habit_text} — {streak} дней подряд"
            text += "\n\nНапиши 'Отметить [номер]', чтобы отметить выполнение сегодня."
        
        await query.edit_message_text(text)
    
    elif query.data == 'stats':
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND done = 1", (user_id,))
        done_tasks = cursor.fetchone()[0]
        
        cursor.execute("SELECT habit_text, streak FROM habits WHERE user_id = ?", (user_id,))
        habits = cursor.fetchall()
        
        text = f"📊 Твоя статистика:\n\n✅ Выполнено задач: {done_tasks}\n\n🔥 Привычки:\n"
        if habits:
            for habit_text, streak in habits:
                text += f"- {habit_text}: {streak} дней подряд\n"
        else:
            text += "Пока нет привычек"
        
        await query.edit_message_text(text)
    
    elif query.data == 'help':
        await query.edit_message_text(
            "ℹ️ Помощь по командам:\n\n"
            "• Нажми '📝 Мои задачи' — чтобы увидеть список задач\n"
            "• Просто отправь текст — чтобы добавить задачу\n"
            "• Напиши 'Удалить 1' — чтобы удалить задачу №1\n"
            "• Напиши 'Привычка читать' — чтобы добавить привычку\n"
            "• Напиши 'Отметить 1' — отметить привычку №1 выполненной сегодня\n"
            "• Нажми '📊 Статистика' — увидеть свой прогресс"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()
    
    if text and not text.startswith(('удалить', 'привычка', 'отметить')):
        cursor.execute("INSERT INTO tasks (user_id, task_text) VALUES (?, ?)", (user_id, update.message.text))
        conn.commit()
        await update.message.reply_text(f"✅ Задача добавлена: {update.message.text}")
    
    elif text.startswith('удалить'):
        try:
            task_id = int(text.split()[1])
            cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
            conn.commit()
            await update.message.reply_text(f"🗑 Задача {task_id} удалена")
        except:
            await update.message.reply_text("Используй: Удалить [номер]")
    
    elif text.startswith('привычка'):
        habit_name = text.replace('привычка', '').strip()
        if habit_name:
            cursor.execute("INSERT INTO habits (user_id, habit_text) VALUES (?, ?)", (user_id, habit_name))
            conn.commit()
            await update.message.reply_text(f"🔥 Привычка добавлена: {habit_name}")
    
    elif text.startswith('отметить'):
        try:
            habit_id = int(text.split()[1])
            cursor.execute("UPDATE habits SET streak = streak + 1 WHERE id = ? AND user_id = ?", (habit_id, user_id))
            conn.commit()
            await update.message.reply_text(f"🎉 Привычка отмечена! Счётчик увеличен.")
        except:
            await update.message.reply_text("Используй: Отметить [номер]")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен! Нажмите Ctrl+C для остановки")
    app.run_polling()

if __name__ == "__main__":
    main()