import telebot
from telebot import types
import random
import time
import threading


TOKEN = '7866406937:AAGoZKzJmnF3DOI4r5T8nVg6_9T_RDhjOPo'
bot = telebot.TeleBot(TOKEN)


games = {}

user_stats = {}


def create_keyboard(board):
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    buttons = []
    for i, cell in enumerate(board):
        buttons.append(types.InlineKeyboardButton(text=cell, callback_data=f'move_{i}'))
    buttons.append(types.InlineKeyboardButton(text="🛑 Прекратить игру", callback_data='stop_game'))
    keyboard.add(*buttons)
    return keyboard


def check_winner(board):
    win_combinations = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, b, c in win_combinations:
        if board[a] == board[b] == board[c] and board[a] != ' ':
            return board[a]
    if ' ' not in board:
        return 'draw'
    return None


def start_new_game(chat_id, user_id):
    games[chat_id] = {
        'board': [' '] * 9,
        'player_turn': '❌',
        'player': user_id,
        'status': 'playing',
        'message_id': None,
        'welcome_message_id': None,
        'winner_message_sent': False,
    }
    return "🎮 Игра против бота началась! Твой ход - ❌"


def delete_old_messages(chat_id):
    if chat_id in games:
        game = games[chat_id]
        if game['message_id']:
            try:
                bot.delete_message(chat_id, game['message_id'])
            except Exception as e:
                print(f"Ошибка удаления сообщения: {e}")
            game['message_id'] = None


def clear_chat_messages(chat_id):
    try:
        while True:
            try:

                last_message = bot.get_chat_history(chat_id, limit=1)[0]
            except Exception:

                break

            last_message_id = last_message.message_id


            for i in range(1, last_message_id + 1):
                try:
                    bot.delete_message(chat_id, i)
                except Exception as e:
                    print(f"Ошибка удаления сообщения: {e}")
                time.sleep(0.05)


            break
    except Exception as e:
        print(f"Ошибка при удалении сообщений: {e}")


def update_board_message(chat_id):
    delete_old_messages(chat_id)
    if chat_id not in games:
        return
    game = games[chat_id]
    board = game['board']
    keyboard = create_keyboard(board)

    winner = check_winner(board)
    if winner:
        if winner == 'draw':
            text = "🤝 Ничья! Хорошая игра!"
        else:
            text = f"🎉 Победил {winner}! Поздравляю! 🎉"
        keyboard = None
    else:
        text = f"👉 Ходит игрок {game['player_turn']}"

    sent_message = bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard
    )
    game['message_id'] = sent_message.message_id


def get_bot_move(board):
    for i in range(9):
        if board[i] == ' ':
            temp_board = board[:]
            temp_board[i] = '⭕'
            if check_winner(temp_board) == '⭕':
                return i
    for i in range(9):
        if board[i] == ' ':
            temp_board = board[:]
            temp_board[i] = '❌'
            if check_winner(temp_board) == '❌':
                return i
    available_moves = [i for i, x in enumerate(board) if x == ' ']
    if available_moves:
        return random.choice(available_moves)
    return None


def create_admin_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton('/start'),
        types.KeyboardButton('/newgame'),
        types.KeyboardButton('Сбросить данные'),
        types.KeyboardButton('Очистить чат'),
    ]
    keyboard.add(*buttons)
    return keyboard


def create_start_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton("🚀 Начать игру"))
    return keyboard


def create_menu_keyboard():  # Новая функция для меню
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        types.KeyboardButton('/newgame'),
        types.KeyboardButton('🚀 Начать игру'),
        types.KeyboardButton('/stats'),
    )
    keyboard.add(
        types.KeyboardButton('Сбросить данные'),
        types.KeyboardButton('Очистить чат'),
    )
    return keyboard



greetings = [
    "👋 Привет! Готов сыграть в крестики-нолики? Нажми кнопку ниже!",
    "🎮 Добро пожаловать! Сыграем партию? Начни игру, нажав кнопку ниже!",
    "✨ Приветствую! Давай сыграем в крестики-нолики. Нажми кнопку ниже, чтобы начать!",
    "🕹️ Готов к игре? Начни новую игру, нажав кнопку ниже!",
]


@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.chat.id == 123456789:
        bot.send_message(message.chat.id, "⚙️ Панель управления ботом", reply_markup=create_admin_keyboard())
    else:
        greeting = random.choice(greetings)
        bot.send_message(message.chat.id, greeting, reply_markup=create_menu_keyboard())


    bot.set_my_commands([
        telebot.types.BotCommand("/start", "Начало работы с ботом"),
        telebot.types.BotCommand("/newgame", "Начать новую игру"),
        telebot.types.BotCommand("/stats", "Посмотреть статистику")
    ])


@bot.message_handler(commands=['stats'])
def stats_handler(message):
    user_id = message.from_user.id
    if user_id in user_stats:
        wins = user_stats[user_id].get('wins', 0)
        losses = user_stats[user_id].get('losses', 0)
        draws = user_stats[user_id].get('draws', 0)
        bot.send_message(message.chat.id, f"📊 Статистика:\nПобед: {wins}\nПоражений: {losses}\nНичьих: {draws}",
                         reply_markup=create_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "📊 Статистика пока отсутствует.", reply_markup=create_menu_keyboard())


@bot.message_handler(func=lambda message: message.text == 'Сбросить данные')
def reset_data(message):
    if message.chat.id == 123456789:
        games.clear()
        user_stats.clear()  # Сбросить статистику
        bot.send_message(message.chat.id, "✅ Данные сброшены.")
    else:
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой команде.")


