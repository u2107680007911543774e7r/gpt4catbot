import telegram
import openai
import os
from telegram import ChatAction, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# Set the SSL_CERT_FILE environment variable to point to the downloaded CA certificates file
os.environ['SSL_CERT_FILE'] = 'cacert.pem'

# Replace the following variables with your actual MongoDB Atlas serverless credentials
mongo_user = 'XXX'
mongo_pass = 'XXX'
cluster_url = 'XXX.mongodb.net'

# Create a connection string
connection_string = f"mongodb+srv://{mongo_user}:{mongo_pass}@{cluster_url}/gpt4catbot?retryWrites=true&w=majority"

# Connect to the MongoDB Atlas serverless instance using SSL and the CA certificate bundle provided by certifi
client = MongoClient(connection_string)

# Replace 'your_database_name' with the name of your database
db = client["gpt4catbot"]

# Replace 'your_collection_name' with the name of your collection
collection = db["messages"]

# Telegram bot token
TELEGRAM_TOKEN = 'XXX'

# OpenAI API key
openai.api_key = 'XXX'

# GPT model ID
#model_engine = "gpt-3.5-turbo"
model_engine = "gpt-4"

# Initialize Telegram bot
bot = telegram.Bot(token=TELEGRAM_TOKEN)


# Define function to handle messages
def save_context(record):
    try:
        collection.insert_one(record)
    except PyMongoError as e:
        print('save_context: not inserted')


def get_context(username):
    # Retrieve all messages for a given chat ID and concatenate them together
    context = ''
    try:
        for message in collection.find({"username": username}):
            context += message["text"] + '\n' + message['ai_response'] + '\n'
    except PyMongoError as e:
        print('get_context: not found')
    return context


def handle_message(update: Update, context: CallbackContext):
    # Get user info
    chat_id = update.message.chat_id
    chat = bot.get_chat(chat_id=chat_id)
    username = chat_id
    if chat.username:
        username = chat.username
    # Get timestamp
    # timestamp = update.message.date.timestamp()
    # date = datetime.datetime.fromtimestamp(timestamp)
    # Get message from user
    user_message = update.message.text
    chat_context = get_context(username)
    date = update.message.date

    # Check if the Trial Limit has been reached
    message_count = collection.count_documents({'username': username})
    print(message_count)
    # update.message.reply_text(f'You have sent {message_count} messages.')
    if message_count < 5:
        # Send the "typing" action
        context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        # Call GPT-3.5 model to generate response
        try:
            response = openai.ChatCompletion.create(
                model=model_engine,
                messages=[
                    {'role': 'system', 'content': 'You are ChatGPT implementation named CatGPT. You are a large language '
                                                  'model trained by OpenAI. You are helpful assistant. Answer as '
                                                  'concisely as possible. You should mind the context, '
                                                  'and sometimes mention "Meow" in the beginning/end of the message.',
                     "role": "user", "content": chat_context + user_message}
                ]
            )
            text = response['choices'][0]['message']['content']
        except openai.error.InvalidRequestError as e:
            text = "Hey, your message is too long. This model's maximum context length is 4097 tokens. " \
                   "Please, reword it shorter! :)"
        # Make a record document for DB
        record = {
            'username': username,
            'text': user_message,
            'ai_response': text,
            'date': date
        }
        save_context(record)

        # Send response back to user
        bot.send_message(chat_id=chat_id, text=text)
    else:
        bot.send_message(chat_id=chat_id, text="You've reached the free trial limit of 5 messages. ")


def media_handler(update: Update, context: CallbackContext):
    update.message.reply_text("Audio/Voice/Video/Sticker files are not yet supported. In progress...")


def thinking(update, context):
    user_message = 'Write me one inspiring, philosophical or psychological or technological or healthy and up-to-date ' \
                   'quote, please. You can also mention the author of the quote. '
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=[
            {'role': 'system', 'content': 'You are ChatGPT implementation named CatGPT. You are a large language '
                                          'model trained by OpenAI. You are helpful assistant. Answer as concisely as '
                                          'possible. You should mind the context, and sometimes add "Meow" to the '
                                          'responses.',
             "role": "user", "content": user_message}
        ]
    )
    text = response['choices'][0]['message']['content']
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=text)


def coding(update, context):
    user_message = 'Write me one short coding example of any sorting algorithm in any language.'
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=[
            {'role': 'system', 'content': 'You are ChatGPT implementation named CatGPT. '
                                          'You are a large programming language '
                                          'model trained by OpenAI. You are helpful assistant. '
                                          'Answer as concisely as possible.',
             "role": "user", "content": user_message}
        ]
    )
    text = response['choices'][0]['message']['content']
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=text)


def thinkingua(update, context):
    user_message = 'Tell me one demotivational and up-to-date quote in Ukrainian ' \
                   'language, please. It should relate to cats, future or evolution. Do not add the translation.'
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=[
            {'role': 'system', 'content': 'You are ChatGPT implementation named CatGPT. You are a large language '
                                          'model trained by OpenAI. You are helpful assistant. Answer as concisely as '
                                          'possible. You should mind the context, and sometimes add "Meow" to the '
                                          'responses.',
             "role": "user", "content": user_message}
        ]
    )
    text = response['choices'][0]['message']['content']
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=text)


# Define function to start the bot
def start_bot(update, context):
    chat_id = update.message.chat_id
    chat = bot.get_chat(chat_id=chat_id)
    username = chat_id
    if chat.username:
        username = chat.username
    if username == 't2107790007911543774e7r':
        try:
            collection.delete_many({'username': username})
        except PyMongoError as e:
            print('clear_context: not cleared')

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='I am CatGPT!'
                                  '\nA Telegram implementation of ChatGPT.'
                                  '\n\nWhat can I do?'
                                  '\n\nInformation, problem-solving, coding, translation, '
                                  'writing tasks, etc.'
                                  '\nHere are some shortcuts:'
                                  '\nCoding example: /coding'
                                  '\nDaily expression: /thinking'
                                  '\nUkrainian expressions to observe your emotions: /ua 🇺🇦'
                                  '\n\nTo reset the conversation context: /start'
                                  '\n\nMode: Free trial '
                                  '\nLimit: 5 messages per user'
                                  '\n\nContact: @t2107790007911543774e7r')


# Create the Updater and pass in the bot's token.
updater = Updater(TELEGRAM_TOKEN, use_context=True)

# Get the dispatcher to register handlers
dispatcher = updater.dispatcher

# Add handlers to the dispatcher
dispatcher.add_handler(CommandHandler("start", start_bot))
dispatcher.add_handler(CommandHandler("thinking", thinking))
dispatcher.add_handler(CommandHandler("ua", thinkingua))
dispatcher.add_handler(CommandHandler("coding", coding))
dispatcher.add_handler(MessageHandler(Filters.text, handle_message))
dispatcher.add_handler(MessageHandler(Filters.voice, media_handler))
dispatcher.add_handler(MessageHandler(Filters.audio, media_handler))
dispatcher.add_handler(MessageHandler(Filters.video, media_handler))
dispatcher.add_handler(MessageHandler(Filters.sticker, media_handler))

# Start the bot
updater.start_polling()

# Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
updater.idle()
