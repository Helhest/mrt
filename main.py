import csv
import random
import math
import re # regular expresions
import networkx  as nx# for editing and creating graphs
from collections import defaultdict 


def get_station(file_name):
    with open(file_name,'r',encoding='utf-8') as f:
        return list(csv.DictReader(f))
    

def get_code(stations):
    all_codes = set()
    map = defaultdict(list)

    for station in stations:
        codes = station['STN_NO'].split('/')
        all_codes.update(codes)
        map[station['STN_NAME']].extend(codes)

    return all_codes, map

def station_line(station_codes):
    grouped = defaultdict(list)
    for code in station_codes:
        match = re.match(r'([A-Z]+)\d*', code)
        if match:
            line = match.group(1)
            grouped[line].append(code)
        else:
            print(f"skip station code invalid: {code}")
    return grouped

def sort_stations_num(line_stations):
    def extract_num(code):
        match = re.search(r'\d+', code)
        return int(match.group()) if match else 0
    
    for line in line_stations:
        line_stations[line].sort(key=extract_num)
    return line_stations

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_l = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_l / 2) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)) 

    return R * c


def add_line_edge(graph, line_stations, loop_lines):
    speed = 40 #km

    for line, stations in line_stations.items():
        for i in range(len(stations) -1):
            a, b = stations[i] , stations[i+1]
            lat1, lon1 = graph.nodes[a]['lat'], graph.nodes[a]['lon']
            lat2, lon2 = graph.nodes[b]['lat'], graph.nodes[b]['lon']
            distance_km = haversine(lat1, lon1, lat2, lon2) 
            time_min = (distance_km / speed) * 60
            graph.add_edge(a, b, weight=round(time_min, 2))
        if line in loop_lines and len(stations) > 1:
            a, b = stations[-1], stations[0]
            lat1, lon1 = graph.nodes[a]['lat'], graph.nodes[a]['lon']
            lat2, lon2 = graph.nodes[b]['lat'], graph.nodes[b]['lon']
            distance_km = haversine(lat1, lon1, lat2, lon2)
            time_min = (distance_km / speed) * 60
            graph.add_edge(a, b, weight=round(time_min, 2))

def add_transfer_edges(graph, map):
    for codes in map.values():
        if len(codes) > 1:
            for i in range(len(codes)):
                for j in range(i + 1, len(codes)):
                    graph.add_edge(codes[i], codes[j], weight=3)
    

def build_metro_graph(file_name): 
    loop_lines = {"CC"}
    graph = nx.Graph()

    stations = get_station(file_name)
    station_codes, map = get_code(stations)
    graph.add_nodes_from(station_codes)

    line_groups = station_line(station_codes)
    sorted_lines = sort_stations_num(line_groups)

    add_line_edge(graph, sorted_lines, loop_lines)
    add_transfer_edges(graph, map)

    return graph

def coordinates(graph, stations):
    for station in stations:
        codes = station['STN_NO'].split('/')
        lat = float(station['Latitude'])
        lon = float(station['Longitude'])
        for code in codes:
            graph.nodes[code]['lat'] = lat
            graph.nodes[code]["lon"] = lon

def short_path(graph, start, end):
    try:
        return nx.shortest_path(graph, source=start, target=end)
    except nx.NetworkXNoPath:
        return None
    
def fast_path(graph, start, end):
    try:
        path = nx.shortest_path(graph, source=start, target=end, weight='weight')
        time = sum(graph[path[i]][path[i + 1]]['weight'] for i in range(len(path) - 1)) 
        return path, time
    except nx.NetworkXNoPath:
        return None, None
    
if __name__ == "__main__":
    file_name = 'stations.csv'
    graph = build_metro_graph('stations.csv')

    start = 'NS16'
    end = 'EW32'

    shortest_path = short_path(graph, start, end)
    if shortest_path:
        print(f"Shortest path: {' -> '.join(shortest_path)} ({len(shortest_path) - 1} stops)")
    else:
        print("No available path for shortest route.")

    fastest_path, total_time = fast_path(graph, start, end)

    if fastest_path:
        print(f"Fastest route: {' -> '.join(fastest_path)} (Total time: {total_time} mins)")
    else:
        print("No available path for fastest route.")