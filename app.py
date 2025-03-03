
import streamlit as st
import folium
from streamlit_folium import folium_static
import numpy as np
from math import radians, sin, cos, sqrt, atan2

# Haversine distance function
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Streamlit app
def main():
    st.title("CleanNet Universal: 5G Node Optimization")
    st.write("Optimize 5G node placements for any region by entering the details below.")

    # Region boundaries
    st.header("Region Boundaries")
    col1, col2 = st.columns(2)
    with col1:
        lat_min = st.number_input("Min Latitude", value=-1.5167, step=0.0001, format="%.4f", key="lat_min")
        lon_min = st.number_input("Min Longitude", value=36.75, step=0.0001, format="%.4f", key="lon_min")
    with col2:
        lat_max = st.number_input("Max Latitude", value=-0.75, step=0.0001, format="%.4f", key="lat_max")
        lon_max = st.number_input("Max Longitude", value=37.75, step=0.0001, format="%.4f", key="lon_max")

    # Population data
    st.header("Population Centers")
    num_centers = st.slider("Number of Urban Centers", 1, 5, 2, key="num_centers")
    centers = []
    for i in range(num_centers):
        st.subheader(f"Urban Center {i+1}")
        name = st.text_input(f"Name {i+1}", f"City {i+1}", key=f"name_{i}")
        lat = st.number_input(f"Latitude {i+1}", min_value=lat_min, max_value=lat_max, value=lat_min + i*0.1, key=f"lat_{i}")
        lon = st.number_input(f"Longitude {i+1}", min_value=lon_min, max_value=lon_max, value=lon_min + i*0.1, key=f"lon_{i}")
        pop = st.number_input(f"Population {i+1}", min_value=0, value=100000, key=f"pop_{i}")
        centers.append({'name': name, 'lat': lat, 'lon': lon, 'pop': pop})

    rural_density = st.number_input("Rural Density (people/km²)", min_value=0, value=165, key="rural_density")

    # AQI data
    st.header("Air Quality Index (AQI)")
    aqi_base_lat = st.number_input("Baseline AQI Latitude", min_value=lat_min, max_value=lat_max, value=lat_min, key="aqi_lat")
    aqi_base_lon = st.number_input("Baseline AQI Longitude", min_value=lon_min, max_value=lon_max, value=lon_min, key="aqi_lon")
    aqi_base_value = st.number_input("Baseline AQI Value", min_value=0, value=65, key="aqi_value")
    D_max = max(
        haversine(lat_min, lon_min, lat_max, lon_max),
        haversine(lat_min, lon_max, lat_max, lon_min)
    )

    # Generate nodes
    if st.button("Optimize Nodes", key="optimize"):
        # Generate 100 random nodes
        np.random.seed(42)  # For reproducibility
        nodes = [{'lat': np.random.uniform(lat_min, lat_max), 'lon': np.random.uniform(lon_min, lon_max)} for _ in range(100)]

        # Calculate scores
        coverage_area = np.pi * 10**2  # 10 km radius
        results = []
        for i, node in enumerate(nodes):
            d_aqi_base = haversine(node['lat'], node['lon'], aqi_base_lat, aqi_base_lon)
            aqi = max(30, 65 - (d_aqi_base / D_max) * 35)  # Simplified AQI
            
            # Coverage
            coverage = rural_density * coverage_area
            for center in centers:
                if haversine(node['lat'], node['lon'], center['lat'], center['lon']) < 10:
                    coverage = center['pop']
                    break
            
            score = coverage - 0.5 * aqi
            results.append({'name': f"Node-{i+1:02d}", 'lat': node['lat'], 'lon': node['lon'], 'coverage': coverage, 'aqi': aqi, 'score': score})

        # Greedy optimization for 10 nodes
        selected_nodes = []
        remaining_nodes = results.copy()
        while len(selected_nodes) < 10 and remaining_nodes:
            remaining_nodes.sort(key=lambda x: x['score'], reverse=True)
            best_node = remaining_nodes.pop(0)
            selected_nodes.append(best_node)
            new_remaining = [
                node for node in remaining_nodes 
                if haversine(best_node['lat'], best_node['lon'], node['lat'], node['lon']) > 10
            ]
            remaining_nodes = new_remaining

        # Display results
        st.header("Optimized Nodes")
        st.write("| Name | Latitude | Longitude | Coverage | AQI | Score |")
        st.write("|------|----------|-----------|----------|-----|-------|")
        for node in selected_nodes:
            st.write(f"| {node['name']} | {node['lat']:.4f} | {node['lon']:.4f} | {node['coverage']:.1f} | {node['aqi']:.2f} | {node['score']:.2f} |")

        # Create and display map
        mymap = folium.Map(location=[(lat_min + lat_max) / 2, (lon_min + lon_max) / 2], zoom_start=10)
        for node in selected_nodes:
            folium.Marker([node['lat'], node['lon']], popup=f"{node['name']}<br>Score: {node['score']:.2f}", icon=folium.Icon(color='blue')).add_to(mymap)
            folium.Circle([node['lat'], node['lon']], radius=10000, color='blue', fill=True, fill_opacity=0.2).add_to(mymap)
        for center in centers:
            folium.Marker([center['lat'], center['lon']], popup=center['name'], icon=folium.Icon(color='red')).add_to(mymap)
        
        folium_static(mymap)

if __name__ == "__main__":
    main()
