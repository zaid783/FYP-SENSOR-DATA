from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ✅ IMPORT YAHI KARO
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
import asyncio

app = FastAPI()

# ✅ ADD CORS MIDDLEWARE HERE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ You can also specify frontend URL here for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
# TANKS = [
#     {"tank_id": "Tank 1", "fuel_type": "Diesel", "capacity": 5000},
#     {"tank_id": "Tank 2", "fuel_type": "Diesel", "capacity": 8000},
#     {"tank_id": "Tank 3", "fuel_type": "Petrol", "capacity": 3000},
#     {"tank_id": "Tank 4", "fuel_type": "Petrol", "capacity": 10000},
# ]

# tank_states = {}
# tank_logs = []

# # Init
# for tank in TANKS:
#     capacity = tank["capacity"]
#     initial_volume = round(random.uniform(0.9, 1.0) * capacity, 2)
#     tank_states[tank["tank_id"]] = {
#         "current_volume": initial_volume,
#         "last_update": datetime.now(),
#         "next_update_after": timedelta(minutes=random.randint(1, 5))
#     }

# # ATG background update task
# async def update_atg_data():
#     while True:
#         now = datetime.now()
#         for tank in TANKS:
#             state = tank_states[tank["tank_id"]]
#             time_since_update = now - state["last_update"]

#             # Only update if next_update_after passed AND tank volume NOT recently updated externally
#             if time_since_update >= state["next_update_after"]:
#                 # Simulate small volume decrease (usage or evaporation)
#                 usage = random.uniform(0.5, 3.0)
#                 new_volume = max(0, state["current_volume"] - usage)

#                 # Refill if low
#                 if new_volume <= 0.2 * tank["capacity"]:
#                     new_volume = round(random.uniform(0.9, 1.0) * tank["capacity"], 2)

#                 tank_states[tank["tank_id"]].update({
#                     "current_volume": new_volume,
#                     "last_update": now,
#                     "next_update_after": timedelta(minutes=random.randint(1, 5))
#                 })

#                 tank_logs.append({
#                     "tank_id": tank["tank_id"],
#                     "fuel_type": tank["fuel_type"],
#                     "capacity_liters": tank["capacity"],
#                     "current_volume": round(new_volume, 2),
#                     "volume_percent": round((new_volume / tank["capacity"]) * 100, 2),
#                     "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
#                 })

#         await asyncio.sleep(30)  # every 5 seconds


# @app.get("/api/atg")
# async def get_atg_data():
#     now = datetime.now()
#     data = []

#     for tank in TANKS:
#         current_volume = tank_states[tank["tank_id"]]["current_volume"]
#         volume_percent = round((current_volume / tank["capacity"]) * 100, 2)

#         data.append({
#             "tank_id": tank["tank_id"],
#             "fuel_type": tank["fuel_type"],
#             "capacity_liters": tank["capacity"],
#             "current_volume": round(current_volume, 2),
#             "volume_percent": volume_percent,
#             "last_update": tank_states[tank["tank_id"]]["last_update"].strftime("%Y-%m-%d %I:%M %p")
#         })

#     # Prepare cards for diesel and petrol tanks separately
#     diesel_cards = []
#     petrol_cards = []

#     for tank in TANKS:
#         state = tank_states[tank["tank_id"]]
#         percent = round((state["current_volume"] / tank["capacity"]) * 100, 2)
#         card = {
#             "tank_id": tank["tank_id"],
#             "fuel_type": tank["fuel_type"],
#             "volume_percent": percent
#         }
#         if tank["fuel_type"].lower() == "diesel":
#             diesel_cards.append(card)
#         else:
#             petrol_cards.append(card)