@bot.message_handler(func=lambda message: message.text == "🚀 Начать игру")
def new_game_from_keyboard_handler(message):
    new_game_handler(message)


def delete_start_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Ошибка удаления сообщения начала игры: {e}")


@bot.message_handler(commands=['newgame'])
def new_game_handler(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if chat_id in games:
        bot.send_message(chat_id,
                         "⚠️ Игра уже идёт в этом чате. Дождись окончания текущей игры или начни новую в другом чате.")
    else:
        if chat_id in games and games[chat_id]['welcome_message_id']:
            try:
                bot.delete_message(chat_id, games[chat_id]['welcome_message_id'])
            except Exception as e:
                print(f"Ошибка удаления приветственного сообщения: {e}")
            games[chat_id]['welcome_message_id'] = None

        message_text = start_new_game(chat_id, user_id)
        sent_message = bot.send_message(chat_id, message_text)

        update_board_message(chat_id)


        threading.Timer(3.0, delete_start_message, args=[chat_id, sent_message.message_id]).start()


@bot.message_handler(func=lambda message: message.text == 'Очистить чат')
def clear_messages_handler(message):
    if message.chat.id == 123456789:
        chat_id = message.chat.id
        clear_chat_messages(chat_id)
        bot.send_message(chat_id, "🧹 Все сообщения удалены.", reply_markup=create_menu_keyboard())
    else:
        bot.send_message(message.chat.id, "⛔ У вас нет доступа к этой команде.", reply_markup=create_menu_keyboard())


def bot_move_with_delay(chat_id, board):
    time.sleep(1)
    game = games.get(chat_id)
    if game and game['status'] == 'playing':
        bot_move = get_bot_move(board)
        if bot_move is not None:
            board[bot_move] = '⭕'
            winner = check_winner(board)
            if winner:
                if not game['winner_message_sent']:
                    game['winner_message_sent'] = True
                    update_board_message(chat_id)
                    user_id = game['player']
                    if user_id not in user_stats:
                        user_stats[user_id] = {'wins': 0, 'losses': 0, 'draws': 0}
                    if winner == 'draw':
                        user_stats[user_id]['draws'] = user_stats[user_id].get('draws', 0) + 1
                        bot.send_message(chat_id, "🤝 Ничья! Хорошая игра!", reply_markup=create_menu_keyboard())
                    else:
                        user_stats[user_id]['losses'] = user_stats[user_id].get('losses', 0) + 1
                        bot.send_message(chat_id, f"🎉 Победил бот! Попробуй ещё раз! 🎉",
                                         reply_markup=create_menu_keyboard())
                    delete_old_messages(chat_id)
                    del games[chat_id]
                    return
            else:

                game['player_turn'] = '❌'
                update_board_message(chat_id)
        else:
            if not game['winner_message_sent']:
                game['winner_message_sent'] = True
                update_board_message(chat_id)
                user_id = game['player']
                if user_id not in user_stats:
                    user_stats[user_id] = {'wins': 0, 'losses': 0, 'draws': 0}
                user_stats[user_id]['draws'] = user_stats[user_id].get('draws', 0) + 1
                bot.send_message(chat_id, "🤝 Игра закончилась ничьей.", reply_markup=create_menu_keyboard())
                delete_old_messages(chat_id)
                del games[chat_id]


@bot.callback_query_handler(func=lambda call: call.data.startswith('move_'))
def move_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    if chat_id not in games or games[chat_id]['status'] != 'playing':
        bot.answer_callback_query(call.id, "⚠️ Игра не найдена или не в состоянии игры")
        return
    game = games[chat_id]
    if user_id != game['player']:
        bot.answer_callback_query(call.id, "⛔ Вы не участник этой игры.")
        return
    if game['player_turn'] != '❌' and game['player_turn'] != '⭕':
        bot.answer_callback_query(call.id, "🤔 Сейчас не ваш ход.")
        return

    move = int(call.data.split('_')[1])
    board = game['board']

    if board[move] == ' ':
        board[move] = game['player_turn']

        winner = check_winner(board)
        if winner:
            if not game['winner_message_sent']:
                game['winner_message_sent'] = True
                update_board_message(chat_id)
                user_id = game['player']
                if user_id not in user_stats:
                    user_stats[user_id] = {'wins': 0, 'losses': 0, 'draws': 0}
                if winner == 'draw':
                    user_stats[user_id]['draws'] = user_stats[user_id].get('draws', 0) + 1
                    bot.send_message(chat_id, "🤝 Ничья! Хорошая игра!", reply_markup=create_menu_keyboard())
                else:
                    user_stats[user_id]['wins'] = user_stats[user_id].get('wins', 0) + 1
                    bot.send_message(chat_id, f"🎉 Победил игрок {winner}! Поздравляю! 🎉",
                                     reply_markup=create_menu_keyboard())
                delete_old_messages(chat_id)
                del games[chat_id]
            return


        game['player_turn'] = '⭕'
        update_board_message(chat_id)


        threading.Thread(target=bot_move_with_delay, args=[chat_id, board]).start()

    else:
        bot.answer_callback_query(call.id, "🚫 Клетка занята, выбери другую!")


@bot.callback_query_handler(func=lambda call: call.data == 'stop_game')
def stop_game_handler(call):
    chat_id = call.message.chat.id
    if chat_id in games:
        del games[chat_id]
        bot.send_message(chat_id, "🛑 Игра прекращена.", reply_markup=create_menu_keyboard())
        delete_old_messages(chat_id)
    else:
        bot.answer_callback_query(call.id, "🚫 Нет активных игр в этом чате.")


if __name__ == '__main__':
    bot.polling(none_stop=True)