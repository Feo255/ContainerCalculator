import openrouteservice
import os
import requests
from shapely.geometry import Point, Polygon
from dotenv import load_dotenv

load_dotenv()

def geocode_address(address: str) -> tuple:
    api_key = os.getenv('AD_TOKEN')
    secret_key = os.getenv('AD_SECRET')

    if not api_key or not secret_key:
        raise ValueError("API-ключ и/или секретный ключ DaData не найдены в .env")

    url = "https://cleaner.dadata.ru/api/v1/clean/address"
    headers = {
        "Authorization": f"Token {api_key}",
        "X-Secret": secret_key,
        "Content-Type": "application/json"
    }
    data = [address]
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    if not result or not result[0].get("geo_lat"):
        return None
    return (float(result[0]["geo_lat"]), float(result[0]["geo_lon"]))
address = "Россия, МО, Красногорк, Павшинский бульвар, 1"
coordinates = geocode_address(address)
print(coordinates)


def find_nearest_exit(target_coords: tuple, api_key: str) -> dict:
    import csv
    from geopy.distance import great_circle

    # Загружаем съезды
    exits = []
    with open('exits_csv.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            exits.append((float(row['lat']), float(row['lon'])))
    print(exits)
    mkad_polygon = Polygon([(lon, lat) for lat, lon in exits])
    lat, lon = target_coords
    point = Point(lon, lat)
    if mkad_polygon.contains(point):
        return 0

    # Находим 5 ближайших по прямой
    distances = [(exit_coords, great_circle(target_coords, exit_coords).km)
                 for exit_coords in exits]
    candidates = sorted(distances, key=lambda x: x[1])[:5]
    print(candidates)

    # Уточняем через API маршрутизации
    min_distance = float('inf')
    nearest_exit = None

    for (exit_coords, _) in candidates:
        route = get_ors_route(exit_coords, target_coords, api_key)
        if route['distance'] < min_distance:
            min_distance = route['distance']
            nearest_exit = exit_coords

    return min_distance

def get_ors_route(start: tuple, end: tuple, api_key: str) -> dict:
    """
    Возвращает маршрут между двумя точками через OpenRouteService.
    start, end: (lat, lon)
    api_key: ключ OpenRouteService
    Возвращает словарь с ключами 'distance' (в метрах) и 'duration' (в секундах)
    """
    client = openrouteservice.Client(key=api_key)
    # ORS требует координаты в формате (lon, lat)
    coords = [(start[1], start[0]), (end[1], end[0])]
    try:
        route = client.directions(coords, profile='driving-car')
        summary = route['routes'][0]['summary']
        return {
            'distance': summary['distance'],   # в метрах
            'duration': summary['duration']    # в секундах
        }
    except Exception as e:
        print(f"Ошибка OpenRouteService: {e}")
        return {'distance': float('inf'), 'duration': float('inf')}

#def get_yandex_route(start: tuple, end: tuple, api_key: str) -> dict:
#    url = "https://api.routing.yandex.net/v2/route"
#    params = {
#        "apikey": api_key,
#        "waypoints": f"{start[1]},{start[0]}|{end[1]},{end[0]}",
#        "mode": "driving"
#    }
#    response = requests.get(url, params=params)
#    data = response.json()
#    print("Ответ Яндекс.Карт:", data)
#    if 'route' not in data:
#        print(f"Маршрут не найден или ошибка: {data}")
#        return {'distance': float('inf'), 'duration': float('inf')}
#    return data['route']

#address = "24-й проезд, 1к1, Владимир"
#coordinates = geocode_address(address)
#print(coordinates)
#api='5b3ce3597851110001cf624851b6bbb750f6431e94dfe06730b82c26'
#result = find_nearest_exit(coordinates, api)
#print(result/1000)
