from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # ✅ IMPORT YAHI KARO
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import random
import asyncio
from db import db


app = FastAPI()

# CORS MIDDLEWARE 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Initialize tank volumes
for tank in TANKS:
    capacity = tank["capacity"]

    if tank["tank_id"] == "Tank 2":
        initial_volume = round(random.uniform(0.50, 0.79) * capacity, 2)
    elif tank["tank_id"] == "Tank 4":
        initial_volume = round(random.uniform(0.21, 0.30) * capacity, 2)
    else:
        initial_volume = round(random.uniform(0.9, 1.0) * capacity, 2)

    tank_states[tank["tank_id"]] = {
        "current_volume": initial_volume,
        "last_update": datetime.now(),
        "next_update_after": timedelta(minutes=random.randint(1, 5))
    }

# ✅ New Helper Function: Deduct fuel volume from appropriate tank
def deduct_from_atg_tank(fuel_type: str, volume: float):
    relevant_tanks = []

    if fuel_type == "Diesel":
        relevant_tanks = ["Tank 1", "Tank 2"]
    elif fuel_type == "Petrol":
        relevant_tanks = ["Tank 3", "Tank 4"]

    random.shuffle(relevant_tanks)  # Pick one tank randomly

    for tank_id in relevant_tanks:
        tank = next((t for t in TANKS if t["tank_id"] == tank_id), None)
        if not tank:
            continue

        current_volume = tank_states[tank_id]["current_volume"]
        capacity = tank["capacity"]

        if current_volume >= volume:
            new_volume = round(current_volume - volume, 2)
        else:
            new_volume = 0.0

        tank_states[tank_id].update({
            "current_volume": new_volume,
            "last_update": datetime.now()
        })
        break  # Only deduct from one tank

# Background tank update loop (simulated usage and refill)
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

        log = {
            "tank_id": tank_id,
            "fuel_type": fuel_type,
            "capacity_liters": capacity,
            "current_volume": round(simulated_volume, 2),
            "volume_percent": round((simulated_volume / capacity) * 100, 2),
            "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
        }

        tank_logs.append(log)

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

        tank_states[tank_id].update({
            "current_volume": simulated_volume,
            "last_update": now,
            "next_update_after": timedelta(minutes=random.randint(1, 5))
        })

# API Endpoint
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


# NEW GLOBAL VALUES
pump_volume_blue = {pump: 0.0 for pump in PUMPS}
pump_volume_yellow = {pump: 0.0 for pump in PUMPS}

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


previous_pump_states = {}

