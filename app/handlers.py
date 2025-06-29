import os
import hashlib
import asyncio
from datetime import datetime
from posixpath import split
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton,InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


from numpy.ma.core import masked_where
from app.geolocation import find_nearest_exit, geocode_address, get_ors_route
import state_num

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.loggers import event
from aiogram.types import Message, CallbackQuery, BufferedInputFile, ReplyKeyboardRemove, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
from aiogram.fsm.context import FSMContext


from app.adata_int import get_company_info_by_inn
from app.googleshets import fetch_sheet_data, fetch_sheet_companies, async_append_rows_to_sheet
import app.keyboards as kb


from dotenv import load_dotenv



#from app.models.stamp import stamp_parsing

#from weasyprint.formatting_structure.build import capitalize

load_dotenv()

client = Router()


@client.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
        await message.answer("Вас приветствует бот для для расчёта стоимости контейнерной транспортировки\n\n"
                             "Нажмите кнопку внизу, чтобы начать расчёт",
                             reply_markup=kb.menu)

@client.message(F.text == 'Рассчиать')
async def start_pr(message: Message, state: FSMContext):
    state_num.number = state_num.number + 1
    number_ = state_num.number
    now = datetime.now()
    formatted_date = now.strftime("%d%m%Y")
    real_number = f'{number_}/{formatted_date}'
    await state.update_data(number=real_number)

    await message.answer('Введите ваш ИНН',
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state('reg_inn')

@client.message(StateFilter('reg_inn'))
async def inn_(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)

    inn = message.text
    if inn.isdigit() and len(inn) in (10, 12):
        adata = await get_company_info_by_inn(inn)
        if adata is None:
            await message.answer("Данные компании не обнаружены.\n"
                                     "Проверьте правильность ИНН заказчика и повторите ввод.")
            await state.set_state('reg_inn')
        elif adata is str:
            await message.answer(f"Ошибка работы сервиса adata {adata}.\n"
                                     "Проверьте правильность ИНН заказчика и повторите ввод.\n"
                                     "Если ошибка повторяется обратитесь за помощью в службу поддержки")
            await state.set_state('reg_inn')
        else:
            if adata['kpp'] == ' ':
                    ustav = 'свидетельства о государственной регистрации'
            else:
                    ustav = 'устава'

            await message.answer(f'Получены данные {adata['full']}')
            company = await fetch_sheet_companies(inn)
            await state.update_data(INN=inn, full_name=adata['full'], stavka_nds=company['stavka_nds'],
                                    tarif_km_nds=company['tarif_km_nds'], tarif_prostoi_nds=company['tarif_prostoi_nds'], tarif_peregruz_nds=company['tarif_peregruz_nds'],
                                    stavka_nonds=company['stavka_nonds'], tarif_km_nonds=company['tarif_km_nonds'], tarif_prostoi_nonds=company['tarif_prostoi_nonds'],
                                    tarif_peregruz_nonds=company['tarif_peregruz_nonds'])


            await message.answer('Выберите тип контейнера',
                                     reply_markup=kb.container_kb)

            await state.set_state('reg_container')
    else:
        await message.answer("Некорректный ввод. Введите ИНН ещё раз.")
        await state.set_state('reg_inn')

@client.message(StateFilter('reg_container'))
async def container_(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    container = message.text
    await state.update_data(container=container)
    if container == '2х20ф':
        await message.answer('Порожний?',
                             reply_markup=kb.yesno_kb)
        await state.set_state('reg_porozhnii')
    else:
        await message.answer('Введите массу груза',
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state('reg_massa')


@client.message(StateFilter('reg_porozhnii'))
async def poroz_(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    poroz = message.text
    if poroz == 'Да':
        await message.answer('Выберите тип маршрута',
                            reply_markup=kb.marsh_kb)
        await state.set_state('reg_marsh')
    else:
        await message.answer('Расчёт не возможен обратитесь, пожалуйста к логистам\n'
                             'Бот заканчивает работу и переходит в начало‼️‼️')
        await asyncio.sleep(3)
        await state.clear()
        await cmd_start(message, state)

@client.message(StateFilter('reg_massa'))
async def massa_(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    massa = message.text
    await state.update_data(massa=massa)
    cont_type = data['container']
    if massa.isdigit():
        if cont_type == '20ф' and int(massa) < 18:
            await state.update_data(peregruz_nds=0, peregruz_nonds=0)
            await message.answer('Выберите тип маршрута',
                                 reply_markup=kb.marsh_kb)

            await state.set_state('reg_marsh')
        elif cont_type == '40ф' and int(massa) < 20:
            await state.update_data(peregruz_nds=0, peregruz_nonds=0)
            await message.answer('Выберите тип маршрута',
                                 reply_markup=kb.marsh_kb)

            await state.set_state('reg_marsh')
        elif cont_type == '20ф' and int(massa) > 25:

            await message.answer('Расчёт не возможен обратитесь, пожалуйста к логистам\n'
                                 'Бот заканчивает работу и переходит в начало‼️‼️')
            await asyncio.sleep(3)
            await state.clear()
            await cmd_start(message, state)


        elif cont_type == '40ф' and int(massa) > 27:
            await message.answer('Расчёт не возможен обратитесь, пожалуйста к логистам\n'
                                 'Бот заканчивает работу и переходит в начало‼️‼️')
            await asyncio.sleep(3)
            await state.clear()
            await cmd_start(message, state)
        else:
            if cont_type == '20ф':
                peregruz_nds = (int(massa)-18)*int(data['tarif_peregruz_nds'])
                peregrez_nonds = (int(massa)-18)*(data['tarif_peregruz_nonds'])
                await state.update_data(peregruz_nds=peregruz_nds, peregruz_nonds=peregrez_nonds)
                await message.answer('Выберите тип маршрута',
                                     reply_markup=kb.marsh_kb)
            else:
                peregruz_nds = (int(massa) - 20) * int(data['tarif_peregruz_nds'])
                peregrez_nonds = (int(massa) - 20) * int(data['tarif_peregruz_nonds'])
                await state.update_data(peregruz_nds=peregruz_nds, peregruz_nonds=peregrez_nonds)
                await message.answer('Выберите тип маршрута',
                                 reply_markup=kb.marsh_kb)

            await state.set_state('reg_marsh')
    else:
        await message.answer("Некорректный ввод. масса должна состоять только из цифр.")
        await state.set_state('reg_massa')



@client.message(StateFilter('reg_marsh'))
async def marsh_(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    marsh = message.text

    dict_terms, list_of_terms = await fetch_sheet_data()
    await state.update_data(marsh=marsh, dict_terms=dict_terms, list_of_terms=list_of_terms)
    # здесь должно быть обращение в таблицу за списком и создание клавиатуры из него.
    await message.answer("Выберите из какого терминала должен начинаться маршрут\n"
                         "Введите начало названия от 3=х букв",
                         reply_markup=ReplyKeyboardRemove())

    await state.set_state('reg_term1')

@client.message(StateFilter('reg_term1'))
async def term1_(message: Message, state: FSMContext):
    data = await state.get_data()
    dict_terms = data['dict_terms']
    list_of_terms = data['list_of_terms']
    query = message.text.lower()
    # Находим совпадения
    matches = [word for word in list_of_terms if query in word.lower()]
    if not matches:
        await message.answer("Совпадений не найдено. Попробуйте еще раз.")
        return
    # Показываем клавиатуру с совпадениями
    #markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    #for match in matches[:10]:  # Ограничим 10 вариантами
    #    markup.add(KeyboardButton(match))
    await message.answer("Выберите терминал из списка:", reply_markup=await kb.terminals_list(matches))
    await state.set_state('reg_term11')

@client.message(StateFilter('reg_term11'))
async def term11_(message: Message, state: FSMContext):
    term1 = message.text
    data = await state.get_data()
    print(data)
    dict_terms = data['dict_terms']
    list_of_terms = data['list_of_terms']
    term1_km = dict_terms[term1]
    await state.update_data(term1=term1, term1_km=term1_km)
    if data['marsh'] == 'Полный (3 точки)':
        await message.answer("Введите адрес склада заказчика 👇 ",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state('reg_address')
    else:

        await message.answer("Выберите в какой терминал надо доставить контейнер\n"
                             "Введите начало названия от 3=х букв",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state('reg_term2')

@client.message(StateFilter('reg_address'))
async def address_(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)

    try:

        address = message.text
        loading_s = address.split(',')
        #address_c, address_r, address_g, address_s, address_h = loading_s
        #Этот адрес должен отправляться в яндекс фзш для расчёта расстояния от МКАД
        # ниже переменная должна равняться циферно результату подсчёта
        cordinates = geocode_address(address)
        api = os.getenv('ORS_TOKEN')
        address_km = find_nearest_exit(cordinates, api)
        address_km = int(address_km)/1000
        await state.update_data(address=address, address_km=address_km)

        data = await state.get_data()
        print(data)
        await message.answer("Выберите в какой терминал надо доставить контейнер\n"
                             "Введите начало названия от 3=х букв",
                             reply_markup=ReplyKeyboardRemove())
        await state.set_state('reg_term2')
    except Exception as e:
        await message.answer(
            f'Некорректный ввод. Ошибка: {e} Повторите пожалуйста\n')
        await state.set_state('reg_address')


@client.message(StateFilter('reg_term2'))
async def term2_(message: Message, state: FSMContext):
    data = await state.get_data()
    dict_terms = data['dict_terms']
    list_of_terms = data['list_of_terms']
    query = message.text.lower()
    # Находим совпадения
    matches = [word for word in list_of_terms if query in word.lower()]
    if not matches:
        await message.answer("Совпадений не найдено. Попробуйте еще раз.")
        return
    # Показываем клавиатуру с совпадениями
    #markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    #for match in matches[:10]:  # Ограничим 10 вариантами
    #    markup.add(KeyboardButton(match))
    await message.answer("Выберите терминал из списка:", reply_markup=await kb.terminals_list(matches))
    await state.set_state('reg_term22')

@client.message(StateFilter('reg_term22'))
async def term22_(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    dict_terms = data['dict_terms']
    term2 = message.text
    term2_km = dict_terms[term2]

    await state.update_data(term2=term2, term2_km=term2_km)
    data = await state.get_data()

    if data['marsh'] == 'Полный (3 точки)':
        result1 = int(data['stavka_nds']) + (int(data['term1_km']) * int(data['tarif_km_nds'])) + (int(data['address_km']) * int(data['tarif_km_nds'])) + (int(data['term2_km']) * int(data['tarif_km_nds'])) + int(data['peregruz_nds'])
        result2 = int(data['stavka_nonds']) + (int(data['term1_km']) * int(data['tarif_km_nonds'])) + (int(data['address_km']) * int(data['tarif_km_nonds'])) + (
                    int(data['term2_km']) * int(data['tarif_km_nonds'])) + int(data['peregruz_nonds'])
        await state.update_data(result1=result1, result2=result2)

        await message.answer(f"Маршрут: {data['term1']}-{data['address']}-{data['term2']}\n"
                             
                             f"Тарифы с НДС 20%\n"
                             f"{result1}P\n\n\n"
                             f"Тип контейнера: {data['container']}\n"
                             f"На выгрузку/погрузку контейнера 5 часов далее {data['tarif_prostoi_nds']}р/ч\n"
                             f"Масса груза {data['massa']} тонн.\n\n"
                             
                             f"Маршрут: {data['term1']}-{data['address']}-{data['term2']}\n"
                             f"Тарифы без НДС \n"
                             f"{result2}P\n\n\n"
                             
                             f"Тип контейнера: {data['container']}\n"
                             f"На выгрузку/погрузку контейнера 5 часов далее {data['tarif_prostoi_nonds']}р/ч\n"
                             f"Масса груза {data['massa']} тонн.\n\n",
                             reply_markup=ReplyKeyboardRemove())
        await message.answer("‼️👇Пожалуйста оставьте комметарий будем очень благодарны за обратную связь 👇‼️\n"
                             "Это так же перезапустит бота и позволит вам повторить расчёт.\n"
                             "Можете просто ввести одну букву")
        await state.set_state('reg_calc')
    else:
        result1 = (int(data['stavka_nds']) + (int(data['term1_km']) * int(data['tarif_km_nds'])) +
                   (int(data['term2_km']) * int(data['tarif_km_nds'])) + int(data['peregruz_nds']))
        result2 = (int(data['stavka_nonds']) + (int(data['term1_km']) * int(data['tarif_km_nonds'])) +
                   (int(data['term2_km']) * int(data['tarif_km_nonds'])) + int(data['peregruz_nonds']))
        await state.update_data(result1=result1, result2=result2)

        await message.answer(f"Маршрут: {data['term1']}-{data['term2']}\n"
                             f"Тарифы с НДС 20%\n"
                             f"{result1}Pn\n\n"
                             f"Тип контейнера: {data['container']}\n"
                             f"На выгрузку/погрузку контейнера 5 часов далее {data['tarif_prostoi_nds']}р/ч\n"
                             f"Масса груза {data['massa']} тонн.\n\n"
                             
                             f"Маршрут: {data['term1']}-{data['term2']}\n"
                             f"Тарифы без НДС \n"
                             f"{result2}P\n\n"
                             f"Тип контейнера: {data['container']}\n"
                             f"На выгрузку/погрузку контейнера 5 часов далее {data['tarif_prostoi_nonds']}р/ч\n"
                             f"Масса груза {data['massa']} тонн.\n\n",
                             reply_markup=ReplyKeyboardRemove())
        await message.answer(
                             "‼️👇Пожалуйста оставьте комметарий будем очень благодарны за обратную связь 👇‼️\n"
                             "Это так же перезапустит бота и позволит вам повторить расчёт.\n"
                             "Можете просто ввести одну букву",)
        await state.set_state('reg_calc')


@client.message(StateFilter('reg_calc'))
async def write_(message: Message, state: FSMContext):
    data = await state.get_data()
    print(data)
    comment = message.text
    keys_needed = ["number", "full_name", "INN", "term1", "term1_km", "address", "address_km", "term2", "term2_km", "container",
                   "peregruz_nds", "peregruz_nonds", "stavka_nds", "stavka_nonds", "result1", "result2"]
    selected_values = [data[key] for key in keys_needed if key in data]
    print(selected_values)
    selected_values.append(comment)
    await async_append_rows_to_sheet(selected_values)
    await message.answer("Спасибо за использование бота\n"
                         "Сейчас бот будет перезапущен")
    await asyncio.sleep(3)
    await state.clear()
    await cmd_start(message, state)


