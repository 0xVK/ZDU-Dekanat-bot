# -*- coding: utf-8 -*-
import urllib
from bs4 import BeautifulSoup
import requests
import re
import telebot
import datetime
import os
from flask import Flask, request

# print(re.sub('\((.*?)\)', '', l))

#  __________________________________________________ROZKLAD__________________________________________________________


def get_rozklad(faculty='', teacher='', group='', sdate='', edate=''):

    dekanat_url = 'https://dekanat.zu.edu.ua/cgi-bin/timetable.cgi?n=700'

    http_headers = {
            'Host': 'dekanat.zu.edu.ua',
            'User-Agent': 'ZDU_Dekanat_Bot',
            'Accept': 'text/html',
    }

    post_data = {
        'faculty': faculty,
        'teacher': teacher.encode('windows-1251'),
        'group': group.encode('windows-1251'),
        'sdate': sdate,
        'edate': edate,
        'n': 700,

    }

    page = requests.post(dekanat_url, post_data, headers=http_headers)
    parsed_page = BeautifulSoup(page.content, 'html.parser')

    all_days_list = parsed_page.find_all('div', class_='col-md-6')[1:]

    all_days_lessons = []

    for day_table in all_days_list:
        all_days_lessons.append({
            'day': day_table.find('h4').find('small').text,
            'date': day_table.find('h4').text[:8],
            'lessons': [' '.join(lesson.text.split()) for lesson in day_table.find_all('td')[1::2]]
        })

    return all_days_lessons

#  ____________________________________________________BOT__________________________________________________________
bot = telebot.TeleBot('365877050:AAEu40eh-KBhlE8HIqifnyGSsw89U_4TK3Y')


def check_user_if_exist(user):

    with open('db.txt', 'r') as user_db_file:

        for line in user_db_file:
            if line.split(':')[0] == str(user):
                user_db_file.close()
                return True
        user_db_file.close()
        return False


def add_user_to_db(user_id, group):

    if not check_user_if_exist(user_id):  # create new user

        with open('db.txt', 'a') as user_db_file:
            user_db_file.write('{}:{}\n'.format(user_id, group))

    else:  # update user group

        with open('db.txt', 'r') as user_db_file:
            file_lines = user_db_file.readlines()

        new_lines = []

        for line in file_lines:

            if line.split(':')[0] == str(user_id):
                new_lines.append('{}:{}\n'.format(user_id, group))
            else:
                new_lines.append(line)

        with open('db.txt', 'w') as user_db_file:
            user_db_file.writelines(new_lines)


def get_user_group(user):

    with open('db.txt', 'r') as user_db_file:
        for line in user_db_file:
            if line.split(':')[0] == str(user):
                user_db_file.close()
                return str(line.split(':')[1])
        user_db_file.close()
        return False


def show_day_rozklad(day_data):

    rozklad = '*******{} ({})*******:\n'.format(day_data['day'], day_data['date'])

    lessons = day_data['lessons']

    for i in range(len(lessons)):
        if lessons[i]:
            s_index = i
            break

    for i in range(s_index, len(lessons)):
        if not lessons[i]:
            e_index = i
            break

    for i in range(s_index, e_index):
        if lessons[i]:
            rozklad += '{}) >{}\n\n'.format(i + 1, lessons[i])
        else:
            rozklad += '{}) > -----\n'.format(i + 1)

    return rozklad


