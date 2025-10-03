#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import math
import folium
from geopy.geocoders import Nominatim
import flexpolyline as fp
import random


# 使用到的MAP API KEY:
API_KEY_1 = ""  #HERE API(用於get_map get_travel_times)
API_KEY_2 = ""  #GOOGLE MAP API(用於get_coordinates get_address find_nearby_restaurant)


# 將多個子陣列的陣列依照指定大小切分為多個群組
def split_array(array, chunk_size):
    return [array[i:i + chunk_size] for i in range(0, len(array), chunk_size)]

# Haversine公式計算球面距離
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 地球半徑（公里）
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 尋找兩地點的中間地點
def get_midpoint(lat1, lon1, lat2, lon2):
    mid_lat = (lat1 + lat2) / 2
    mid_lon = (lon1 + lon2) / 2
    
    return mid_lat, mid_lon

# 獲取地點座標資料
def get_coordinate(attraction):
    api_key = API_KEY_2
    
    coordinate = []
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": attraction,
        "key": api_key,
        "language": "zh-TW"  # 使用繁體中文返回結果
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            result = data["results"][0]
            name = attraction
            lat = result["geometry"]["location"]["lat"]
            lon = result["geometry"]["location"]["lng"]
            formatted_address = result["formatted_address"]
            return (name, lat, lon, formatted_address)
        else:
            return False
    else:
        return False

# 用座標查詢中文地址
def get_address(lat, lon):
    # Google Maps Geocoding API 的 URL
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    api_key = API_KEY_2
    
    # 請求參數
    params = {
        "latlng": f"{lat},{lon}",
        "key": api_key,
        "language": "zh-TW"  # 指定返回結果為繁體中文
    }
    
    try:
        # 發送 API 請求
        response = requests.get(url, params=params)
        response.raise_for_status()  # 檢查是否成功請求
        data = response.json()
        
        # 提取地址
        if "results" in data and len(data["results"]) > 0:
            # 使用第一個結果作為地址
            formatted_address = data["results"][0].get("formatted_address", "地址未知")
            return formatted_address
        else:
            print("未找到相關地址資訊。")
            return "地址未知"
    except requests.exceptions.RequestException as e:
        print(f"地址查詢失敗: {e}")
        return "地址未知"

# 創建距離矩陣
def create_distance_matrix(locations):
    size = len(locations)
    matrix = [[0] * size for _ in range(size)]
    for i in range(size):
        for j in range(size):
            if i != j:
                lat1, lon1 = locations[i][1], locations[i][2]
                lat2, lon2 = locations[j][1], locations[j][2]
                matrix[i][j] = haversine(lat1, lon1, lat2, lon2)
    return matrix

# TSP 路徑分析 - simulated annealing
def simulated_annealing(locations, initial_temperature=1000, cooling_rate=0.995, max_iterations=10000):
    distance_matrix = create_distance_matrix(locations)  
    n = len(distance_matrix)
    
    # 初始化
    current_route = list(range(n))  # 初始路徑 [0, 1, 2, ..., n-1]
    random.shuffle(current_route)
    current_distance = calculate_route_distance(distance_matrix, current_route)
    best_route = current_route[:]
    best_distance = current_distance

    temperature = initial_temperature

    for iteration in range(max_iterations):
        # 隨機交換兩個地點的位置
        new_route = current_route[:]
        i, j = random.sample(range(n), 2)
        new_route[i], new_route[j] = new_route[j], new_route[i]

        # 計算新路徑的距離
        new_distance = calculate_route_distance(distance_matrix, new_route)

        # 接受或拒絕新路徑
        if accept_solution(current_distance, new_distance, temperature):
            current_route = new_route
            current_distance = new_distance
            # 如果新路徑更好，更新最佳路徑
            if new_distance < best_distance:
                best_route = new_route
                best_distance = new_distance

        # 降低溫度
        temperature *= cooling_rate
        if temperature < 1e-8:  # 終止條件：溫度過低
            break
    
    # 根據最佳路徑返回相應的完整地點數據
    route_locations = [locations[i] for i in best_route]

    # 返回排序後的完整地點及最佳距離
    return route_locations

def calculate_route_distance(distance_matrix, route):
    """計算路徑的總距離，包括回到起點"""
    return sum(distance_matrix[route[i]][route[i+1]] for i in range(len(route) - 1)) + distance_matrix[route[-1]][route[0]]

def accept_solution(current_distance, new_distance, temperature):
    """根據 Metropolis 准則決定是否接受新解"""
    if new_distance < current_distance:
        return True
    return random.random() < math.exp((current_distance - new_distance) / temperature)

