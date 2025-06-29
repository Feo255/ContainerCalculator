import os
from dotenv import load_dotenv

load_dotenv()

import aiohttp
import asyncio
import requests


async def get_company_info_by_inn(inn):
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"
    token = os.getenv('AD_TOKEN')
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {token}"
    }
    data = {
        "query": inn,
        "limit": 1
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data, headers=headers) as response:
            if response.status == 200:
                resp_json = await response.json()
                suggestions = resp_json.get('suggestions', [])
                if suggestions:
                    if len(inn) == 10:
                        first = suggestions[0]['data']

                        # Извлекаем ogrn
                        ogrn = first.get('ogrn')

                        # Извлекаем kpp из UL
                        kpp = first.get('kpp')

                        # Извлекаем название компании
                        full_name = first.get('name', {}).get('full_with_opf')
                        short_name = first.get('name', {}).get('short_with_opf')

                        full_address = first.get('address', {}).get('unrestricted_value')

                        name = first.get('management', {}).get('name')

                        surname = name.split(' ')[0]
                        name_ = name.split(' ')[1]
                        patronymic = name.split(' ')[2]

                        position = first.get('management', {}).get('post')
                        sh_name = f'{surname} {name_[0]}. {patronymic[0]}.'

                        result = {
                            'ogrn': ogrn,
                            'kpp': kpp,
                            'full': full_name,
                            'short': short_name,
                            'full_address': full_address,
                            'f_surname': surname,
                            'f_name': name_,
                            'f_patronymic': patronymic,
                            'position': position.lower(),
                            'sh_name': sh_name
                        }
                        return result
                    else:
                        first = suggestions[0]['data']
                        # Извлекаем ogrn
                        ogrn = first.get('ogrn')

                        # Извлекаем kpp из UL
                        kpp = ' '

                        # Извлекаем название компании
                        full_name = first.get('name', {}).get('full_with_opf')
                        short_name = first.get('name', {}).get('short_with_opf')

                        full_address = first.get('address', {}).get('unrestricted_value')

                        name = first.get('management', {}).get('name')

                        surname = first.get('fio', {}).get('surname')
                        name_ = first.get('fio', {}).get('name')
                        patronymic = first.get('fio', {}).get('patronymic')

                        position = first.get('opf', {}).get('full')

                        sh_name = f'{surname} {name_[0]}. {patronymic[0]}.'

                        result = {
                            'ogrn': ogrn,
                            'kpp': kpp,
                            'full': full_name,
                            'short': short_name,
                            'full_address': full_address,
                            'f_surname': surname,
                            'f_name': name_,
                            'f_patronymic': patronymic,
                            'position': position.lower(),
                            'sh_name': sh_name
                        }

                        return result
                else:
                    return None
            else:
                text = await response.text()
                print(f"Ошибка: {response.status} - {text}")
                return text

# Тестируйте

# async def main():
#    api_key = 'caf232daa238775a52103dd45321674c1798cf92'
#   inn = '481400883724'  # пример ИНН

#   info = await get_company_info_by_inn(inn)
#   if info:
#       print("Компания найдена:", info)
#    else:
#        print("Компания не найдена.")

# if __name__ == '__main__':
#    asyncio.run(main())