from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
from datetime import datetime
from functools import partial

TOKEN = '7299163597:AAHrtCo08atATkF-iWC7aWDCb_hgfXAEJPY'
TASKS_FILE = 'tasks.json'

# Load tasks from file if exists
def load_tasks():
    try:
        with open(TASKS_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

# Save tasks to file
def save_tasks(tasks):
    with open(TASKS_FILE, 'w') as file:
        json.dump(tasks, file)

tasks = load_tasks()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('سلام! من ربات مدیریت وظایف شما هستم.')

async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    task_text = ' '.join(context.args)
    if not task_text:
        await update.message.reply_text('لطفاً توضیح وظیفه را وارد کنید.')
        return

    chat_id = str(update.message.chat_id)
    if chat_id not in tasks:
        tasks[chat_id] = []

    tasks[chat_id].append({
        'task': task_text,
        'completed': False,
        'priority': 'متوسط'
    })
    save_tasks(tasks)
    await update.message.reply_text(f'وظیفه جدید ثبت شد: {task_text}')

async def view_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    if chat_id not in tasks or not tasks[chat_id]:
        await update.message.reply_text('هیچ وظیفه‌ای ثبت نشده است.')
        return

    response = 'وظایف شما:\n'
    for i, task in enumerate(tasks[chat_id], 1):
        status = '✓' if task['completed'] else '✗'
        priority = task.get('priority', 'متوسط')
        response += f"{i}. {task['task']} [{status}] - {priority}\n"

    await update.message.reply_text(response)

async def update_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    if chat_id not in tasks or not tasks[chat_id]:
        await update.message.reply_text('هیچ وظیفه‌ای برای به‌روزرسانی وجود ندارد.')
        return

    try:
        task_index = int(context.args[0]) - 1
        if task_index < 0 or task_index >= len(tasks[chat_id]):
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text('شماره وظیفه معتبر نیست.')
        return

    tasks[chat_id][task_index]['completed'] = not tasks[chat_id][task_index]['completed']
    save_tasks(tasks)
    await update.message.reply_text(f"وضعیت وظیفه به‌روزرسانی شد: {tasks[chat_id][task_index]['task']}")

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    if chat_id not in tasks or not tasks[chat_id]:
        await update.message.reply_text('هیچ وظیفه‌ای برای یادآوری وجود ندارد.')
        return

    try:
        task_index = int(context.args[0]) - 1
        reminder_time = ' '.join(context.args[1:])
        reminder_datetime = datetime.strptime(reminder_time, '%Y-%m-%d %H:%M')
    except (IndexError, ValueError):
        await update.message.reply_text('فرمت زمان یادآوری صحیح نیست.')
        return

    if task_index < 0 or task_index >= len(tasks[chat_id]):
        await update.message.reply_text('شماره وظیفه معتبر نیست.')
        return

    task = tasks[chat_id][task_index]
    job_name = f'reminder_{chat_id}_{task_index}'

    # Passing required data to the reminder_callback function using partial
    reminder_callback_with_data = partial(reminder_callback, chat_id=chat_id, task_text=task['task'])
    job_time = (reminder_datetime - datetime.now()).total_seconds()

    # Scheduling the reminder job
    job = context.job_queue.run_once(reminder_callback_with_data, job_time, name=job_name)

    await update.message.reply_text(f"یادآوری برای وظیفه تنظیم شد: {task['task']} در {reminder_time}")

async def reminder_callback(context, chat_id, task_text) -> None:
    await context.bot.send_message(chat_id, text=f"یادآوری: {task_text}")

async def set_priority(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    if chat_id not in tasks or not tasks[chat_id]:
        await update.message.reply_text('هیچ وظیفه‌ای برای تنظیم اولویت وجود ندارد.')
        return

    try:
        task_index = int(context.args[0]) - 1
        priority = context.args[1]
        if priority not in ['بالا', 'متوسط', 'پایین']:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text('فرمت اولویت صحیح نیست.')
        return

    if task_index < 0 or task_index >= len(tasks[chat_id][task_index]):
        await update.message.reply_text('شماره وظیفه معتبر نیست.')
        return

    tasks[chat_id][task_index]['priority'] = priority
    save_tasks(tasks)
    await update.message.reply_text(f"اولویت وظیفه به‌روزرسانی شد: {tasks[chat_id][task_index]['task']} - {priority}")

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('newtask', new_task))
    application.add_handler(CommandHandler('viewtasks', view_tasks))
    application.add_handler(CommandHandler('updatetask', update_task))
    application.add_handler(CommandHandler('setreminder', set_reminder))
    application.add_handler(CommandHandler('setpriority', set_priority))

    application.run_polling()

if __name__ == '__main__':
    main()