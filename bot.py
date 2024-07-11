import logging
import asyncio
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler

import consts

# 1 to subscribe, 2 to unsubscribe
command = [1]
bot = Bot(consts.BOT_TOKEN)
loop = asyncio.get_event_loop()

subscriptions = {}
user_messages = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def validate_mac_address(mac: str) -> str:
    mac = mac.replace(":", "").replace("-", "").replace(" ", "").upper()
    if len(mac) != 12:
        return "Invalid MAC address format"
    
    pattern = re.compile('[A-Z0-9]+')
    if not pattern.match(mac):
        return "Invalid MAC address format"

    formatted_mac = '-'.join(mac[i:i+2] for i in range(0, 12, 2))
    return formatted_mac


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("Подписаться", callback_data="1"),
            InlineKeyboardButton("Отписаться", callback_data="2"),
        ],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text("Выберите подписаться или отписаться, и введите MAC устройства:", reply_markup=reply_markup)

def keyboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    logging.info('query.data:', query.data)

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    mac = validate_mac_address(update.message.text)
    if len(mac) != 17:
        await context.bot.send_message(chat_id=chat_id, text=f'Слишком много аргументов, введите 1 MAC адрес')
        return

    if mac not in subscriptions:
        subscriptions[mac] = []
    if chat_id not in subscriptions[mac]:
        subscriptions[mac].append(chat_id)
        await context.bot.send_message(chat_id=chat_id, text=f'Подписан на события от {mac}')
    else:
        await context.bot.send_message(chat_id=chat_id, text=f'Вы и так подписаны на {mac}')


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(update.message.text)
    chat_id = update.message.chat_id
    mac = validate_mac_address(update.message.text)
    if len(mac) != 17:
        await context.bot.send_message(chat_id=chat_id, text=f'Слишком много аргументов, введите 1 MAC адрес')
        return

    if mac in subscriptions and chat_id in subscriptions[mac]:
        subscriptions[mac].remove(chat_id)
        await context.bot.send_message(chat_id=chat_id, text=f'Отписан от событий от {mac}')
    else:
        await context.bot.send_message(chat_id=chat_id, text=f'Вы и так не подписаны на события от {mac}')


async def get_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    match update.message.text:
        case "Подписаться":
            command[0] = 1
        case "Отписаться":
            command[0] = 2
        case _:
            match command[0]:
                case 1: await subscribe(update, context)
                case 2: await unsubscribe(update, context)


async def send_message(chat_id: int, text: str):
    to_start_flag = False
    if (chat_id) not in user_messages:
        user_messages[chat_id] = []
    user_messages[chat_id].append(text)
    if (len(user_messages[chat_id]) == 1):
        to_start_flag = True

    if (to_start_flag):
        await asyncio.sleep(3)
        messages = ""
        for message in user_messages[chat_id]:
            messages += message + '\n\n'
        user_messages[chat_id] = []
        await bot.send_message(chat_id=chat_id, text=messages)


def get_mqtt_message(message):
    mac = message.topic.split('/')[1]
    if mac in subscriptions:
        for chat_id in subscriptions[mac]:
            message = make_message(mac, message.payload)
            loop.create_task(send_message(chat_id, message))


def make_message(mac, payload) -> str:
    return f'Устройство с MAC: {mac}\nСообщение: {str(payload)}'


def start_bot():
    application = ApplicationBuilder().token(consts.BOT_TOKEN).build()
    bot = Bot(consts.BOT_TOKEN)
    loop = asyncio.get_event_loop()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('unsubscribe', unsubscribe))
    application.add_handler(CommandHandler('subscribe', subscribe))
    #application.add_handler(CallbackQueryHandler(keyboard_callback))
    application.add_handler(MessageHandler(filters.TEXT, get_message))
    
    application.run_polling()