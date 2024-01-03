from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ParseMode
import requests
import json
import worker
import os

telegram_bot_key = os.getenv('TELEGRAM_BOT_TOKEN')


def start(update: Update, context: CallbackContext):
    context.user_data['chat_id'] = update.message.chat_id
    message_text = f"INSERT YOUR WELCOME MESSAGE HERE"

    # keyboard = [[InlineKeyboardButton("Consent", callback_data='consent')]]
    # reply_markup = InlineKeyboardMarkup(keyboard)

    # Sending the message with Markdown enabled
    update.message.reply_text(
        message_text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        # reply_markup=reply_markup
    )


def message_handler(update: Update, context: CallbackContext):
    if update.message.voice or update.message.audio:
        print(f"Received message.")
        print(update.message.chat.first_name)

        # Store the voice file path in context.user_data for access during callback
        context.user_data['chat_id'] = update.message.chat_id
        context.user_data['message_id'] = update.message.message_id

        try:
            context.user_data['voice_file_id'] = update.message.voice.file_id
            context.user_data['voice_duration'] = update.message.voice.duration

        except:
            context.user_data['voice_file_id'] = update.message.audio.file_id
            context.user_data['voice_duration'] = update.message.audio.duration

        keyboard = [
            [InlineKeyboardButton("Transcribe", callback_data='transcribe'),
             InlineKeyboardButton("Summarize", callback_data='summarize')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text('You sent an audio! Choose an option:', reply_markup=reply_markup)



def button(update: Update, context: CallbackContext):
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    query.answer()

    if query.data == 'transcribe' or query.data == 'summarize':

        if context.user_data['voice_duration'] >= 900:
            context.bot.send_message(context.user_data['chat_id'],
                                     f"I'm sorry, but your voice message is too long.",
                                     reply_to_message_id=context.user_data['message_id'])
        else:

            # This is where you would handle the callback data and work with it
            query.edit_message_text(text=f"Selected option: {query.data}")

            # Retrieve the voice file path from the context.user_data
            message_id = context.user_data.get('message_id', None)
            voice_file_id = context.user_data.get('voice_file_id', None)

            voice_id = voice_file_id
            voice = requests.get(f"https://api.telegram.org/bot{telegram_bot_key}/getFile?file_id={voice_id}")
            voice = voice.content.decode('utf-8')
            voice_url = json.loads(voice)['result']['file_path']
            voice_url = f"https://api.telegram.org/file/bot{telegram_bot_key}/{voice_url}"
            voice = requests.get(voice_url)
            voice = voice.content

            # Saving the OGG File
            file_name_ogg = f"my_audio.ogg"
            file_name_mp3 = f"my_audio.mp3"
            with open(f"audio/{file_name_ogg}", "wb") as f:
                f.write(voice)

            # Convert OGG into MP3
            worker.convert_ogg_to_mp3(f"audio/{file_name_ogg}", f"audio/{file_name_mp3}")
            print("Converted successfully.")

            transcript = worker.transcribe(file_name_mp3)
            # Check which button was pressed
            if query.data == 'transcribe':
                context.bot.send_message(context.user_data['chat_id'],
                                         f"{transcript}",
                                         reply_to_message_id=context.user_data['message_id'])


            elif query.data == 'summarize':
                summarize = worker.summarize(transcript)
                context.bot.send_message(context.user_data['chat_id'],
                                         f"{summarize}",
                                         reply_to_message_id=context.user_data['message_id'])



def main() -> None:
    updater = Updater(telegram_bot_key, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register commands
    dispatcher.add_handler(CommandHandler("start", start))

    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    dispatcher.add_handler(MessageHandler(~Filters.command, message_handler))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
