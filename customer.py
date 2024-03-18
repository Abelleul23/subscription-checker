import logging
import queue
from telegram import Update, Bot
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    Updater,
    CallbackContext,
)
from pymongo import MongoClient
from datetime import datetime, timezone
import motor.motor_asyncio
import pymongo



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["telegram"]
collection = db["subscription"]



def add_subscriber(user_id):
    # Add a new subscriber to the database
    collection.update_one({"_id": user_id}, {"$set": {"subscribed": True}}, upsert=True)


def remove_subscriber(user_id):
    # Remove a subscriber from the database
    collection.delete_one({"_id": user_id})


def update_subscription(user_id, status):
    # Update the subscription status of a subscriber in the database
    collection.update_one({"_id": user_id}, {"$set": {"subscribed": status}})


def check_subscription(user_id):
    # Check the subscription status of a subscriber from the database
    subscriber = collection.find_one({"_id": user_id})
    if subscriber:
        return subscriber.get("subscribed", False)
    return False


async def start(update: Update, context: CallbackContext) -> None:
    """Start command handler."""
    await update.message.reply_text(
        "Hi! This bot manages subscriptions. Use /subscribe to start your subscription."
    )
    return ConversationHandler.END


async def subscribe(update: Update, context: CallbackContext) -> None:
    """Subscribe command handler."""
    user_id = update.message.from_user.id
    add_subscriber(user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Successfully subscribed!")


async def unsubscribe(update: Update, context: CallbackContext) -> None:
    """Unsubscribe command handler."""
    user_id = update.message.from_user.id
    remove_subscriber(user_id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Successfully unsubscribed!")


async def check_subscription_status(update: Update, context: CallbackContext) -> None:
    """Check subscription status command handler."""
    user_id = update.message.from_user.id
    is_subscribed = check_subscription(user_id)
    if is_subscribed:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are subscribed!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are not subscribed!")


async def handle_message(update: Update, context: CallbackContext) -> None:
    """Message handler to allow only subscribed members to write in the group."""
    user_id = update.message.from_user.id
    is_subscribed = check_subscription(user_id)
    if not is_subscribed:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)

def main() -> None:
    update_queue = queue.Queue()
    updater = Updater(bot=Bot, update_queue=update_queue)

    start_handler = CommandHandler("start", start)
    subscribe_handler = CommandHandler("subscribe", subscribe)
    unsubscribe_handler = CommandHandler("unsubscribe", unsubscribe)
    check_subscription_handler = CommandHandler("check_subscription", check_subscription_status)
    message_handler = MessageHandler(filters.ALL, handle_message)


    application = Application.builder().token(
        "7010182982:AAF7QT58T_VLlvmNvI1thSLFscNyyd5EEx8").build()


# Add handlers to the application
    application.add_handler(start_handler)
    application.add_handler(subscribe_handler)
    application.add_handler(unsubscribe_handler)
    application.add_handler(check_subscription_handler)
    application.add_handler(message_handler)


    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()