# 獲取座標所在的縣市名稱
def get_county(lat, lon):
    # 初始化 geolocator
    geolocator = Nominatim(user_agent="myGeocoder")
    
    try:
        # 進行反向查詢
        location = geolocator.reverse((lat, lon), language='en', timeout=10)
        
        if location:
            #print(f"反向查詢返回的原始數據: {location.raw}")  # 打印返回的原始數據
            
            # 獲取地址信息
            address = location.raw.get('address', {})
            
            # 優先獲取 city 或 suburb，若無則使用 county
            city = address.get('city', '') or address.get('town', '') or address.get('village', '')
            county = address.get('county', 'Unknown')
            country = address.get('country', 'Unknown')
            
            # 如果 county 依然有值，檢查並去掉「County」字樣
            if "County" in county:
                county = county.replace("County", "").strip()
            
            # 如果 city 和 county 都無法正確提取，可以選擇返回更具體的地理位置
            if not city:
                city = county  # 如果找不到城市，返回 county 作為城市
            
            return f"{city}, {country}"
        
        else:
            print(f"反向查詢未找到位置: ({lat}, {lon})")  # 如果沒有找到位置，打印座標
            return 'Unknown'
    
    except Exception as e:
        print(f"Error during geocoding: {e}")  # 打印具體錯誤信息
        return 'Unknown'

# 生成路徑地圖
def get_map(locations, transMode="car"):
    # API 密鑰
    api_key = API_KEY_1
    
    all_coordinates = []
    
    # 遍歷所有相鄰地點並獲取路徑
    for i in range(len(locations) - 1):
        origin = f"{locations[i][1]},{locations[i][2]}"  # 起點
        destination = f"{locations[i+1][1]},{locations[i+1][2]}"  # 終點
        
        # 設置移動方式
        transportMode = transMode
        
        # 構建請求 URL
        url = f"https://router.hereapi.com/v8/routes?transportMode={transportMode}&origin={origin}&destination={destination}&return=summary,polyline&apiKey={api_key}"
        
        # 發送 GET 請求
        response = requests.get(url)
        
        # 檢查請求是否成功
        if response.status_code == 200:
            route_data = response.json()
            
            # 提取路徑的 polyline
            route_info = route_data['routes'][0]['sections'][0]
            polyline_data = route_info.get('polyline')
            
            # 解碼 polyline
            coordinates = fp.decode(polyline_data)
            
            # 假設我們只選擇寬度大於 10 米的道路
            filtered_coordinates = [coord for coord in coordinates if coord[0] > 10]
            all_coordinates.extend(filtered_coordinates)  # 添加到總路徑中
        else:
            print(f"請求失敗，狀態碼: {response.status_code}")
            return None
    
    # 設定起點座標作為地圖的中心
    start_coords = all_coordinates[0]
    
    # 創建地圖
    m = folium.Map(location=start_coords, zoom_start=12)
    
    # 在地圖上繪製路徑
    folium.PolyLine(all_coordinates, color='blue', weight=5, opacity=0.7).add_to(m)
    
    # 在每個地點添加標記
    for loc in locations:
        name, lat, lng, address = loc
        folium.Marker([lat, lng], popup=name).add_to(m)
    
    # 返回生成的地圖對象
    # print("路徑地圖完成!")
    return m

# 尋找地點附近的餐廳
def find_nearby_restaurant(lat, lon, radius=300, limit=1, max_radius=10000, step=300):
    api_key = API_KEY_2
    
    places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    selected_places = []
    
    while radius <= max_radius:
        params = {
            "location": f"{lat},{lon}",
            "radius": radius,
            "type": "restaurant",
            "key": api_key,
            "language": "zh-TW"  # 使用繁體中文返回地點名稱與地址
        }
        
        try:
            # 發送 API 請求
            response = requests.get(places_url, params=params)
            response.raise_for_status()
            data = response.json()

            # 檢查是否有結果
            if "results" in data and data["results"]:
                for result in data["results"]:
                    name = result.get("name", "Unnamed")  # 獲取地點名稱
                    place_lat = result["geometry"]["location"]["lat"]
                    place_lon = result["geometry"]["location"]["lng"]
                    address = result.get("vicinity", "地址未知")  # 簡單地址（附近地點）

                    # 過濾未命名地點
                    if name != "Unnamed":
                        selected_places.append([name, place_lat, place_lon, address])

                # 若找到足夠數量的地點，停止搜尋
                if len(selected_places) >= limit:
                    break

        except requests.exceptions.RequestException as e:
            print(f"請求失敗: {e}")
            return []
        except KeyError as e:
            print(f"數據解析失敗: {e}")
            return []

        # 擴大搜尋範圍
        radius += step

    if selected_places:
        # 隨機選擇地點
        return random.sample(selected_places, k=min(limit, len(selected_places)))

    # 若超過最大範圍仍無結果，返回提示
    print("未能找到符合條件的地點。")
    return []

