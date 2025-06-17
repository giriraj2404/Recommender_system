import streamlit as st
import pandas as pd
import folium
from geopy.distance import geodesic, distance
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
from faker import Faker
from geopy import Point
import threading
import random
import os
import time
from datetime import datetime
import plotly.express as px
from streamlit_option_menu import option_menu




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


    st_autorefresh(interval=5* 1000, key="auto_refresh")  # Auto-refresh every 10s

    GEOFENCE_CENTER = (8.552327586824264, 76.88001143071841)
    GEOFENCE_RADIUS = 500  # in meters
    csv_path = "users_data.csv"
    csv_updated = "data_updates.csv"

    Faker.seed(0)
    fake = Faker('en_IN')

    all_offers = [
        "Free coffee and snacks", "Cafe order offer", "Snack and drink combo",
        "Car wash discount", "Oil change offer", "Full service discount",
        "Fuel bonus points", "Fuel and cafe combo", "Triple combo reward",
        "Birthday double points", "Cafe happy hour", "New tyre deal"
    ]

    # ------------------------------
    # Data Generation Thread
    # ------------------------------
    def generate_random_coordinate(center, radius_m=500):
        bearing = random.uniform(0, 360)
        d = distance(meters=random.uniform(0, radius_m))
        new_point = d.destination(point=Point(center), bearing=bearing)
        return new_point.latitude, new_point.longitude

    def generate_data(start_user_id, num_new_users=None):
        if num_new_users is None:
            num_new_users = random.randint(5, 10)
        data = []
        for i in range(num_new_users):
            lat, lon = generate_random_coordinate(GEOFENCE_CENTER)
            in_gas_station = random.choice([True, False])
            availed_offer = random.choice([True, False])
            purchase_amount = random.randint(50, 500) if availed_offer else 0
            names = f'{fake.first_name()} {fake.last_name()}'
            phone_no = fake.phone_number()
            membership = random.choice(["Member", "Non_member"])
            loyalty_point = random.randint(0, 500)
            offer = random.choice(all_offers) if availed_offer else 'None'

            data.append({
                "user_id": start_user_id + i,
                "Name": names,
                "Phone_Number": phone_no,
                "latitude": lat,
                "longitude": lon,
                "in_gas_station": in_gas_station,
                "availed_offer": availed_offer,
                "purchase_amount": purchase_amount,
                "Membership": membership,
                "loyalty_points": loyalty_point,
                "Offers": offer,
            })
        return pd.DataFrame(data)

    def data_updater():
        while True:
            try:
                if os.path.exists(csv_path):
                    try:
                        old_df = pd.read_csv(csv_path)
                        last_user_id = old_df["user_id"].max()
                        if pd.isna(last_user_id):
                            last_user_id = 0
                    except Exception:
                        old_df = pd.DataFrame()
                        last_user_id = 0
                else:
                    old_df = pd.DataFrame()
                    last_user_id = 0

                new_df = generate_data(start_user_id=last_user_id + 1)
                new_df.to_csv(csv_updated, index=False)

                combined_df = pd.concat([old_df, new_df], ignore_index=True)
                combined_df.to_csv(csv_path, index=False)

                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Generated {len(new_df)} users.")
            except Exception as e:
                print(f"❌ Error in data generation: {e}")
            time.sleep(30)  # wait 60s before next update

    # Run data generator in background thread
    if "data_thread_started" not in st.session_state:
        threading.Thread(target=data_updater, daemon=True).start()
        st.session_state.data_thread_started = True

    # ------------------------------
    # Streamlit UI
    # ------------------------------
    st.title("📊 Servi-AI Client Dashboard")

    # Load CSVs
    try:
        df = pd.read_csv(csv_path)
        new_df = pd.read_csv(csv_updated)
    except FileNotFoundError:
        st.error("CSV files not found. Make sure users_data.csv exists.")
        st.stop()

    # Clean missing values
    new_df = new_df.dropna(subset=["latitude", "longitude"])

    # Compute distances
    new_df["distance"] = new_df.apply(
        lambda row: geodesic((row["latitude"], row["longitude"]), GEOFENCE_CENTER).meters, axis=1
    )

    # KPIs
    members_in_geofence = len(new_df[new_df["distance"] <= GEOFENCE_RADIUS])
    members_in_gas_station = len(new_df[new_df["in_gas_station"] == True])
    penetration = f"{(df['availed_offer'].sum() / len(df) * 100):.1f}%" if len(df) else "0%"
    sales = f"${df['purchase_amount'].sum()}"
    total_penetration = len(df[df['availed_offer'] == True])

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("🧭 Members in Geofence", members_in_geofence)
    col2.metric("⛽ Members redeemed offers", members_in_gas_station)
    col3.metric("🎯 Offer Penetration", penetration)
    col4.metric("💰 Sales Generated", sales)
    col5.metric("📈 Total Day Penetration", total_penetration)

    # Map
    map_ = folium.Map(location=GEOFENCE_CENTER, zoom_start=16)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(map_)

    folium.Circle(
        location=GEOFENCE_CENTER,
        radius=GEOFENCE_RADIUS,
        color="blue",
        fill=True,
        fill_opacity=0.1,
        popup="Geofence Zone"
    ).add_to(map_)

    for _, row in new_df.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"User {int(row['user_id'])}",
            icon=folium.Icon(color="green" if row["in_gas_station"] else "red")
        ).add_to(map_)

    # Filtered table
    filtered_df = df[df['availed_offer'] == True]
    my_df = filtered_df[["user_id", "Name", "purchase_amount", "Membership", "loyalty_points", "Offers", "Phone_Number"]]

    col11, col12, col13 = st.columns(3)
    with col11:
        st.markdown("### Users Inside Geo-Fence")
        st_folium(map_, width=600, height=400)

    with col12:
        st.markdown("### Member/Non Member Redeemed Offers")
        purchase_by_membership = df.groupby('Membership')['purchase_amount'].sum().reset_index()
        fig = px.pie(purchase_by_membership, names='Membership', values='purchase_amount', title='Total Purchase Amount by Membership')
        st.plotly_chart(fig)

    with col13:
        st.markdown("### Membership Details")
        st.dataframe(my_df, hide_index=True)
