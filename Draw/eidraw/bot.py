import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import logging

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your bot token and app URL
TOKEN = "7641412543:AAF1ozs7Iux0kPMU6bMvRegCb7wF3Q_S5k0"  # e.g., "123456:ABC-DEF"
BASE_URL = "http://yourapp.com"  # Update with your deployed app URL

def start(update, context):
    """Handle /start command with group UUID."""
    chat_id = update.message.chat_id
    if not context.args:
        update.message.reply_text("Please use the link shared by the organizer (e.g., /start <group_uuid>).")
        return
    
    group_uuid = context.args[0]
    try:
        response = requests.get(f"{BASE_URL}/api/group/{group_uuid}/")
        if response.status_code == 200:
            context.user_data['group_uuid'] = group_uuid
            context.user_data['telegram_id'] = str(chat_id)
            update.message.reply_text(
                "Welcome to the Eid Secret Gift Exchange!\n"
                "Please provide your details in this format: Name, Age, Gender (Male/Female/Other), Wishlist\n"
                "Example: John, 30, Male, Toy car"
            )
        else:
            update.message.reply_text("Invalid group link. Please check with the organizer.")
    except requests.RequestException as e:
        logger.error(f"Error checking group: {e}")
        update.message.reply_text("Something went wrong. Try again later.")

def register(update, context):
    """Handle registration message."""
    if 'group_uuid' not in context.user_data:
        update.message.reply_text("Please start with the group link first using /start <group_uuid>.")
        return
    
    group_uuid = context.user_data['group_uuid']
    telegram_id = context.user_data['telegram_id']
    
    try:
        text = update.message.text.split(',')
        if len(text) < 4:
            raise ValueError("Please provide all details: Name, Age, Gender, Wishlist")
        
        name, age, gender, wishlist = [t.strip() for t in text]
        age = int(age)
        gender = gender.capitalize()
        if gender not in ['Male', 'Female', 'Other']:
            raise ValueError("Gender must be Male, Female, or Other")
        
        data = {
            'telegram_id': telegram_id,
            'name': name,
            'age': age,
            'gender': gender,
            'wishlist': wishlist,
            'group_uuid': group_uuid
        }
        response = requests.post(f"{BASE_URL}/api/register/", json=data)
        if response.status_code == 201:
            update.message.reply_text(f"Successfully registered {name}! Use /draw when the organizer enables it.")
        else:
            error_msg = response.json().get('error', 'Registration failed')
            update.message.reply_text(f"Error: {error_msg}")
    except ValueError as e:
        update.message.reply_text(f"Invalid input: {str(e)}. Use format: Name, Age, Gender, Wishlist")
    except requests.RequestException as e:
        logger.error(f"Error registering: {e}")
        update.message.reply_text("Couldn’t connect to the server. Try again later.")

def draw(update, context):
    """Handle /draw command."""
    if 'group_uuid' not in context.user_data:
        update.message.reply_text("Please start with the group link first using /start <group_uuid>.")
        return
    
    telegram_id = context.user_data['telegram_id']
    group_uuid = context.user_data['group_uuid']
    
    try:
        response = requests.post(f"{BASE_URL}/api/draw/", json={'telegram_id': telegram_id, 'group_uuid': group_uuid})
        if response.status_code == 200:
            data = response.json()
            update.message.reply_text(
                "🎉 Congratulations! Your secret Eid gift buddy is:\n"
                f"Name: {data['drawn_name']}\n"
                f"Age: {data['drawn_age']}\n"
                f"Gender: {data['drawn_gender']}\n"
                f"Wishlist: {data['drawn_wishlist']}"
            )
        else:
            error_msg = response.json().get('error', 'Drawing failed')
            update.message.reply_text(f"Error: {error_msg}")
    except requests.RequestException as e:
        logger.error(f"Error drawing: {e}")
        update.message.reply_text("Couldn’t connect to the server. Try again later.")

def error(update, context):
    """Log errors."""
    logger.warning(f"Update {update} caused error {context.error}")

def main():
    """Run the bot."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("draw", draw))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, register))
    dp.add_error_handler(error)
    
    # Start bot
    updater.start_polling()
    logger.info("Bot started polling...")
    updater.idle()

if __name__ == "__main__":
    main()