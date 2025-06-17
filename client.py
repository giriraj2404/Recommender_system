import streamlit as st
import pandas as pd
import folium
from geopy.distance import geodesic
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
import plotly.express as px
from streamlit_option_menu import option_menu
import time

st.set_page_config(layout="wide", page_title="Servi-AI Dashboard")


with st.sidebar:
    selected = option_menu(
    menu_title=None,
    options=["Dashboard", "Tracker", "Profile"],
    icons=["house", "bar-chart", "person"],
    menu_icon="cast",
    default_index=0,
    orientation="vertical",

)

# Display page content based on selection
if selected == "Dashboard":

    # Auto-refresh every 10 seconds
    st_autorefresh(interval=10 * 1000, key="auto_refresh")


    # Geofence Config
    GEOFENCE_CENTER = (8.552327586824264, 76.88001143071841)  # Nagpur
    GEOFENCE_RADIUS = 500  # meters

    st.title("📊 Servi-AI Client Dashboard")

    # Load live data
    try:
        df = pd.read_csv("users_data.csv")
        new_df =pd.read_csv("data_updates.csv")
    except FileNotFoundError:
        st.error("CSV file not found. Please add 'users_data.csv' in the directory.")
        st.stop()

    # Clean missing values
    new_df= new_df.dropna(subset=["latitude", "longitude"])

    # Calculate distance from geofence center
    new_df["distance"] = new_df.apply(
        lambda row: geodesic((row["latitude"], row["longitude"]), GEOFENCE_CENTER).meters, axis=1
    )

    # KPIs
    members_in_geofence = len(new_df[new_df["distance"] <= GEOFENCE_RADIUS])
    members_in_gas_station = len(new_df[new_df["in_gas_station"] == True])
    penetration = f"{(df['availed_offer'].sum() / len(df) * 100):.1f}%" if len(df) else "0%"
    sales = f"${df['purchase_amount'].sum()}"
    total_penetration = len(df[df['availed_offer']==True])

    # KPI Display
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🧭 Members in Geofence", members_in_geofence)
    col2.metric("⛽ Members redeemed offers", members_in_gas_station)
    col3.metric("🎯 Offer Penetration", penetration)
    col4.metric("💰 Sales Generated", sales)
    col5.metric("### Total Day Penetration", total_penetration)
    # Folium map
    map_ = folium.Map(location=GEOFENCE_CENTER, zoom_start=16,)

    tile = folium.TileLayer(
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri Satellite',
        overlay = False,
        control = True
        ).add_to(map_)

    folium.Circle(
        location=GEOFENCE_CENTER,
        radius=GEOFENCE_RADIUS,
        color="blue",
        fill=True,
        fill_opacity=0.1,
        popup="Geofence Zone"
    ).add_to(map_)
    folium.Marker(
            location=[8.552229591225231, 76.87957964874424],  
            
            icon=folium.Icon(color="black",icon_size=(500, 700))
        ).add_to(map_)
    for _, row in new_df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"User {int(row['user_id'])}",
            icon=folium.Icon(color="green" if row["in_gas_station"] else "red")
        ).add_to(map_)

    filtered_df = df[df['availed_offer'] == True]

    # Select required columns
    my_df = filtered_df[["user_id", "Name", "purchase_amount", "Membership", "loyalty_points", "Offers", "Phone_Number"]]
    # my_df= my_df.reset_index(drop = True)
        # Display in Streamlit
    col11, col12, col13 = st.columns(3)
    with col11:
        # Render map in Streamlit
        st.markdown("### Users Inside Geo-Fence")
        st_folium(map_, width=600, height=400)

    with col12:
        st.markdown("### Member/Non Member Reedemed Offers")
        purchase_by_membership = df.groupby('Membership')['purchase_amount'].sum().reset_index()

    # Create Pie Chart
        fig = px.pie(purchase_by_membership,
                names='Membership',
                values='purchase_amount',
                title='Total Purchase Amount by Membership')
        st.plotly_chart(fig)
    with col13:
        st.markdown("### Membership Details")

        # Filter rows where availed_offer is True

        st.dataframe(my_df, hide_index = True)



    