def menu_action(message):

    if message.text == 'На сьогодні':
        group = get_user_group(message.chat.id)
        rozklad_data = get_rozklad(group=group)

        if rozklad_data:
            rozklad_for_today = show_day_rozklad(rozklad_data[0])
        else:
            rozklad_for_today = 'На сьогодні пар не знайдено.'

        bot.send_message(message.chat.id, rozklad_for_today)

    elif message.text == 'На завтра':
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)

        tom_day = tomorrow.strftime('%d.%m.%Y')

        group = get_user_group(message.chat.id)
        rozklad_data = get_rozklad(group=group, sdate=tom_day, edate=tom_day)

        if rozklad_data:
            rozklad_for_tom = show_day_rozklad(rozklad_data[0])
        else:
            rozklad_for_tom = 'На завтра пар не знайдено.'

        bot.send_message(message.chat.id, rozklad_for_tom)

    elif message.text == 'На тиждень':

        in_week = datetime.date.today() + datetime.timedelta(days=7)

        in_week_day = in_week.strftime('%d.%m.%Y')
        today = datetime.date.today().strftime('%d.%m.%Y')

        group = get_user_group(message.chat.id)
        rozklad_data = get_rozklad(group=group, sdate=today, edate=in_week_day)

        rozklad_for_week = ''

        if rozklad_data:
            for rozklad_day in rozklad_data:
                rozklad_for_week += show_day_rozklad(rozklad_day)
        else:
            rozklad_for_week = 'На тиждень пар не знайдено.'

        bot.send_message(message.chat.id, rozklad_for_week)

    elif message.text == 'Підписатися':
        bot.send_message(message.chat.id, 'Тут можна буде активувати фігнюшку, '
                                          'яка буде сама присилати розклад у вибраний час. Це ще в розробці, чекай)')

    elif message.text == 'Час пар':
        lessons_time = "Час пар:\n1) 08:00-09:20\n2) 09:30-10:50\n3) 11:10-12:30\n4) 12:40-14:00\n5) 14:10-15:30\n" \
                           "6) 15:40-17:00 \n7) 17:20-18:40\n8) 18:50-20:10"

        bot.send_message(message.chat.id, lessons_time)

    elif message.text == 'Змінити групу':

        user_group = get_user_group(message.chat.id)

        if user_group:
            msg = 'Твоя група: {}щоб змінити введи /start і вкажи нову.'.format(user_group)

        bot.send_message(message.chat.id, msg)

    elif message.text == 'Інформація':
        bot.send_message(message.chat.id, 'Бот знаходиться в розробці це поки перша - тестова версія.\n'
                                          'Пропозиції щодо покращення, повідомлення про баги сюди :\n '
                                          'Телеграм: @Koocherov, \n VK: vk.com/koocherov')

    elif message.text == 'Розклад іншої групи':
        sent = bot.send_message(message.chat.id,
                                'Для того щоб подивитись розклад будь якої групи на сьогодні введи її назву')
        bot.register_next_step_handler(sent, show_other_group)


@bot.message_handler(commands=['start'])
def start(message):
    sent = bot.send_message(message.chat.id, 'Вітаю, {}, я хороший Бот який допоможе тобі швидко дізнаватись свій розклад.'
                                             ' Для початку скажи мені свою групу (Напр. 44_і_д)'.format(message.chat.first_name))
    bot.register_next_step_handler(sent, set_group)


def set_group(message):

    add_user_to_db(message.chat.id, message.text)

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    keyboard.row('На сьогодні', 'На завтра', 'На тиждень')
    keyboard.row('Підписатися', 'Час пар', 'Змінити групу')
    keyboard.row('Розклад іншої групи', 'Інформація')

    sent = bot.send_message(message.chat.id, 'Чудово, від тепер я буду показувати розклад для групи {}.'.
                            format(message.text), reply_markup=keyboard)

    bot.register_next_step_handler(sent, menu_action)


@bot.message_handler(content_types=["text"])
def main_menu(message):

    if check_user_if_exist(message.chat.id):

        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

        keyboard.row('На сьогодні', 'На завтра', 'На тиждень')
        keyboard.row('Підписатися', 'Час пар', 'Змінити групу')
        keyboard.row('Розклад іншої групи', 'Інформація')

        sent = bot.send_message(message.chat.id, '...', reply_markup=keyboard)

        bot.register_next_step_handler(sent, menu_action)

    else:
        bot.send_message(message.chat.id, 'Щоб вказати групу введіть /start')


def show_other_group(message):

    group = message.text
    rozklad_data = get_rozklad(group=group)

    rozklad_for_today = '[Розклад на сьогодні групи {}]:\n'.format(message.text)

    if rozklad_data:
        rozklad_for_today += show_day_rozklad(rozklad_data[0])
    else:
        rozklad_for_today += 'На сьогодні пар не знайдено.\n'

    bot.send_message(message.chat.id, rozklad_for_today)


#  ____________________________________________________SERVER__________________________________________________________
server = Flask(__name__)


@server.route("/bot", methods=['POST'])
def get_new_updates():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://fathomless-everglades-21175.herokuapp.com/bot")
    return "!", 200


def main():

    server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))

if __name__ == '__main__':
    main()
