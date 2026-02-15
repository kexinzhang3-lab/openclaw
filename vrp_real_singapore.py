#!/usr/bin/env python3
"""
VRP (Vehicle Routing Problem) Solution for Singapore Logistics
使用 OR-Tools 解决新加坡物流路径优化问题
输出交互式地图：Singapore_route_map.html
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import folium
from folium.plugins import AntPath
import math

# ============================================================================
# Task 1: 硬编码 25 个新加坡真实地点数据
# ============================================================================

LOCATIONS = [
    # Depots & Hubs
    {"name": "Jurong West DC (Main Depot)", "lat": 1.3404, "lon": 103.7090, "demand": 0},
    {"name": "Changi Airfreight Centre", "lat": 1.3644, "lon": 103.9915, "demand": 20},
    {"name": "Tuas Industrial Hub", "lat": 1.3200, "lon": 103.6368, "demand": 15},
    {"name": "PSA Pasir Panjang Terminal", "lat": 1.2800, "lon": 103.7850, "demand": 18},
    # North
    {"name": "Woodlands Checkpoint", "lat": 1.4360, "lon": 103.7860, "demand": 12},
    {"name": "Yishun Northpoint City", "lat": 1.4295, "lon": 103.8358, "demand": 8},
    {"name": "Sembawang Shopping Centre", "lat": 1.4417, "lon": 103.8286, "demand": 6},
    {"name": "Seletar Aerospace Park", "lat": 1.4177, "lon": 103.8687, "demand": 10},
    # North-East
    {"name": "Punggol Waterway Point", "lat": 1.4067, "lon": 103.9022, "demand": 9},
    {"name": "Sengkang Compass One", "lat": 1.3916, "lon": 103.8949, "demand": 7},
    {"name": "Serangoon Nex", "lat": 1.3506, "lon": 103.8718, "demand": 8},
    # East
    {"name": "Tampines Hub", "lat": 1.3524, "lon": 103.9443, "demand": 10},
    {"name": "Pasir Ris Interchange", "lat": 1.3732, "lon": 103.9493, "demand": 6},
    {"name": "Bedok Mall", "lat": 1.3241, "lon": 103.9295, "demand": 8},
    {"name": "Changi Business Park", "lat": 1.3340, "lon": 103.9644, "demand": 11},
    # Central / CBD
    {"name": "Marina Bay Sands (VIP)", "lat": 1.2834, "lon": 103.8607, "demand": 15},
    {"name": "Suntec City", "lat": 1.2935, "lon": 103.8572, "demand": 9},
    {"name": "Orchard Ion", "lat": 1.3040, "lon": 103.8318, "demand": 12},
    {"name": "Bishan Junction 8", "lat": 1.3500, "lon": 103.8485, "demand": 7},
    {"name": "Toa Payoh Hub", "lat": 1.3323, "lon": 103.8475, "demand": 6},
    {"name": "Ang Mo Kio Hub", "lat": 1.3695, "lon": 103.8483, "demand": 7},
    # West
    {"name": "NTU (Nanyang Tech)", "lat": 1.3483, "lon": 103.6831, "demand": 5},
    {"name": "Clementi Mall", "lat": 1.3150, "lon": 103.7651, "demand": 6},
    {"name": "NUS (National Univ)", "lat": 1.2966, "lon": 103.7764, "demand": 8},
    {"name": "Jurong East IMM", "lat": 1.3329, "lon": 103.7436, "demand": 10},
]

# ============================================================================
# 辅助函数：计算两点之间的距离（米）
# ============================================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """计算两个经纬度点之间的距离（公里）"""
    R = 6371  # 地球半径（公里）
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c * 1000  # 转换为米

# ============================================================================
# Task 2: OR-Tools VRP 优化
# ============================================================================

def create_data_model():
    """创建 VRP 数据模型"""
    data = {}
    data["locations"] = [(loc["lat"], loc["lon"]) for loc in LOCATIONS]
    data["demands"] = [loc["demand"] for loc in LOCATIONS]
    data["num_vehicles"] = 5
    data["depot"] = 0  # Jurong West DC 是起点
    
    # 车辆容量
    data["vehicle_capacities"] = [40] * data["num_vehicles"]
    
    # 距离矩阵
    num_locations = len(LOCATIONS)
    data["distance_matrix"] = [[0] * num_locations for _ in range(num_locations)]
    
    for i in range(num_locations):
        for j in range(num_locations):
            if i != j:
                lat1, lon1 = data["locations"][i]
                lat2, lon2 = data["locations"][j]
                data["distance_matrix"][i][j] = int(haversine_distance(lat1, lon1, lat2, lon2))
    
    return data

def solve_vrp():
    """求解 VRP 问题"""
    data = create_data_model()
    
    # 创建路由索引管理器
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]),
        data["num_vehicles"],
        data["depot"]
    )
    
    # 创建路由模型
    routing = pywrapcp.RoutingModel(manager)
    
    # 距离回调函数
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # 添加容量约束
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]
    
    demand_callback_index = routing.RegisterCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # 空驶惩罚
        data["vehicle_capacities"],  # 车辆容量
        True,  # 起点也计入容量
        "Capacity"
    )
    
    # 设置搜索参数
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 30
    
    # 求解
    print("🚀 开始求解 VRP 问题...")
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution:
        return solution, manager, routing, data
    else:
        print("❌ 无法找到解决方案")
        return None, manager, routing, data

# ============================================================================
# Task 3: Folium 交互式地图可视化
# ============================================================================

def create_map(solution, manager, routing, data):
    """创建交互式地图"""
    print("🗺️ 正在生成地图...")
    
    # 计算新加坡中心点
    center_lat = sum(loc["lat"] for loc in LOCATIONS) / len(LOCATIONS)
    center_lon = sum(loc["lon"] for loc in LOCATIONS) / len(LOCATIONS)
    
    # 创建地图
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='CartoDB positron'
    )
    
    # 颜色配置（5辆车）
    vehicle_colors = ['red', 'blue', 'green', 'purple', 'orange']
    
    # 添加所有地点标记
    for idx, loc in enumerate(LOCATIONS):
        if idx == 0:
            # 仓库 - 红色家图标
            folium.Marker(
                location=[loc["lat"], loc["lon"]],
                popup=f"<b>{loc['name']}</b><br>Demand: {loc['demand']}<br>Stop #0 (Depot)",
                icon=folium.Icon(color='red', icon='home', prefix='fa'),
                tooltip=loc["name"]
            ).add_to(m)
        elif loc["name"] == "Marina Bay Sands (VIP)":
            # VIP - 金色星星
            folium.Marker(
                location=[loc["lat"], loc["lon"]],
                popup=f"<b>⭐ {loc['name']}</b><br>Demand: {loc['demand']}",
                icon=folium.Icon(color='orange', icon='star', prefix='fa'),
                tooltip=f"⭐ {loc['name']}"
            ).add_to(m)
        else:
            # 普通地点 - 蓝色信息图标
            folium.Marker(
                location=[loc["lat"], loc["lon"]],
                popup=f"<b>{loc['name']}</b><br>Demand: {loc['demand']}",
                icon=folium.Icon(color='blue', icon='info-sign'),
                tooltip=loc["name"]
            ).add_to(m)
    
    # 绘制路线
    total_distance = 0
    total_load = 0
    
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        route = []
        route_coords = []
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            loc = LOCATIONS[node]
            route_coords.append([loc["lat"], loc["lon"]])
            index = solution.Value(routing.NextVar(index))
        
        # 添加终点
        route.append(manager.IndexToNode(index))
        loc = LOCATIONS[manager.IndexToNode(index)]
        route_coords.append([loc["lat"], loc["lon"]])
        
        # 计算这辆车的距离
        vehicle_distance = 0
        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]
            vehicle_distance += data["distance_matrix"][from_node][to_node]
        
        total_distance += vehicle_distance
        
        # 只显示有路线的车辆
        if len(route) > 2:
            print(f"🚗 Vehicle {vehicle_id + 1}: {len(route) - 2} stops, {vehicle_distance/1000:.2f} km")
            
            # 使用 AntPath 添加动画路线
            AntPath(
                locations=route_coords,
                color=vehicle_colors[vehicle_id],
                weight=5,
                opacity=0.8,
                delay=800,
                dash_array=[10, 20],
                pulse_color='#FFFFFF'
            ).add_to(m)
    
    # 添加图例
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; 
                background-color: white; padding: 15px; border-radius: 5px;
                border: 2px solid grey; font-size: 14px;">
        <b>🚚 Vehicle Routes</b><br>
        <i class="fa fa-circle" style="color:red"></i> Vehicle 1<br>
        <i class="fa fa-circle" style="color:blue"></i> Vehicle 2<br>
        <i class="fa fa-circle" style="color:green"></i> Vehicle 3<br>
        <i class="fa fa-circle" style="color:purple"></i> Vehicle 4<br>
        <i class="fa fa-circle" style="color:orange"></i> Vehicle 5<br>
        <hr>
        <b>📍 Markers</b><br>
        <i class="fa fa-home" style="color:red"></i> Depot (Jurong West)<br>
        <i class="fa fa-star" style="color:orange"></i> VIP (Marina Bay)<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 添加标题
    title_html = '''
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
                z-index: 1000; background-color: white; padding: 10px 20px;
                border-radius: 5px; border: 2px solid grey; font-size: 18px;">
        <b>🚚 Singapore VRP Optimization</b><br>
        <span style="font-size: 12px;">25 Locations | 5 Vehicles | Capacity 40</span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # 保存地图
    output_file = "Singapore_route_map.html"
    m.save(output_file)
    print(f"✅ 地图已保存到: {output_file}")
    
    return output_file, total_distance

# ============================================================================
# 主程序
# ============================================================================

def main():
    print("=" * 60)
    print("🚚 新加坡物流路径优化 (VRP)")
    print("=" * 60)
    print(f"📍 地点数量: {len(LOCATIONS)}")
    print(f"🚗 车辆数量: 5")
    print(f"📦 车辆容量: 40")
    print("=" * 60)
    
    # 求解 VRP
    solution, manager, routing, data = solve_vrp()
    
    if solution:
        print("\n✅ 优化完成！")
        print("=" * 60)
        
        # 生成地图
        output_file, total_distance = create_map(solution, manager, routing, data)
        
        print("\n" + "=" * 60)
        print("📊 优化结果汇总")
        print("=" * 60)
        print(f"🚚 总行驶距离: {total_distance/1000:.2f} km")
        print(f"🗺️ 地图文件: {output_file}")
        print("\n💡 提示: 用浏览器打开 Singapore_route_map.html 查看交互式地图")
        print("=" * 60)

if __name__ == "__main__":
    main()
