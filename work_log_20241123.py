import numpy as np
import  pandas as pd 
import networkx as nx
import matplotlib.pyplot as plt
import geopandas as gpd
from geopy.distance import geodesic
import contextily as ctx

houses = pd.read_csv("minimal_example/synthetic_data/houses.csv")
regions= pd.read_csv("minimal_example/synthetic_data/regions.csv")
schools= pd.read_csv("minimal_example/synthetic_data/schools.csv")
stations= pd.read_csv("minimal_example/synthetic_data/stations.csv")

print(stations.head())

G = nx.Graph()

for _, row in houses.iterrows():
    G.add_node(
        row["property_id"],
        type="house",
        price=row["price"],
        rooms=row["rooms"],
        bathrooms=row["bathrooms"],
        surface_total=row["surface_total"],
        lat=row["lat"],
        lon=row["lon"],
    )


for _, row in stations.iterrows():
    G.add_node(
        row["poi_id"],
        type="train_station",
        daily_traffic=row["daily_traffic"],
        connections=row["connections"],
        lat=row["lat"],
        lon=row["lon"],
    )

# Add edges between houses and train stations based on proximity
for _, house in houses.iterrows():
    house_coords = (house["lat"], house["lon"])
    for _, station in stations.iterrows():
        station_coords = (station["lat"], station["lon"])
        distance = geodesic(house_coords, station_coords).km
        if distance < 5:  # Connect if within 5 km
            G.add_edge(house["property_id"], station["poi_id"], weight= 1/distance)



print(G.edges()) #G.edges


geo_h = gpd.GeoDataFrame(houses, geometry=gpd.points_from_xy(houses.lon, houses.lat))
geo_s = gpd.GeoDataFrame(stations, geometry=gpd.points_from_xy(stations.lon, stations.lat))
geo_r = gpd.GeoDataFrame(regions, geometry=gpd.points_from_xy(regions.lon, regions.lat))

#Map houses
# add basemap

fig, ax = plt.subplots(figsize=(10, 10))
geo_h.plot(ax=ax, color="red", markersize=10)
geo_s.plot(ax=ax, color="blue", markersize=10)
geo_r.plot(ax=ax, color="green", markersize=10)
plt.show()

#See attributes of houses
att = nx.get_node_attributes(G, name = 'lat')

