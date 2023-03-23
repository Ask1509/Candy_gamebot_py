import random
import telebot
from telebot import types
import logging
from config import TOKEN
from spy import log
import datetime


API_TOKEN = TOKEN
SET_CANDIES = 200
MAX_CANDIES = 28

bot = telebot.TeleBot(API_TOKEN)
telebot.logger.setLevel(logging.INFO)


storage = dict()
   
def init_storage(user_id):
    storage[user_id] = dict(current_candies=SET_CANDIES, user_candies=None, bot_name=None, user_name=None, game_state=True, move_maker=None)

def set_data_storage(user_id, key, value):
    storage[user_id][key] = value

def get_data_storage(user_id):
    return storage[user_id]


@bot.message_handler(func=lambda message: message.text.lower() == "привет")
def command_text_hi(m):
    bot.send_message(m.chat.id, 'Для начала игры введите "игра"')

@bot.message_handler(func=lambda message: message.text.lower() == "игра")
def digitgames(message):
    bot.send_message(message.chat.id, f'Привет! Предлагаем сыграть в увлекательную игру "Забери последнюю конфетку!" Правила простые: ' +
    f'на столе лежат {SET_CANDIES} конфет. Вы по очереди берёте несколько конфет, но не более {MAX_CANDIES} штук за раз. ' +
    f'Побеждает тот, кто заберёт последнюю конфету и не оставит ничего другому игроку!')
    # задание имени бота
    bot_names = ['Александр', 'Афанасий', 'Егор', 'Иван', 'Амфибрахий', 'Георгий', 'Василий']
    b_t = random.choice(bot_names)
    # Инициализация хранилища
    init_storage(message.chat.id)
    set_data_storage(message.chat.id, 'bot_name', b_t)
    # 
    sent_msg = bot.send_message(message.chat.id, 'Как Вас зовут?')
    bot.register_next_step_handler(sent_msg, welcome)

def welcome(message):
    n_bot = get_data_storage(message.chat.id)
    if message.text == "n" and n_bot['game_state'] == False:
        if n_bot == 'user': res = 'выиграл'
        else: res = 'проиграл'
        today = datetime.datetime.today()
        log(message.chat.first_name, n_bot['bot_name'], today.strftime("%d/%m/%Y %H.%M:%S"),res)
        bot.send_message(message.chat.id, 'Спасибо за игру! До встречи!')
        return
    if n_bot['user_name'] == None:
        set_data_storage(message.chat.id, 'user_name', message.text)
    set_data_storage(message.chat.id, 'current_candies', SET_CANDIES)
    set_data_storage(message.chat.id, 'game_state', True)
    bot.send_message(message.chat.id, f'{n_bot["user_name"]}, против Вас играет бот {n_bot["bot_name"]}')
    # передача хода игроку
    player_move(message)

# проверка ввода игрока
def check_step(message):
     # инициируем исходные данные
    msg_error = ""
    n_bot = get_data_storage(message.chat.id)
    # проверка на число
    if message.text.isnumeric():
        candies_taken = int(message.text)
     
        if candies_taken <= 0:
            msg_error = n_bot['user_name'] +" , количество взятых конфет должно быть больше 1!"
        if candies_taken > MAX_CANDIES:
            msg_error = n_bot['user_name'] +f" , не более {MAX_CANDIES} конфет!"
        if candies_taken > n_bot['current_candies']:
            msg_error = n_bot['user_name'] + " , конфет осталось всего "+n_bot['current_candies'] +" ! Вы не можете взять больше! Попробуйте еще раз?"
        if  msg_error:
            m_sent = bot.send_message(message.chat.id, msg_error)
            bot.register_next_step_handler(m_sent, check_step)
        else: 
            set_data_storage(message.chat.id, 'current_candies', n_bot['current_candies'] - candies_taken)
            bot.send_message(message.chat.id, n_bot['user_name'] + f" , Вы взяли конфет {candies_taken}, конфет осталось всего "+str(n_bot['current_candies']))
            # передача хода боту
            bot_move(message)
    else:
        msg_error = f'Ошибка ввода! Введите число от 1 до {MAX_CANDIES}'
        m_sent = bot.send_message(message.chat.id, msg_error)
        bot.register_next_step_handler(m_sent, check_step)
    
# ход бота
def bot_move(message):
    cur_state = get_data_storage(message.chat.id)
    set_data_storage(message.chat.id, 'move_maker', 'bot')
    if cur_state['current_candies'] <= 28:
        set_data_storage(message.chat.id, 'game_state', False)
        sent_msg = bot.send_message(message.chat.id, f'И последнюю конфету забирает {cur_state["bot_name"]}! В следующий раз Вам обязательно повезёт! Для выхода из игры введите "n"')
        bot.register_next_step_handler(sent_msg, welcome)
    else:
        step = cur_state["current_candies"] % (MAX_CANDIES + 1)
        if step < 1:
            step = random.randint(1, MAX_CANDIES)
        set_data_storage(message.chat.id, 'current_candies', cur_state['current_candies'] - step)
        bot.send_message(message.chat.id, f'{cur_state["bot_name"]} забирает {step} конфет, остаётся {cur_state["current_candies"]} конфет')
        player_move(message)
    
# ход игрока
def player_move(message):
    cur_state = get_data_storage(message.chat.id)
    set_data_storage(message.chat.id, 'move_maker', 'user')
    if cur_state['current_candies'] <= 28:
        set_data_storage(message.chat.id, 'game_state', False)
        sent_msg = bot.send_message(message.chat.id, f'{cur_state["user_name"]}, Вы забираете последнюю конфету! Поздравляем! Для выхода из игры введите "n"')
        bot.register_next_step_handler(sent_msg, welcome)
    else:
        sent_msg = bot.send_message(message.chat.id, f'{cur_state["user_name"]}, Ваш ход! Возьмите не более {MAX_CANDIES} конфет. Всего конфет осталось: {cur_state["current_candies"]}')
        bot.register_next_step_handler(sent_msg, check_step)
  
if __name__ == '__main__':
    bot.skip_pending = True
    bot.polling()