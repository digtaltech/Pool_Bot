import telebot
import sqlite3
import datetime
import requests
from telebot import types

bot = telebot.TeleBot('TOKEN')
conn = sqlite3.connect("pool.db")
cursor = conn.cursor()


@bot.message_handler(commands=['start'])
def send_start(message):

    bot.reply_to(message, 'Привет, смотри есть 2 основных команды: \n\n'
                 '- Просмотр баланса /balance (баланс обновляется раз в день) \n'
                 '- Заказать заявку на вывод /withdrawal')


@bot.message_handler(commands=['balance'])
def send_welcome(message):
    conn = sqlite3.connect("pool.db")
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT balance FROM users WHERE telegram_id={message.from_user.id}")
    balance = cursor.fetchall()
    bot.send_message(message.from_user.id,
                     'Баланс в XCH: ' + str(balance[0][0]))
    response = requests.get(
        'https://min-api.cryptocompare.com/data/price?fsym=XCH&tsyms=USD&api_key=%7B345f0ef4daa15497addbd88e6763b659436381c4042d83e9c067383f9e71d7bc%7D')
    price_usd = response.json()
    balance_in_usd = price_usd['USD'] * balance[0][0]
    bot.send_message(message.from_user.id,
                     'Баланс в USD: ' + str(balance_in_usd))
    cursor.execute(
        f"SELECT name FROM users WHERE telegram_id={message.from_user.id}")
    name = cursor.fetchall()
    bot.send_message(1047198180, f"{name[0][0]} узнал свой баланс")


@bot.message_handler(commands=['withdrawal'])
def send_withdrawal(message):

    bot.send_message(message.from_user.id, 'Сколько выводим ? \n'
                                           '- Вывод писать в формате 0.165 \n'
                                           '- Минимальный вывод от 0.1')
    bot.register_next_step_handler(message, withdrawal_validate)

# Функция выполнения выплаты


def withdrawal_validate(message):
    amount = message.text
    try:
        if float(amount) >= 0.1:
            # bot.send_message(message.from_user.id, 'Good1')
            try:
                conn = sqlite3.connect("pool.db")
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT balance FROM users WHERE telegram_id={message.from_user.id}")
                balance = cursor.fetchall()
                if balance[0][0] >= float(amount):
                    # Списываем с баланса сумму выплаты
                    cursor.execute(
                        f"UPDATE users SET balance=balance-{amount} WHERE telegram_id={message.from_user.id}")
                    conn.commit()
                    # Получим имя того кому выплачиваем
                    cursor.execute(
                        f"SELECT name FROM users WHERE telegram_id={message.from_user.id}")
                    name = cursor.fetchall()
                    # Создаём новую запись о выплате в нужной таблице
                    cursor.execute(
                        f"""INSERT INTO withdrawal (telegram_id,name,amount,date)
                         VALUES ('{message.from_user.id}','{name[0][0]}','{amount}',
                         '{datetime.datetime.now()}')""")
                    conn.commit()
                    # Если всё получилось говорим о успехе и отправляем заявку
                    # владельцу пула
                    bot.send_message(message.from_user.id, "Заявка оформлена")
                    bot.send_message(
                        201743325, f"{name[0][0]}, оформил заявку на выплату на сумму {amount}")
                else:
                    bot.send_message(message.from_user.id,
                                     'Недостаточно средств')
                    bot.register_next_step_handler(
                        message, withdrawal_validate)
            except BaseException as ex:
                bot.send_message(message.from_user.id, str(ex))
        else:
            bot.send_message(message.from_user.id, 'Минимальный вывод от 0.1')
            bot.register_next_step_handler(message, withdrawal_validate)
    except BaseException:
        bot.send_message(message.from_user.id,
                         'Данные указаны в неверном формате')
        bot.register_next_step_handler(message, withdrawal_validate)


@bot.message_handler(commands=['bank'])
def send_balance(message):
    if message.from_user.id == 201743325:
        bot.send_message(message.from_user.id, 'Сколько заработали сегодня ?')
        bot.register_next_step_handler(message, set_bank)
    else:
        bot.send_message(message.from_user.id, 'Тебе этого знать не надо')

def set_bank(message):
    try:
        bank = message.text
        conn = sqlite3.connect("pool.db")
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE users SET balance=balance+(rate*{bank})")
        conn.commit()
        bot.send_message(message.from_user.id, "Балансы установлены")

        cursor.execute("SELECT name, balance FROM users")
        for row in cursor.fetchall():
            name, balance = row
            bot.send_message(message.from_user.id, {f"{name} - {balance}"})
    except BaseException:
        bot.send_message(message.from_user.id, "Ошибка")


bot.polling(none_stop=True, interval=0)
