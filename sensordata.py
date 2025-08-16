from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
import asyncio

app = FastAPI()

# ========================
# === ATG MONITORING ====
# ========================

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
    initial_volume = round(random.uniform(0.9, 1.0) * capacity, 2)
    tank_states[tank["tank_id"]] = {
        "current_volume": initial_volume,
        "last_update": datetime.now(),
        "next_update_after": timedelta(minutes=random.randint(1, 5))
    }

# ATG background update task
async def update_atg_data():
    while True:
        now = datetime.now()
        for tank in TANKS:
            state = tank_states[tank["tank_id"]]
            time_since_update = now - state["last_update"]

            if time_since_update >= state["next_update_after"]:
                usage = random.uniform(0.5, 3.0)
                new_volume = max(0, state["current_volume"] - usage)

                # Refill if needed
                if new_volume <= 0.2 * tank["capacity"]:
                    new_volume = round(random.uniform(0.9, 1.0) * tank["capacity"], 2)

                tank_states[tank["tank_id"]].update({
                    "current_volume": new_volume,
                    "last_update": now,
                    "next_update_after": timedelta(minutes=random.randint(1, 5))
                })

                tank_logs.append({
                    "tank_id": tank["tank_id"],
                    "fuel_type": tank["fuel_type"],
                    "capacity_liters": tank["capacity"],
                    "current_volume": round(new_volume, 2),
                    "volume_percent": round((new_volume / tank["capacity"]) * 100, 2),
                    "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
                })

        await asyncio.sleep(5)  # every 5 seconds
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

    # Prepare cards for diesel and petrol tanks separately
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

# Background task to update dispenser data
async def update_dispenser_data():
    while True:
        now = datetime.now()
        new_rows = []

        for pump in PUMPS:
            state = pump_states[pump]

            # Randomly toggle status with 10% chance
            if random.random() < 0.1:
                state["status"] = "offline" if state["status"] == "online" else "online"

            # Only update volume if online
            if state["status"] == "online":
                volume_increase = random.uniform(1.0, 5.0)
                state["volume"] += volume_increase
                state["last_update"] = now

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

        dispenser_logs.extend(new_rows)
        await asyncio.sleep(5)


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

async def update_avi_vehicle_data():
    global total_transactions, total_delivered_volume, total_sale_value, serial_no_counter

    while True:
        now = datetime.now()
        fueling_events = random.randint(0, 3)

        for _ in range(fueling_events):
            vehicle = random.choice(VEHICLES)
            pump = random.choice(PUMPS)
            state = pump_states[pump]

            if state["status"] != "online":
                continue  # skip offline pumps

            volume = round(random.uniform(1.0, 10.0), 2)
            price = state["price"]
            amount = round(price * volume, 3)

            total_transactions += 1
            total_delivered_volume += volume
            total_sale_value += amount
            serial_no_counter += 1

            vehicle_logs.append({
                "S_No": serial_no_counter,
                "VRN": vehicle["vrn"],
                "RFID_Tag_No": vehicle["rfid"],
                "Dispenser_Id": state["dispenser_id"],
                "Nozzle_Id": random.choice(NOZZLES),
                "Price_OMR": price,
                "Volume_Liters": volume,
                "Total_Amount_OMR": amount,
                "Fuel_Type": state["fuel_type"],
                "Timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
            })

        await asyncio.sleep(5)


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
    asyncio.create_task(update_atg_data())
    asyncio.create_task(update_dispenser_data())
    asyncio.create_task(update_avi_vehicle_data())
