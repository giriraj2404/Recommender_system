import pandas as pd
import random
import os
import time
from datetime import datetime
from geopy.distance import distance
from geopy import Point
from faker import Faker



Faker.seed(0)

fake = Faker('en_IN')

all_offers = [
    "Free coffee and snacks",
    "Cafe order offer",
    "Snack and drink combo",
    "Car wash discount",
    "Oil change offer",
    "Full service discount",
    "Fuel bonus points",
    "Fuel and cafe combo",
    "Triple combo reward",
    "Birthday double points",
    "Cafe happy hour",
    "New tyre deal",
]

# Geofence center (Kerala coords used here, not Nagpur)
GEOFENCE_CENTER = (8.552327586824264, 76.88001143071841)

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
        purchase_amount = random.randint(50, 500)if availed_offer else 0
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

if __name__ == "__main__":
    csv_path = "users_data.csv"
    csv_updated = "data_updates.csv"

    while True:
        try:
            # Load existing data if available
            if os.path.exists(csv_path):
                try:
                    old_df = pd.read_csv(csv_path)
                    last_user_id = old_df["user_id"].max()
                    if pd.isna(last_user_id):
                        last_user_id = 0
                except Exception as e:
                    print(f"âš ï¸ Failed to read existing CSV: {e}")
                    old_df = pd.DataFrame()
                    last_user_id = 0
            else:
                old_df = pd.DataFrame()
                last_user_id = 0    

            # Generate new data
            new_df = generate_data(start_user_id=last_user_id + 1)

            # Always overwrite csv_updated with the latest batch
            new_df.to_csv(csv_updated, index=False)

            # Append and save to master CSV
            combined_df = pd.concat([old_df, new_df], ignore_index=True)
            combined_df.to_csv(csv_path, index=False)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] âœ… Appended {len(new_df)} new users. Total now: {len(combined_df)}")

        except Exception as e:
            print(f"Error occurred: {e}")

        # Wait before next update
        time.sleep(60)