# 尋找地點附近的旅館
def find_nearby_hotel(lat, lon, radius=300, limit=1, max_radius=10000, step=300):
    overpass_url = "http://overpass-api.de/api/interpreter"

    while radius <= max_radius:
        query = f"""
            [out:json];
            node["tourism"="hotel"](around:{radius},{lat},{lon});
            out;
        """

        try:
            # 發送 API 請求
            response = requests.get(overpass_url, params={'data': query})
            response.raise_for_status()  # 如果請求失敗會拋出 HTTPError
            data = response.json()

            # 收集地點數據
            all_places = []
            for element in data.get('elements', []):
                name = element.get("tags", {}).get("name", "Unnamed")
                lat = element.get("lat")
                lon = element.get("lon")

                if name != "Unnamed":  # 過濾掉未命名的地點
                    all_places.append([name, lat, lon, ""])

            # 若已收集到足夠數量的地點，停止搜尋
            if len(all_places) >= limit:
                break

        except requests.exceptions.RequestException as e:
            print(f"請求失敗: {e}")
            return []
        except KeyError as e:
            print(f"數據解析失敗: {e}")
            return []

        # 擴大搜尋半徑
        radius += step

    if all_places:
        # 隨機選擇地點
        selected_places = random.sample(all_places, k=min(limit, len(all_places)))
        # 為隨機選擇的地點查詢地址
        for place in selected_places:
            name, lat, lon, _ = place
            place[3] = get_address(lat, lon)  # 查詢地址並更新列表
        return selected_places

    # 若超過最大範圍仍無結果，返回提示
    print("未能找到符合條件的地點。")
    return []


# 將景點陣列增加餐廳和旅館
def add_restaurant_and_hotel(group):
    loc1 = group[0]
    loc2 = group[1]
    loc3 = group[2]

    loc_name1, lat1, lon1 = loc1[0], loc1[1], loc1[2]
    loc_name2, lat2, lon2 = loc2[0], loc2[1], loc2[2]

    midpoint_lat, midpoint_lon = get_midpoint(lat1, lon1, lat2, lon2)
    lunch = find_nearby_restaurant(midpoint_lat, midpoint_lon)
    
    group.insert(1, lunch[0])

    dinner = find_nearby_restaurant(loc3[1], loc3[2])
    group.append(dinner[0])

    hotel = find_nearby_hotel(loc3[1], loc3[2])
    group.append(hotel[0])

    return group

# 獲取估計移動時間
def get_travel_times(locations, transport_mode="car", error=0):
    api_key = API_KEY_1
    
    travel_times = []

    # 遍歷每兩個連續地點
    for i in range(len(locations) - 1):
        origin = f"{locations[i][1]},{locations[i][2]}"
        destination = f"{locations[i + 1][1]},{locations[i + 1][2]}"

        # 構建請求 URL
        url = (
            f"https://router.hereapi.com/v8/routes"
            f"?transportMode={transport_mode}"
            f"&origin={origin}"
            f"&destination={destination}"
            f"&return=summary"
            f"&apiKey={api_key}"
        )

        # 發送 GET 請求
        response = requests.get(url)

        if response.status_code == 200:
            # 解析 JSON 回應
            route_data = response.json()
            duration = route_data['routes'][0]['sections'][0]['summary']['duration']
            travel_times.append(duration // 60 + error)  # 將秒數轉換為分鐘
        else:
            print(f"請求失敗，狀態碼: {response.status_code}")
            travel_times.append(None)  # 如果失敗，填入 None

    return travel_times


def generate_route(attractions):
    # 尋找最佳路徑
    print("地點資訊已獲取，正在計算最佳路徑...")
    sorted_locations = simulated_annealing(attractions)
    
    # 將景點分組
    grouped_locations = split_array(sorted_locations, 3)
    
    # 為每組景點添加餐廳和旅館
    print("正在尋找餐廳和旅館...")
    grouped_locations = [add_restaurant_and_hotel(group) for group in grouped_locations]
    
    # 獲取移動時間
    print("正在計算交通時間...")
    travel_times = [get_travel_times(group, "car", error=10) for group in grouped_locations]
    
    # 創建地圖
    print("正在生成路線圖...")
    route_map = [get_map(group, "car") for group in grouped_locations]
    
    print("旅遊行程與路線圖已生成！")
    
    return route_map, grouped_locations, travel_times


# In[ ]:




