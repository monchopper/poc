import geopandas as gpd
import pandas as pd
from pathlib import Path
import json
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import Geocoder
from folium.plugins import Fullscreen
import plotly.express as px
import janitor


def load_data_csv(csv_file):
    data_csv = pd.read_csv(csv_file)
    return data_csv


apairy_sites_csv = Path(__file__).parents[0] / 'apiary_sites.csv'
optimal_mgo = Path(__file__).parents[0] / 'optimal_mgo_batch.csv'
market_price_mgo = Path(__file__).parents[0] / 'market_price_mgo.csv'
honey_extraction = Path(__file__).parents[0] / 'extraction_2022.csv'

df_apairy_sites = load_data_csv(apairy_sites_csv)
df_optimal_mgo = load_data_csv(optimal_mgo)
df_market_price_mgo = load_data_csv(market_price_mgo)
df_honey_extraction = load_data_csv(honey_extraction)

df_market_price_mgo.lower_boundary = df_market_price_mgo.lower_boundary.astype(float)
df_market_price_mgo.upper_boundary = df_market_price_mgo.upper_boundary.astype(float)

df_batch = df_optimal_mgo.conditional_join(df_market_price_mgo, ('optimal_mgo', 'lower_boundary', '>='),
                                           ('optimal_mgo', 'upper_boundary', '<='))

df_extracts_price = df_batch.merge(df_honey_extraction, left_on='batch_id', right_on='batch_id')

df_display = df_extracts_price.merge(df_apairy_sites, how='inner', left_on='site', right_on='site_name')

# st.write(df_display)


farm_blocks = Path(__file__).parents[0] / 'atihau_farm_blocks.geojson'


def load_data_geo(geojson_file):
    data_geo = gpd.read_file(geojson_file)
    return data_geo


overlay_farm_blocks = load_data_geo(farm_blocks)

df_display = df_display.dropna(subset=['lon', 'lat'])
df_display["revenue"] = (df_display["market_price"] * df_display["total"])

gdf_sites = gpd.GeoDataFrame(df_display, geometry=gpd.points_from_xy(df_display.lon, df_display.lat))

# Spatial Join to bring in area name from our zones geojson file
spatjoined = gpd.sjoin(gdf_sites, overlay_farm_blocks, how="inner", op="within")

df_aggs = spatjoined.groupby('name').agg(total_revenue=('revenue', 'sum'))
df_farm_block_display = overlay_farm_blocks.merge(df_aggs, on='name', how='left')
gdf2 = gpd.GeoDataFrame(df_farm_block_display)

#st.write(gdf2)

m = folium.Map(location=[-39.552096250878634, 175.29244153902494], zoom_start=9)

for indice, row in df_display.iterrows():
    html = f'''
                    <h2><b>{row['land_owner']} {row['site']}</b></h2>
                    <br>Details: {row['contract_name']} - {row['trading_name']}</br>
                    <p>2022 Revenue: ${row['market_price'] * row['total']}<p/>
                    
                    '''
    if row['site_type'] == 'HONEY':
        folium.Marker(
            location=[row['lat'], row['lon']], tooltip=row['site_name'] + '-' + row['site_type'],
            popup=folium.Popup(folium.IFrame(html=html, width=500, height=500), min_width=300, max_width=800),
            icon=folium.map.Icon(color='green')
        ).add_to(m)
    else:
        folium.Marker(
            location=[row['lat'], row['lon']], tooltip=row['site_name'] + '-' + row['site_type'],
            popup=folium.Popup(folium.IFrame(html=html, width=500, height=500), min_width=300, max_width=800),
            icon=folium.map.Icon(color='blue')
        ).add_to(m)

for _, lq in gdf2.iterrows():
    area_html = f'''
                    <h2><b>Farm Name: {lq['name']} </b></h2>
                    '''
    sim_geo = gpd.GeoSeries(lq['geometry'])
    geo_j = sim_geo.to_json()

    if lq['name'] == "Te Paenga":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#fc4e03', 'fillOpacity': 0.5, 'color': 'black',
                                                         'opacity': 0.5})
    elif lq['name'] == "Tohunga":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#fca103', 'fillOpacity': 0.5, 'color': 'black',
                                                         'opacity': 0.5})
    elif lq['name'] == "Hapuawhenua":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#fcfc03', 'fillOpacity': 0.5, 'color': 'black',
                                                         'opacity': 0.5})

    elif lq['name'] == "Te Pa":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#a5fc03', 'fillOpacity': 0.5, 'color': 'black',
                                                         'opacity': 0.5})
    elif lq['name'] == "Tawanui":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#03fc4a', 'fillOpacity': 0.5, 'color': 'black',
                                                         'opacity': 0.5})
    elif lq['name'] == "Waipuna Station":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#03dbfc', 'fillOpacity': 0.5, 'color': 'black',
                                                         'opacity': 0.5})
    elif lq['name'] == "Papahaua":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#0324fc', 'fillOpacity': 0.74117,
                                                         'color': 'black',
                                                         'opacity': 0.5})
    elif lq['name'] == "Ohotu":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#9003fc', 'fillOpacity': 0.74117,
                                                         'color': 'black',
                                                         'opacity': 0.5})
    elif lq['name'] == "Ohotu":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#fc03eb', 'fillOpacity': 0.74117,
                                                         'color': 'black',
                                                         'opacity': 0.5})
    elif lq['name'] == "Ohorea":
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': '#fc0356', 'fillOpacity': 0.74117,
                                                         'color': 'black',
                                                         'opacity': 0.5})
    else:
        geo_j = folium.GeoJson(data=geo_j,
                               style_function=lambda x: {'fillColor': 'beige', 'fillOpacity': 0.8,
                                                         'color': 'orange', 'opacity': 0.5})

    st.write(area_html)

    folium.Popup(folium.IFrame(html=area_html
                              , width=300, height=300), min_width=300, max_width=300).add_to(geo_j)
    geo_j.add_to(m)


#folium.LayerControl().add_to(m)

st_data = st_folium(m, width=725)
