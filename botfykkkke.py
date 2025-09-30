import telebot
bot = telebot.TeleBot('7626248496:AAH4r7DC9HoXLd-l02X_9hJd6G4w814gJtI')

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    bot.send_message(message.chat.id, message.text)

if __name__ == '__main__':
     bot.infinity_polling()