async def update_dispenser_data():
    global dispenser_total_volume_by_fuel, previous_pump_states

    while True:
        now = datetime.now()
        new_rows = []

        for pump in PUMPS:
            state = pump_states[pump]

            # Randomly toggle status with 10% chance (optional, keep if you want)
            if random.random() < 0.1:
                state["status"] = "offline" if state["status"] == "online" else "online"

            # Calculate volumes from blue + yellow
            blue_vol = pump_volume_blue[pump]
            yellow_vol = pump_volume_yellow[pump]
            combined_vol = blue_vol + yellow_vol

            # Get previous state
            prev = previous_pump_states.get(pump, {})
            prev_status = prev.get("status")
            prev_volume = prev.get("volume", 0.0)

            status_changed = (state["status"] != prev_status)
            volume_changed = (abs(combined_vol - prev_volume) > 0.01)

            if status_changed or volume_changed:
                total_amount = round(state["price"] * combined_vol, 3)

                log_entry = {
                    "pump": pump,
                    "status": state["status"],
                    "dispenser_id": state["dispenser_id"],
                    "fuel_type": state["fuel_type"],
                    "price_omr": state["price"],
                    "volume_liters": round(combined_vol, 2),
                    "total_amount_omr": total_amount,
                    "timestamp": now.strftime("%Y-%m-%d %I:%M:%S %p")
                }

                new_rows.append(log_entry)

                # Update previous state
                previous_pump_states[pump] = {
                    "status": state["status"],
                    "volume": combined_vol
                }

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
    total_dispensed_volume_blue = sum(pump_volume_blue.values())
    total_dispensed_volume_yellow = sum(pump_volume_yellow.values())
    total_sale_value = sum(
        round(state["price"] * (pump_volume_blue[pump] + pump_volume_yellow[pump]), 3) 
        for pump, state in pump_states.items()
    )

    max_volume = max((pump_volume_blue[pump] + pump_volume_yellow[pump]) for pump in PUMPS)
    max_sale = max(
        round(state["price"] * (pump_volume_blue[pump] + pump_volume_yellow[pump]), 3) 
        for pump, state in pump_states.items()
    )

    cards = {
        "total_dispensed_volume_blue": round(total_dispensed_volume_blue, 2),
        "total_dispensed_volume_yellow": round(total_dispensed_volume_yellow, 2),
        "total_sale_value_green": round(total_sale_value, 3),
        "total_sale_value_red": round(max_sale, 3),
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

# Cooldown tracking
vehicle_last_fuel_time = {}  # Track last fueling time
vehicle_cooldown_seconds = 180  # 3 minutes cooldown

from typing import List

# Helper: get tanks by fuel type (Diesel tanks: Tank 1 & 2; Petrol tanks: Tank 3 & 4)
def get_tanks_by_fuel(fuel_type: str) -> List[dict]:
    return [tank for tank in TANKS if tank["fuel_type"] == fuel_type] 

vehicle_index = 0  # outside the async function, global

async def update_avi_vehicle_data():
    global total_transactions, total_delivered_volume, total_sale_value
    global serial_no_counter, vehicle_index
    global pump_volume_blue, pump_volume_yellow

    while True:
        now = datetime.now()
        fueling_events = random.randint(1, 5)

        for _ in range(fueling_events):
            vehicle = VEHICLES[vehicle_index % total_vehicles]
            vehicle_index += 1
            rfid = vehicle["rfid"]

            if rfid in vehicle_last_fuel_time:
                last_fueled = vehicle_last_fuel_time[rfid]
                if (now - last_fueled).total_seconds() < vehicle_cooldown_seconds:
                    continue

            valid_pumps = [p for p in PUMPS if pump_states[p]["status"] == "online"]
            if not valid_pumps:
                continue

            pump = random.choice(valid_pumps)
            state = pump_states[pump]

            # Simulate total fuel volume
            volume = round(random.uniform(1.0, 10.0), 2)

            # Split into blue and yellow volumes
            blue_volume = round(volume * random.uniform(0.4, 0.6), 2)
            yellow_volume = round(volume - blue_volume, 2)

            # Update per-pump blue and yellow totals
            pump_volume_blue[pump] += blue_volume
            pump_volume_yellow[pump] += yellow_volume

            # Combined volume in pump_states (for compatibility)
            state["volume"] = pump_volume_blue[pump] + pump_volume_yellow[pump]
            state["last_update"] = now

            # Update overall metrics
            price = state["price"]
            amount = round(price * volume, 3)

            total_transactions += 1
            total_delivered_volume += volume
            total_sale_value += amount
            serial_no_counter += 1

            # Update total volume per fuel type for ATG
            dispenser_total_volume_by_fuel[state["fuel_type"]] += volume

            # ✅ Deduct from ATG tanks using helper
            deduct_from_atg_tank(state["fuel_type"], volume)

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
            vehicle_last_fuel_time[rfid] = now

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

from fastapi.responses import JSONResponse
from collections import defaultdict

@app.get("/api/dashboard")
async def get_dashboard_summary():
    TOTAL_ATGS = 4
    TOTAL_AVI_VEHICLES = len(VEHICLES)
    TOTAL_BOWSERS = 5  
    TOTAL_RTGS = TOTAL_AVI_VEHICLES - TOTAL_BOWSERS

    # --- ATG fuel volumes ---
    total_atg_volume = sum(tank_states[t["tank_id"]]["current_volume"] for t in TANKS)
    total_atg_capacity = sum(t["capacity"] for t in TANKS)
    total_consumed_atg = total_atg_capacity - total_atg_volume

    # --- Fuel consumed by each vehicle from vehicle_logs ---
    fuel_consumed_per_vehicle = defaultdict(float)
    for log in vehicle_logs:
        vrn = log["VRN"]
        fuel_consumed_per_vehicle[vrn] += log["Volume_Liters"]

    # --- Split vehicles into bowsers and RTGs ---
    bowser_vehicles = VEHICLES[:TOTAL_BOWSERS]
    rtg_vehicles = VEHICLES[TOTAL_BOWSERS:]

    total_consumed_bowser = sum(fuel_consumed_per_vehicle[v["vrn"]] for v in bowser_vehicles)
    total_consumed_rtg = sum(fuel_consumed_per_vehicle[v["vrn"]] for v in rtg_vehicles)

    # --- RTG capacity assumption ---
    RTG_CAPACITY = 500

    # --- Low-level RTG threshold in liters ---
    LOW_LEVEL_THRESHOLD_LITERS = 499

    # --- Low-level RTG table: those below or equal to threshold liters remaining ---
    low_level_rtgs = []
    for v in rtg_vehicles:
        consumed = fuel_consumed_per_vehicle[v["vrn"]]
        current_fuel = max(RTG_CAPACITY - consumed, 0) 

        if current_fuel <= LOW_LEVEL_THRESHOLD_LITERS:
            last_update = None
            for log in reversed(vehicle_logs):
                if log["VRN"] == v["vrn"]:
                    last_update = log["Timestamp"]
                    break
            low_level_rtgs.append({
                "name": v["vrn"],
                "current_fuel_liters": round(current_fuel, 2),
                "last_update": last_update or "N/A"
            })

    # --- Pie chart for ATG consumed vs remaining fuel ---
    pie_chart = [
        {"label": "Consumed Fuel", "value": round(total_consumed_atg, 2)},
        {"label": "Remaining Fuel", "value": round(total_atg_volume, 2)},
    ]

    # --- chart for fuel volume % (RTGs, ATGs, Bowsers) ---
    total_consumed_fuel = total_consumed_atg + total_consumed_bowser + total_consumed_rtg

    def safe_percent(val, total):
        return round((val / total) * 100, 2) if total > 0 else 0

    bar_chart = [
        {"source": "RTGs", "volume_percent": safe_percent(total_consumed_rtg, total_consumed_fuel)},
        {"source": "ATGs", "volume_percent": safe_percent(total_consumed_atg, total_consumed_fuel)},
        {"source": "Bowsers", "volume_percent": safe_percent(total_consumed_bowser, total_consumed_fuel)},
    ]

    # --- Summary cards ---
    summary_cards = {
        "total_atgs": TOTAL_ATGS,
        "total_bowsers": TOTAL_BOWSERS,
        "total_rtgs": TOTAL_RTGS,
        "total_avi_vehicles": TOTAL_AVI_VEHICLES
    }

    return JSONResponse(content={
        "summary_cards": summary_cards,
        "low_level_rtg_table": low_level_rtgs,
        "fuel_pie_chart": pie_chart,
        "volume_bar_chart": bar_chart
    })

@app.get("/api/debug_rtgs")
async def debug_rtgs():
    RTG_CAPACITY = 500
    fuel_consumed_per_vehicle = defaultdict(float)
    for log in vehicle_logs:
        fuel_consumed_per_vehicle[log["VRN"]] += log["Volume_Liters"]

    rtg_vehicles = VEHICLES[5:]  # Assuming first 5 bowsers
    rtg_fuels = []
    for v in rtg_vehicles:
        consumed = fuel_consumed_per_vehicle[v["vrn"]]
        current_fuel = max(RTG_CAPACITY - consumed, 0)
        rtg_fuels.append({
            "vrn": v["vrn"],
            "consumed": consumed,
            "current_fuel": current_fuel
        })
    return rtg_fuels


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