#     return JSONResponse(content={
#         "cards": {
#             "diesel": diesel_cards,
#             "petrol": petrol_cards
#         },
#         "data_table": data,
#         "logs": tank_logs[-100:]
#     })
"""
# ========================
# === ATG MONITORING ====
# ========================

import random
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import asyncio
from db import db


app = FastAPI()

TANKS = [
    {"tank_id": "Tank 1", "fuel_type": "Diesel", "capacity": 5000},
    {"tank_id": "Tank 2", "fuel_type": "Diesel", "capacity": 8000},
    {"tank_id": "Tank 3", "fuel_type": "Petrol", "capacity": 3000},
    {"tank_id": "Tank 4", "fuel_type": "Petrol", "capacity": 10000},
]

tank_states = {}
tank_logs = []

# Init
for tank in TANKS:
    capacity = tank["capacity"]

    if tank["tank_id"] == "Tank 2":
        # Start between 50% to 79%
        initial_volume = round(random.uniform(0.50, 0.79) * capacity, 2)
    elif tank["tank_id"] == "Tank 4":
        # Start from 21% to 30%
        initial_volume = round(random.uniform(0.21, 0.30) * capacity, 2)
    else:
        # Default: start from 90% to 100%
        initial_volume = round(random.uniform(0.9, 1.0) * capacity, 2)

    tank_states[tank["tank_id"]] = {
        "current_volume": initial_volume,
        "last_update": datetime.now(),
        "next_update_after": timedelta(minutes=random.randint(1, 5))
    }


async def update_single_tank(tank):
    tank_id = tank["tank_id"]
    capacity = tank["capacity"]
    fuel_type = tank["fuel_type"]

    while True:
        state = tank_states[tank_id]
        await asyncio.sleep(state["next_update_after"].total_seconds())

        usage = random.uniform(0.5, 3.0)
        simulated_volume = max(0, state["current_volume"] - usage)

        # Refill if too low
        if simulated_volume <= 0.10 * capacity:
            simulated_volume = round(random.uniform(0.9, 1.0) * capacity, 2)

        now = datetime.now()

        # ✅ Create log BEFORE updating the in-memory state
        log = {
            "tank_id": tank_id,
            "fuel_type": fuel_type,
            "capacity_liters": capacity,
            "current_volume": round(simulated_volume, 2),
            "volume_percent": round((simulated_volume / capacity) * 100, 2),
            "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
        }

        tank_logs.append(log)

        # ✅ Write to DB before updating tank state
        await db.execute(
            """
            INSERT INTO atg_logs 
            (tank_id, fuel_type, capacity_liters, current_volume, volume_percent, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                log["tank_id"],
                log["fuel_type"],
                log["capacity_liters"],
                log["current_volume"],
                log["volume_percent"],
                now.strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        # ✅ Update tank state AFTER logging
        tank_states[tank_id].update({
            "current_volume": simulated_volume,
            "last_update": now,
            "next_update_after": timedelta(minutes=random.randint(1, 5))
        })


@app.get("/api/atg")
async def get_atg_data():
    now = datetime.now()
    data = []

    for tank in TANKS:
        current_volume = tank_states[tank["tank_id"]]["current_volume"]
        volume_percent = round((current_volume / tank["capacity"]) * 100, 2)

        data.append({
            "tank_id": tank["tank_id"],
            "fuel_type": tank["fuel_type"],
            "capacity_liters": tank["capacity"],
            "current_volume": round(current_volume, 2),
            "volume_percent": volume_percent,
            "last_update": tank_states[tank["tank_id"]]["last_update"].strftime("%Y-%m-%d %I:%M %p")
        })

    # Split cards
    diesel_cards = []
    petrol_cards = []

    for tank in TANKS:
        state = tank_states[tank["tank_id"]]
        percent = round((state["current_volume"] / tank["capacity"]) * 100, 2)
        card = {
            "tank_id": tank["tank_id"],
            "fuel_type": tank["fuel_type"],
            "volume_percent": percent
        }
        if tank["fuel_type"].lower() == "diesel":
            diesel_cards.append(card)
        else:
            petrol_cards.append(card)

    return JSONResponse(content={
        "cards": {
            "diesel": diesel_cards,
            "petrol": petrol_cards
        },
        "data_table": data,
        "logs": tank_logs[-100:]
    })



# ===============================
# === DISPENSER MONITORING ====
# ===============================

# Fixed prices per fuel type
FUEL_TYPES = {
    "Diesel": 0.240,
    "Petrol": 0.280
}

PUMPS = [f"Pump-{i}" for i in range(1, 11)]
DISPENSERS = [f"Dispenser-{i}" for i in range(1, 6)]

# Assign each dispenser a fixed fuel type (and thus fixed price)
dispenser_fuel_types = {}
for dispenser in DISPENSERS:
    fuel_type = random.choice(list(FUEL_TYPES.keys()))
    dispenser_fuel_types[dispenser] = fuel_type

# Initialize pump states; each pump assigned a dispenser_id and inherits that dispenser's fuel type and price
pump_states = {}
dispenser_logs = []

# Also track total volume dispensed per fuel type for syncing with ATG tanks later
dispenser_total_volume_by_fuel = {
    "Diesel": 0.0,
    "Petrol": 0.0
}

for pump in PUMPS:
    dispenser_id = random.choice(DISPENSERS)
    fuel_type = dispenser_fuel_types[dispenser_id]
    price = FUEL_TYPES[fuel_type]

    pump_states[pump] = {
        "dispenser_id": dispenser_id,
        "fuel_type": fuel_type,
        "status": "online",
        "price": price,
        "volume": round(random.uniform(5.0, 20.0), 2),
        "last_update": datetime.now(),
    }

# # Background task to update dispenser data
# async def update_dispenser_data():
#     global dispenser_total_volume_by_fuel

#     while True:
#         now = datetime.now()
#         new_rows = []

#         for pump in PUMPS:
#             state = pump_states[pump]

#             # Randomly toggle status with 10% chance
#             if random.random() < 0.1:
#                 state["status"] = "offline" if state["status"] == "online" else "online"

#             # Only update volume if online
#             if state["status"] == "online":
#                 volume_increase = random.uniform(1.0, 5.0)
#                 state["volume"] += volume_increase
#                 state["last_update"] = now

#                 # Add volume dispensed by this pump to total by fuel type
#                 dispenser_total_volume_by_fuel[state["fuel_type"]] += volume_increase

#             total_amount = round(state["price"] * state["volume"], 3)

#             log_entry = {
#                 "pump": pump,
#                 "status": state["status"],
#                 "dispenser_id": state["dispenser_id"],
#                 "fuel_type": state["fuel_type"],
#                 "price_omr": state["price"],
#                 "volume_liters": round(state["volume"], 2),
#                 "total_amount_omr": total_amount,
#                 "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
#             }

#             new_rows.append(log_entry)

#         dispenser_logs.extend(new_rows)
#         for log in new_rows:
#             await db.execute(
#                 """
#                 INSERT INTO dispenser_logs 
#                 (pump, status, dispenser_id, fuel_type, price_omr, volume_liters, total_amount_omr, timestamp)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
#                 """,
#                 (
#                     log["pump"],
#                     log["status"],
#                     log["dispenser_id"],
#                     log["fuel_type"],
#                     log["price_omr"],
#                     log["volume_liters"],
#                     log["total_amount_omr"],
#                     now.strftime("%Y-%m-%d %H:%M:%S")
#                 )
#             )

#         await asyncio.sleep(30)


previous_pump_states = {}

# Modify your update loop:
# async def update_dispenser_data():
#     global dispenser_total_volume_by_fuel, previous_pump_states

#     while True:
#         now = datetime.now()
#         new_rows = []

#         for pump in PUMPS:
#             state = pump_states[pump]

#             # Randomly toggle status with 10% chance
#             if random.random() < 0.1:
#                 state["status"] = "offline" if state["status"] == "online" else "online"

#             # Only update volume if online
#             volume_increase = 0.0
#             if state["status"] == "online":
#                 volume_increase = random.uniform(1.0, 5.0)
#                 state["volume"] += volume_increase
#                 state["last_update"] = now

#                 dispenser_total_volume_by_fuel[state["fuel_type"]] += volume_increase

#             # Get previous state
#             prev = previous_pump_states.get(pump, {})
#             prev_status = prev.get("status")
#             prev_volume = prev.get("volume", 0.0)

#             # Compare with current
#             status_changed = (state["status"] != prev_status)
#             volume_changed = (abs(state["volume"] - prev_volume) > 0.01)

#             if status_changed or volume_changed:
#                 total_amount = round(state["price"] * state["volume"], 3)

#                 log_entry = {
#                     "pump": pump,
#                     "status": state["status"],
#                     "dispenser_id": state["dispenser_id"],
#                     "fuel_type": state["fuel_type"],
#                     "price_omr": state["price"],
#                     "volume_liters": round(state["volume"], 2),
#                     "total_amount_omr": total_amount,
#                     "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
#                 }

#                 new_rows.append(log_entry)

#                 # Save current as previous for next cycle
#                 previous_pump_states[pump] = {
#                     "status": state["status"],
#                     "volume": state["volume"]
#                 }

#         dispenser_logs.extend(new_rows)
#         for log in new_rows:
#             await db.execute(
#                 """
#                 INSERT INTO dispenser_logs 
#                 (pump, status, dispenser_id, fuel_type, price_omr, volume_liters, total_amount_omr, timestamp)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#                 """,
#                 (
#                     log["pump"],
#                     log["status"],
#                     log["dispenser_id"],
#                     log["fuel_type"],
#                     log["price_omr"],
#                     log["volume_liters"],
#                     log["total_amount_omr"],
#                     now.strftime("%Y-%m-%d %H:%M:%S")
#                 )
#             )

#         await asyncio.sleep(30)

async def update_dispenser_data():
    global dispenser_total_volume_by_fuel, previous_pump_states

    while True:
        now = datetime.now()
        new_rows = []

        for pump in PUMPS:
            state = pump_states[pump]

            # Randomly toggle status with 10% chance
            if random.random() < 0.1:
                state["status"] = "offline" if state["status"] == "online" else "online"

            # Get previous state
            prev = previous_pump_states.get(pump, {})
            prev_status = prev.get("status")
            prev_volume = prev.get("volume", 0.0)

            # Compare current vs previous
            status_changed = (state["status"] != prev_status)
            volume_changed = (abs(state["volume"] - prev_volume) > 0.01)

            if status_changed or volume_changed:
                total_amount = round(state["price"] * state["volume"], 3)

                log_entry = {
                    "pump": pump,
                    "status": state["status"],
                    "dispenser_id": state["dispenser_id"],
                    "fuel_type": state["fuel_type"],
                    "price_omr": state["price"],
                    "volume_liters": round(state["volume"], 2),
                    "total_amount_omr": total_amount,
                    "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
                }

                new_rows.append(log_entry)

                # Update previous state
                previous_pump_states[pump] = {
                    "status": state["status"],
                    "volume": state["volume"]
                }

        # Log changes to DB
        dispenser_logs.extend(new_rows)
        for log in new_rows:
            await db.execute(
                """
                INSERT INTO dispenser_logs 
                (pump, status, dispenser_id, fuel_type, price_omr, volume_liters, total_amount_omr, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log["pump"],
                    log["status"],
                    log["dispenser_id"],
                    log["fuel_type"],
                    log["price_omr"],
                    log["volume_liters"],
                    log["total_amount_omr"],
                    now.strftime("%Y-%m-%d %H:%M:%S")
                )
            )
        await asyncio.sleep(30)


@app.get("/api/dispenser")
async def get_dispenser_data():
    total_dispensed_volume = sum(state["volume"] for state in pump_states.values())
    total_sale_value = sum(round(state["price"] * state["volume"], 3) for state in pump_states.values())
    warning_volume = max(state["volume"] for state in pump_states.values())
    warning_sale = max(round(state["price"] * state["volume"], 3) for state in pump_states.values())

    cards = {
        "total_dispensed_volume_blue": round(total_dispensed_volume, 2),
        "total_sale_value_green": round(total_sale_value, 2),
        "total_dispensed_volume_yellow": round(warning_volume, 2),
        "total_sale_value_red": round(warning_sale, 2),
    }

    return JSONResponse(content={"cards": cards, "data_table": dispenser_logs[-100:]})




# # ===============================
# # === AVI VEHICLE MONITORING ====
# # ===============================

# VEHICLES = [
#     {"vrn": "1415-HK", "rfid": "5954691162383060001"},
#     {"vrn": "1823-LM", "rfid": "5954691162383060002"},
#     {"vrn": "2207-RT", "rfid": "5954691162383060003"},
#     {"vrn": "3145-ZX", "rfid": "5954691162383060004"},
#     {"vrn": "4876-NB", "rfid": "5954691162383060005"},
#     {"vrn": "5234-OP", "rfid": "5954691162383060006"},
#     {"vrn": "6157-QW", "rfid": "5954691162383060007"},
#     {"vrn": "7012-ER", "rfid": "5954691162383060008"},
#     {"vrn": "8349-TY", "rfid": "5954691162383060009"},
#     {"vrn": "9220-UI", "rfid": "5954691162383060010"},
# ]

# total_vehicles = len(VEHICLES)
# total_transactions = 0
# total_delivered_volume = 0.0
# total_sale_value = 0.0
# vehicle_logs = []
# serial_no_counter = 0
# NOZZLES = [1, 2]

# # Reference to dispenser_total_volume_by_fuel from dispenser monitoring
# # We'll deduct these volumes from ATG tanks accordingly
# from typing import List

# # Helper: get tanks by fuel type (Diesel tanks: Tank 1 & 2; Petrol tanks: Tank 3 & 4)
# def get_tanks_by_fuel(fuel_type: str) -> List[dict]:
#     return [tank for tank in TANKS if tank["fuel_type"] == fuel_type]

# vehicle_index = 0  # outside the async function, global

# # async def update_avi_vehicle_data():
# #     global total_transactions, total_delivered_volume, total_sale_value, serial_no_counter, vehicle_index

# #     while True:
# #         now = datetime.now()
# #         fueling_events = random.randint(1, 5)

# #         for _ in range(fueling_events):
# #             vehicle = VEHICLES[vehicle_index % total_vehicles]
# #             vehicle_index += 1
# #             pump = random.choice(PUMPS)
# #             state = pump_states[pump]

# #             if state["status"] != "online":
# #                 continue  # skip offline pumps

# #             volume = round(random.uniform(1.0, 10.0), 2)
# #             price = state["price"]
# #             amount = round(price * volume, 3)

# #             # Update total counters
# #             total_transactions += 1
# #             total_delivered_volume += volume
# #             total_sale_value += amount
# #             serial_no_counter += 1

# #             # Update dispenser pump volume (simulate fuel dispensed)
# #             state["volume"] += volume
# #             state["last_update"] = now

# #             # Also increment dispenser total volume by fuel for ATG sync
# #             dispenser_total_volume_by_fuel[state["fuel_type"]] += volume

# #             # Deduct volume from relevant ATG tanks by fuel type
# #             tanks = get_tanks_by_fuel(state["fuel_type"])
# #             volume_to_deduct = volume

# #             for tank in tanks:
# #                 tank_state = tank_states[tank["tank_id"]]
# #                 current_vol = tank_state["current_volume"]

# #                 if current_vol >= volume_to_deduct:
# #                     new_volume = current_vol - volume_to_deduct
# #                     tank_state["current_volume"] = new_volume
# #                     volume_to_deduct = 0
# #                 else:
# #                     volume_to_deduct -= current_vol
# #                     tank_state["current_volume"] = 0

# #                 # Update tank metadata
# #                 tank_state["last_update"] = now
# #                 tank_state["next_update_after"] = timedelta(minutes=random.randint(1, 5))

# #                 if volume_to_deduct <= 0:
# #                     break

# #             log = {
# #                 "S_No": serial_no_counter,
# #                 "VRN": vehicle["vrn"],
# #                 "RFID_Tag_No": vehicle["rfid"],
# #                 "Dispenser_Id": state["dispenser_id"],
# #                 "Nozzle_Id": random.choice(NOZZLES),
# #                 "Price_OMR": price,
# #                 "Volume_Liters": volume,
# #                 "Total_Amount_OMR": amount,
# #                 "Fuel_Type": state["fuel_type"],
# #                 "Timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
# #             }

# #             vehicle_logs.append(log)

# #             # Log to MySQL database
# #             await db.execute(
# #                 """
# #                 INSERT INTO avi_vehicle_logs 
# #                 (s_no, vrn, rfid_tag_no, dispenser_id, nozzle_id, price_omr, volume_liters, total_amount_omr, fuel_type, timestamp)
# #                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
# #                 """,
# #                 (
# #                     log["S_No"],
# #                     log["VRN"],
# #                     log["RFID_Tag_No"],
# #                     log["Dispenser_Id"],
# #                     log["Nozzle_Id"],
# #                     log["Price_OMR"],
# #                     log["Volume_Liters"],
# #                     log["Total_Amount_OMR"],
# #                     log["Fuel_Type"],
# #                     now.strftime("%Y-%m-%d %H:%M:%S")
# #                 )
# #             )

# #         await asyncio.sleep(30)

# async def update_avi_vehicle_data():
#     global total_transactions, total_delivered_volume, total_sale_value, serial_no_counter, vehicle_index

#     while True:
#         now = datetime.now()
#         fueling_events = random.randint(1, 5)

#         for _ in range(fueling_events):
#             vehicle = VEHICLES[vehicle_index % total_vehicles]
#             vehicle_index += 1

#             # Get pumps that are online
#             valid_pumps = [p for p in PUMPS if pump_states[p]["status"] == "online"]
#             if not valid_pumps:
#                 continue  # Skip if no online pump is available

#             pump = random.choice(valid_pumps)
#             state = pump_states[pump]

#             # Simulate fuel volume
#             volume = round(random.uniform(1.0, 10.0), 2)
#             price = state["price"]
#             amount = round(price * volume, 3)

#             # Update stats
#             total_transactions += 1
#             total_delivered_volume += volume
#             total_sale_value += amount
#             serial_no_counter += 1

#             # Update dispenser volume (only when vehicle fuels)
#             state["volume"] += volume
#             state["last_update"] = now

#             # Update total volume for syncing with ATG
#             dispenser_total_volume_by_fuel[state["fuel_type"]] += volume

#             # Deduct from ATG tanks
#             tanks = get_tanks_by_fuel(state["fuel_type"])
#             volume_to_deduct = volume

#             for tank in tanks:
#                 tank_state = tank_states[tank["tank_id"]]
#                 current_vol = tank_state["current_volume"]

#                 if current_vol >= volume_to_deduct:
#                     tank_state["current_volume"] = current_vol - volume_to_deduct
#                     volume_to_deduct = 0
#                 else:
#                     volume_to_deduct -= current_vol
#                     tank_state["current_volume"] = 0

#                 tank_state["last_update"] = now
#                 tank_state["next_update_after"] = timedelta(minutes=random.randint(1, 5))

#                 if volume_to_deduct <= 0:
#                     break

#             log = {
#                 "S_No": serial_no_counter,
#                 "VRN": vehicle["vrn"],
#                 "RFID_Tag_No": vehicle["rfid"],
#                 "Dispenser_Id": state["dispenser_id"],
#                 "Nozzle_Id": random.choice(NOZZLES),
#                 "Price_OMR": price,
#                 "Volume_Liters": volume,
#                 "Total_Amount_OMR": amount,
#                 "Fuel_Type": state["fuel_type"],
#                 "Timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
#             }

#             vehicle_logs.append(log)

#             # Log to MySQL
#             await db.execute(
#                 """
#                 INSERT INTO avi_vehicle_logs 
#                 (s_no, vrn, rfid_tag_no, dispenser_id, nozzle_id, price_omr, volume_liters, total_amount_omr, fuel_type, timestamp)
#                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#                 """,
#                 (
#                     log["S_No"],
#                     log["VRN"],
#                     log["RFID_Tag_No"],
#                     log["Dispenser_Id"],
#                     log["Nozzle_Id"],
#                     log["Price_OMR"],
#                     log["Volume_Liters"],
#                     log["Total_Amount_OMR"],
#                     log["Fuel_Type"],
#                     now.strftime("%Y-%m-%d %H:%M:%S")
#                 )
#             )

#         await asyncio.sleep(30)


# @app.get("/api/avi_vehicle")
# async def get_avi_vehicle_data():
#     cards = {
#         "total_vehicles": total_vehicles,
#         "total_transactions": total_transactions,
#         "total_delivered_volume_liters": round(total_delivered_volume, 2),
#         "total_sale_value_omr": round(total_sale_value, 3),
#     }
#     return JSONResponse(content={
#         "cards": cards,
#         "data_table": vehicle_logs[-100:]
#     })


# ===============================
# === AVI VEHICLE MONITORING ====
# ===============================

VEHICLES = [
    {"vrn": "1415-HK", "rfid": "5954691162383060001"},
    {"vrn": "1823-LM", "rfid": "5954691162383060002"},
    {"vrn": "2207-RT", "rfid": "5954691162383060003"},
    {"vrn": "3145-ZX", "rfid": "5954691162383060004"},
    {"vrn": "4876-NB", "rfid": "5954691162383060005"},
    {"vrn": "5234-OP", "rfid": "5954691162383060006"},
    {"vrn": "6157-QW", "rfid": "5954691162383060007"},
    {"vrn": "7012-ER", "rfid": "5954691162383060008"},
    {"vrn": "8349-TY", "rfid": "5954691162383060009"},
    {"vrn": "9220-UI", "rfid": "5954691162383060010"},
]

total_vehicles = len(VEHICLES)
total_transactions = 0
total_delivered_volume = 0.0
total_sale_value = 0.0
vehicle_logs = []
serial_no_counter = 0
NOZZLES = [1, 2]

# Cooldown tracking
vehicle_last_fuel_time = {}  # Track last fueling time
vehicle_cooldown_seconds = 180  # 3 minutes cooldown

from typing import List


# Helper: get tanks by fuel type (Diesel tanks: Tank 1 & 2; Petrol tanks: Tank 3 & 4)
def get_tanks_by_fuel(fuel_type: str) -> List[dict]:
    return [tank for tank in TANKS if tank["fuel_type"] == fuel_type] 

vehicle_index = 0  # outside the async function, global

async def update_avi_vehicle_data():
    global total_transactions, total_delivered_volume, total_sale_value, serial_no_counter, vehicle_index

    while True:
        now = datetime.now()
        fueling_events = random.randint(1, 5)

        for _ in range(fueling_events):
            vehicle = VEHICLES[vehicle_index % total_vehicles]
            vehicle_index += 1
            rfid = vehicle["rfid"]

            # Cooldown check only if vehicle has already fueled before
            if rfid in vehicle_last_fuel_time:
                last_fueled = vehicle_last_fuel_time[rfid]
                if (now - last_fueled).total_seconds() < vehicle_cooldown_seconds:
                    continue  # Skip if within cooldown

            # Get pumps that are online
            valid_pumps = [p for p in PUMPS if pump_states[p]["status"] == "online"]
            if not valid_pumps:
                continue  # Skip if no online pump is available

            pump = random.choice(valid_pumps)
            state = pump_states[pump]

            # Simulate fuel volume
            volume = round(random.uniform(1.0, 10.0), 2)
            price = state["price"]
            amount = round(price * volume, 3)

            # Update stats
            total_transactions += 1
            total_delivered_volume += volume
            total_sale_value += amount
            serial_no_counter += 1

            # Update dispenser volume
            state["volume"] += volume
            state["last_update"] = now

            # Update total volume for syncing with ATG
            dispenser_total_volume_by_fuel[state["fuel_type"]] += volume

            # Deduct from ATG tanks
            tanks = get_tanks_by_fuel(state["fuel_type"])
            volume_to_deduct = volume

            for tank in tanks:
                tank_state = tank_states[tank["tank_id"]]
                current_vol = tank_state["current_volume"]

                if current_vol >= volume_to_deduct:
                    tank_state["current_volume"] = current_vol - volume_to_deduct
                    volume_to_deduct = 0
                else:
                    volume_to_deduct -= current_vol
                    tank_state["current_volume"] = 0

                tank_state["last_update"] = now
                tank_state["next_update_after"] = timedelta(minutes=random.randint(1, 5))

                if volume_to_deduct <= 0:
                    break

            log = {
                "S_No": serial_no_counter,
                "VRN": vehicle["vrn"],
                "RFID_Tag_No": rfid,
                "Dispenser_Id": state["dispenser_id"],
                "Nozzle_Id": random.choice(NOZZLES),
                "Price_OMR": price,
                "Volume_Liters": volume,
                "Total_Amount_OMR": amount,
                "Fuel_Type": state["fuel_type"],
                "Timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
            }

            vehicle_logs.append(log)

            # Record last fueling time
            vehicle_last_fuel_time[rfid] = now

            # # Mark this vehicle as having completed its first fuel
            # vehicle_first_fuel_done.add(rfid)

            # Log to MySQL
            await db.execute(
                """
                INSERT INTO avi_vehicle_logs 
                (s_no, vrn, rfid_tag_no, dispenser_id, nozzle_id, price_omr, volume_liters, total_amount_omr, fuel_type, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log["S_No"],
                    log["VRN"],
                    log["RFID_Tag_No"],
                    log["Dispenser_Id"],
                    log["Nozzle_Id"],
                    log["Price_OMR"],
                    log["Volume_Liters"],
                    log["Total_Amount_OMR"],
                    log["Fuel_Type"],
                    now.strftime("%Y-%m-%d %H:%M:%S")
                )
            )

        await asyncio.sleep(30)


@app.get("/api/avi_vehicle")
async def get_avi_vehicle_data():
    cards = {
        "total_vehicles": total_vehicles,
        "total_transactions": total_transactions,
        "total_delivered_volume_liters": round(total_delivered_volume, 2),
        "total_sale_value_omr": round(total_sale_value, 3),
    }
    return JSONResponse(content={
        "cards": cards,
        "data_table": vehicle_logs[-100:]
    })


# =======================
# === BACKGROUND TASK ===
# =======================

@app.on_event("startup")
async def startup_event():
    try:
        await db.connect()
        print("✅ Database connected.")

        # Launch a task per tank
        for tank in TANKS:
            asyncio.create_task(update_single_tank(tank))

        asyncio.create_task(update_dispenser_data())
        asyncio.create_task(update_avi_vehicle_data())

        print("🚀 All background tasks started.")
    except Exception as e:
        print("❌ Startup error:", e)

@app.on_event("shutdown")
async def shutdown_event():
    await db.disconnect()
    print("🔌 Database connection closed.")