import asyncio
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('testprojectforpython-462411-8123c3554bd6.json', scopes=SCOPES)
client = gspread.authorize(creds)

async def fetch_sheet_data():
    # Вся работа с gspread — в отдельном потоке
    def get_data():
        spreadsheet = client.open_by_key('1VMjgQ6JijArovFY6j7SDQ3rk3F3d-Gtg0xyr3veoLoM')
        worksheet = spreadsheet.worksheet('Лист1')
        data = worksheet.get_all_values()
        return data

    data = await asyncio.to_thread(get_data)

    list_of_terms = []
    dict_terms = {}

    for row in data:
        list_of_terms.append(row[0])
        key = row[0]
        value = row[1]
        dict_terms[key] = value

    first_ = list_of_terms.pop(0)
    first_key = next(iter(dict_terms))
    first_value = dict_terms.pop(first_key)

    return dict_terms, list_of_terms

# Пример вызова в асинхронной функции:
#async def main():
#    dict_terms, list_of_terms = await fetch_sheet_data()
#    print(dict_terms)
#    print(list_of_terms)

# Для теста:
#if __name__ == '__main__':
 #   asyncio.run(main())

async def fetch_sheet_companies(inn):
    def get_data():
        spreadsheet = client.open_by_key('1VMjgQ6JijArovFY6j7SDQ3rk3F3d-Gtg0xyr3veoLoM')
        worksheet = spreadsheet.worksheet('Лист2')
        data = worksheet.get_all_values()
        return data

    data = await asyncio.to_thread(get_data)
    company = None
    fallback_company = None  # Если понадобится "дефолтная" строка с '-'

    for row in data:
        if inn == row[2]:
            company = {
                "stavka_nds": row[3],
                "tarif_km_nds": row[4],
                "tarif_prostoi_nds": row[5],
                "tarif_peregruz_nds": row[6],
                "stavka_nonds": row[7],
                "tarif_km_nonds": row[8],
                "tarif_prostoi_nonds": row[9],
                "tarif_peregruz_nonds": row[10]
            }
            print(company)
            return company
        elif "-" in row:
            # Сохраняем дефолтную строку, но не возвращаем сразу
            fallback_company = {
                "stavka_nds": row[3],
                "tarif_km_nds": row[4],
                "tarif_prostoi_nds": row[5],
                "tarif_peregruz_nds": row[6],
                "stavka_nonds": row[7],
                "tarif_km_nonds": row[8],
                "tarif_prostoi_nonds": row[9],
                "tarif_peregruz_nonds": row[10]
            }

    # Если не нашли по ИНН, возвращаем дефолтную строку (если она была)
    if fallback_company:
        print(fallback_company)
        return fallback_company

async def async_append_rows_to_sheet(api_list):
    def append_rows():
        sheet_id ='1VMjgQ6JijArovFY6j7SDQ3rk3F3d-Gtg0xyr3veoLoM'
        worksheet_name = 'Результаты'
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        worksheet.append_rows([api_list], value_input_option='USER_ENTERED')
    await asyncio.to_thread(append_rows)







