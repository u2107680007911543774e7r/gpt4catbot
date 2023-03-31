import datetime
import telegram
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import openai
import os
import speech_recognition as sr
from google.cloud import speech_v1p1beta1 as speech

# Set the SSL_CERT_FILE environment variable to point to the downloaded CA certificates file
os.environ['SSL_CERT_FILE'] = 'cacert.pem'

# Replace the following variables with your actual MongoDB Atlas serverless credentials
mongo_user = 'u2107680007911543774e7r'
mongo_pass = 'evOCiYG3bpip5TB1'
cluster_url = 'serverlessinstance0.bnnnc12.mongodb.net'

# Create a connection string
connection_string = f"mongodb+srv://{mongo_user}:{mongo_pass}@{cluster_url}/gpt4catbot?retryWrites=true&w=majority"

# Connect to the MongoDB Atlas serverless instance using SSL and the CA certificate bundle provided by certifi
client = MongoClient(connection_string)

# Replace 'your_database_name' with the name of your database
db = client["gpt4catbot"]

# Replace 'your_collection_name' with the name of your collection
collection = db["messages"]

# Telegram bot token
TELEGRAM_TOKEN = '5846714506:AAGDghMQMNFyNkhjIgt7hDQcqlh3Nj64NLU'

# OpenAI API key
openai.api_key = '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'

# GPT-3.5 model ID
model_engine = "gpt-3.5-turbo-0301"
# model_engine = "gpt-4"

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


def handle_message(update, context):
    # Get user info
    chat_id = update.message.chat_id
    chat = bot.get_chat(chat_id=chat_id)
    username = chat_id
    if chat.username:
        username = chat.username
    # Get timestamp
    timestamp = update.message.date.timestamp()
    date = datetime.datetime.fromtimestamp(timestamp)
    # Get message from user
    user_message = update.message.text
    chat_context = get_context(username)
    # Call GPT-3.5 model to generate response
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=[
            {'role': 'system', 'content': 'You are ChatGPT implementation named CatGPT. You are a large language '
                                          'model trained by OpenAI. You are helpful assistant. Answer as concisely as '
                                          'possible. You should mind the context, and sometimes add "Meow" to the '
                                          'responses.',
             "role": "user", "content": chat_context + user_message}
        ]
    )
    text = response['choices'][0]['message']['content']
    record = {
        'username': username,
        'text': user_message,
        'ai_response': text,
        'date': date.strftime('%Y-%m-%d, %H:%M:%S')
    }
    save_context(record)

    # Send response back to user
    bot.send_message(chat_id=chat_id, text=text)


def thinking(update, context):
    user_message = 'Tell me one positive philosophical/psychological/technological and up-to-date quote, please. You ' \
                   'can also mention the author of the quote. '
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


def thinkingua(update, context):
    user_message = 'Tell me one demotivational and up-to-date quote in Ukrainian ' \
                   'language, please. It should relate to cats. You can also mention the author of the quote. '
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
    try:
        collection.delete_many({'username': username})
    except PyMongoError as e:
        print('clear_context: not cleared')
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Hi! I am CatGPT! A Telegram implementation of the latest ChatGPT model.'
                                  '\n\nSend me a message and I will respond like ChatGPT does. Maybe... Go check it! '
                                  '\U0001F640' +
                                  '\n\nTo reset the conversation context: /start\nContact: @t2107790007911543774e7r '
                                  '\U000000A9' +
                                  '\nDaily expression: /thinking' +
                                  '\nDaily expression: /ua \U0001F1FA')


# define function to convert voice message to text
def transcribe_voice_message(voice_message_file):
    # load voice message file using SpeechRecognition library
    r = sr.Recognizer()
    with sr.AudioFile(voice_message_file) as source:
        audio_data = r.record(source)

    # set up Google Cloud Speech-to-Text API client
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        language_code="und",
        sample_rate_hertz=16000,
    )
    audio = speech.RecognitionAudio(content=audio_data.frame_data)

    # send transcription request to Google Cloud Speech-to-Text API
    response = client.recognize(request={"config": config, "audio": audio})

    # extract transcribed text from API response
    text = ''
    for result in response.results:
        text += result.alternatives[0].transcript

    return text


# Create the Updater and pass in the bot's token.
updater = Updater(TELEGRAM_TOKEN, use_context=True)

# Get the dispatcher to register handlers
dispatcher = updater.dispatcher

# Add handlers to the dispatcher
dispatcher.add_handler(CommandHandler("start", start_bot))
dispatcher.add_handler(CommandHandler("thinking", thinking))
dispatcher.add_handler(CommandHandler("ua", thinkingua))
dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

# Start the bot
updater.start_polling()

# Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
updater.idle()
