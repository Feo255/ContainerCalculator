from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiohttp import request
#from app.database.requests import get_categories, get_cards_by_category

#terminals = ['Быково', 'Кольцово', 'Окружное']

menu = ReplyKeyboardMarkup(keyboard=[
                            [KeyboardButton(text='Рассчиать')]
                            ],
                            resize_keyboard=True,
                            input_field_placeholder='Начните создание расчёта...')

container_kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text='20ф'),
                                KeyboardButton(text='40ф'),
                                 KeyboardButton(text='2х20ф')]
                              ],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите вариант 👇')



yesno_kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text='Да'),
                                KeyboardButton(text='Нет')]
                              ],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите вариант 👇')

marsh_kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text='Полный (3 точки)'),
                                KeyboardButton(text='Перемещение (2 точки между терминалами')]
                              ],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите вариант 👇')


async def terminals_list(terminals):
    keyboard = ReplyKeyboardBuilder()
    for terminal in terminals[:10]:
        keyboard.row(KeyboardButton(text=terminal))

    return keyboard.as_markup(resize_keyboard=True)

coment_kb = ReplyKeyboardMarkup(keyboard=[
                                [KeyboardButton(text='Дорого'),
                                KeyboardButton(text='Дёшево')]
                              ],
                                resize_keyboard=True,
                                input_field_placeholder='Выберите вариант 👇')