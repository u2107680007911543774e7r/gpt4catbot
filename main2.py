import datetime
import os
import openai
import telegram
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure, PyMongoError
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import pymongo
import certifi
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

ca = certifi.where()

# set the path of the certificate bundle file
cert_file_path = 'cacert.pem'

# set the REQUESTS_CA_BUNDLE environment variable to the path of the certificate bundle file
os.environ['REQUESTS_CA_BUNDLE'] = cert_file_path

# Set up OpenAI API credentials
# openai.api_key = "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"

# Telegram bot token
TELEGRAM_TOKEN = '5846714506:AAGDghMQMNFyNkhjIgt7hDQcqlh3Nj64NLU'

# OpenAI API key
openai.api_key = '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'

# Connect to MongoDB Atlas
mongo_uri = os.environ.get('mongodb+srv://u2107680007911543774e7r:evOCiYG3bpip5TB1@catgptcluster.mpnqoq1.mongodb.net/?retryWrites" \
            "=true&w=majority')
# mongo_dbname = os.environ.get('catgpt')
# = os.environ.get('u2107680007911543774e7r')
#mongo_password = os.environ.get('evOCiYG3bpip5TB1')

try:
    client = pymongo.MongoClient(mongo_uri, tlsCAFile=ca)
    db = client.get_database('catgpt')
    # db.authenticate(mongo_username, mongo_password)
    messages_collection = db.get_collection("catgpt_messages")
    feedback_collection = db.get_collection('catgpt_feedback')
except ConnectionFailure as e:
    print(f"CONNECTION ERR u21: {e}")

# Set up Telegram Bot API credentials
# telegram_token = '6257116099:AAEu_sGp6q_aqGH1D6riDPRmKMmR4e3vdpQ'
# telegram_token = '5978104179:AAF7ZHT6ci5jPqLhAbOnhN7upWMxbftuYNM'
bot = telegram.Bot(token=TELEGRAM_TOKEN)

newchat_button = InlineKeyboardButton("New chat", callback_data="newchat")
feedback_button = InlineKeyboardButton("Leave feedback", callback_data="feedback")
keyboard = [[newchat_button, feedback_button]]
reply_markup = InlineKeyboardMarkup(keyboard)
chat_type = ''


# import SpeechRecognition as sr
#
# # create a recognizer object
# r = sr.Recognizer()
#
# # define a function to convert the voice message to text
# def voice_to_text(voice_file):
#     # open the voice file using SpeechRecognition
#     with sr.AudioFile(voice_file) as source:
#         # read the audio data from the file
#         audio_data = r.record(source)
#         try:
#             # use Google's speech recognition service to transcribe the audio
#             text = r.recognize_google(audio_data)
#             return text
#         except sr.UnknownValueError:
#             # if the speech recognition service couldn't transcribe the audio, return an error message
#             return "Error: Could not recognize audio"


# Define function to get AI response
def ask_ai(prompt):
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {'role': 'system', 'content': 'You are ChatGPT, a large language model trained by OpenAI. You are helpful '
                                          'assistant Answer as '
                                          'concisely as possible.',
             "role": "user", "content": prompt}
        ]
    )
    message = response.choices[0].text.strip()
    return message


def handle_message(update, context):
    global chat_type
    # Get the chat ID and message text
    chat_id = update.message.chat_id
    chat = bot.get_chat(chat_id=chat_id)
    if chat.username:
        username = chat.username
    else:
        username = chat_id
    text = update.message.text
    timestamp = update.message.date.timestamp()
    date = datetime.datetime.fromtimestamp(timestamp)
    # if text.voice:
    #     text = voice_to_text(text.voice)
    if chat_type == 'feedback':
        # insert the feedback into the database
        feedback_doc = {"feedback_text": text,
                        'username': username,
                        'date': date.strftime('%Y-%m-%d, %H:%M:%S')}
        feedback_collection.insert_one(feedback_doc)
        # send a confirmation message to the user
        bot.send_message(chat_id=chat_id, text="Meow! And! Thanks for your feedback!")
        chat_type = ''
    else:
        # Save the message attributes to the database
        conversation_history = context.user_data.get('conversation', [])
        conversation_history.append(text)
        context.user_data['conversation'] = conversation_history

        # Concatenate the conversation history into a single prompt for the AI
        prompt = '\n'.join(conversation_history[-3:])
        if not prompt:
            prompt = "Hello!"

        # Ask the AI for a response
        ai_response = ask_ai(prompt)

        # Save the message and AI response to the database
        record = {
            'username': username,
            'text': text,
            'ai_response': ai_response,
            'date': date.strftime('%Y-%m-%d, %H:%M:%S'),
            'conversation_history': conversation_history
        }
        try:
            messages_collection.insert_one(record)
        except PyMongoError as e:
            print("Error occurred while inserting the record:", e)

        # Get the previous messages for this chat ID
        previous_messages = list(messages_collection.find({"chat_id": chat_id}))

        # Build the prompt with previous messages
        prompt_with_context = ""
        for i in range(len(previous_messages)):
            prompt_with_context += f"{previous_messages[i]['text']}\n"
            prompt_with_context += f"{previous_messages[i + 1]['text']}\n" if i + 1 < len(previous_messages) else ""
        prompt_with_context += text + "\n"

        # Send the message to the user
        bot.send_message(chat_id=chat_id,
                         text=ai_response)


def start(update, context):
    global chat_type
    chat_type = ''

    context.user_data['conversation'] = []
    bot.send_message(chat_id=update.message.chat_id,
                     text="Menu:",
                     reply_markup=reply_markup)


# Define functions
def newchat_callback(update, context):
    query = update.callback_query
    chat_id = query.message.chat_id
    context.user_data['conversation'] = []
    try:
        messages_collection.delete_many({'chat_id': chat_id})
    except (OperationFailure, ServerSelectionTimeoutError) as e:
        print(f"Error deleting item: {e}")
    bot.send_message(chat_id=chat_id,
                     text="Meow! Send me a message to start a new conversation.")


def feedback_callback(update, context):
    query = update.callback_query
    context.user_data['conversation'] = []
    bot.send_message(chat_id=query.message.chat_id,
                     text="Meow! Please leave your feedback in a message.")
    global chat_type
    chat_type += query.data


def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Registering handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(newchat_callback, pattern='newchat'))
    dp.add_handler(CallbackQueryHandler(feedback_callback, pattern='feedback'))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
