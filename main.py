# Edit configuration --> environment variables --> +
# GOOGLE_APPLICATION_CREDENTIALS = small-talk-xkyu-4d349b50b864.json

# pip install -r requirements.txt

import telebot
import cv2
import os
from rmn import RMN
import random
from google.cloud import dialogflow_v2beta1 as dialogflow

from google.api_core.exceptions import InvalidArgument
DIALOGFLOW_PROJECT_ID = 'small-talk-xkyu'
DIALOGFLOW_LANGUAGE_CODE = 'ru'
GOOGLE_APPLICATION_CREDENTIALS = 'small-talk-xkyu-4d349b50b864.json'
SESSION_ID = 'current-user-id'
session_client = dialogflow.SessionsClient()
session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)

m = RMN()

# Создаем экземпляр бота
bot = telebot.TeleBot('5099090138:AAF2LTvMf75qiwAIJXP264Zles4pmONsaHE')

f = open('current_emotion.txt', 'w')
f.write('neutral')
f.close()

smiles = {'sad': [' 😔', ' 😞', ' 😕', ' ☹', ' 🥲', ' 😢', ' 😭', ' 😥', ' 😓', ' 😪', ' 😩', ' 😫', ''],
          'happy': [' 😀', ' 😃', ' 😄', ' 😁', ' 😉', ' 😋', ''],
          'surprise': [' 😲', ' 😮', ' 😧', ' 😦', ' 😯', ''], 'angry': [' 😡', ' 😠', ' 🤬', ' 👿', ' 😤', ''],
          'fear': [' 😱', ' 😨', ' 😰', ' 😳', ' 🥴', ' 😵', ''], 'disgust': [' 🤢', ' 🤮', ' 🥴', ' 😑', ' 😬', ' 🤨', ''],
          'neutral': ['']}


# Функция, обрабатывающая команду /start
@bot.message_handler(commands=["start"])
def start(m, res=False):
    bot.send_message(m.chat.id, 'Привет! Отправь мне свою фотографию, и я постараюсь перенять твое настроение в нашем разговоре. '
    'Мои эмоции можно понять по эмоджи. Я знаю только русский язык')


# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
def handle_text(message):
    text_input = dialogflow.types.TextInput(text=message.text, language_code=DIALOGFLOW_LANGUAGE_CODE)
    query_input = dialogflow.types.QueryInput(text=text_input)
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise
    f = open('current_emotion.txt', 'r')
    cur_emotion = f.read()
    f.close()
    bot.send_message(message.chat.id, response.query_result.fulfillment_text + random.choice(smiles[cur_emotion]))


@bot.message_handler(content_types=['photo'])
def handler_file(message):
    from pathlib import Path
    Path(f'files/{message.chat.id}/').mkdir(parents=True, exist_ok=True)
    try:
        file_info = bot.get_file(message.photo[len(message.photo) - 1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = f'files/' + file_info.file_path.replace('photos/', '')
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        image = cv2.imread(src)
        num_faces = len(m.detect_faces(image))
        f = open('current_emotion.txt', 'w')
        if num_faces == 0:
            bot.send_message(message.chat.id, "Прости, не могу найти лицо на этом фото")
            f.write('neutral')
        else:
            results = m.detect_emotion_for_single_frame(image)
            cur_emotion = results[0]['emo_label']
            f.write(cur_emotion)
            if cur_emotion == 'neutral':
                bot.send_message(message.chat.id, 'Настраиваюсь на нейтральное состояние')
            else:
                bot.send_message(message.chat.id, random.choice(smiles[cur_emotion][:-1]))
        f.close()
        os.remove(os.path.join('./', src))
    except Exception as e:
        bot.reply_to(message, e)

# Запускаем бота
bot.polling(none_stop=True, interval=0)
