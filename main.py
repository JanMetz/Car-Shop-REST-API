from datetime import datetime
import uuid
from resources import *
from fastapi import FastAPI


app = FastAPI()

vehicles = dict([])
mechanics = dict([])
appointments = dict([])

new_tokens_apps = []
new_tokens_mechanics = []
new_tokens_vehicles = []


# *************** POSTS ***************

def get_token(new_tokens):
    if len(new_tokens) > 0:
        return new_tokens[0]

    while True:
        token = str(uuid.uuid4().hex[:5])
        not_in_keys = token not in vehicles.keys() and token not in mechanics.keys() and token not in appointments.keys()
        not_in_tokens = token not in new_tokens_apps and token not in new_tokens_mechanics and token not in new_tokens_vehicles

        if not_in_tokens and not_in_keys:
            new_tokens.append(token)
            return token


@app.post("/apps")
async def post_apps():
    if len(mechanics.keys()) == 0 or len(vehicles.keys()) == 0:
        return {
            "token": "-1",
            "message": "token generation failed! At least 1 mechanic and 1 vehicle are required",
            "collection": "apps"
        }
    else:
        return {
            "token": get_token(new_tokens_apps),
            "message": "token created",
            "collection": "apps"
        }


@app.post("/vehicles")
async def post_vehicles():
    return {
        "token":  get_token(new_tokens_vehicles),
        "message": "token created",
        "collection": "vehicles"
    }


@app.post("/mechanics")
async def post_mechanics():
    return {
        "token":  get_token(new_tokens_mechanics),
        "message": "token created",
        "collection": "mechanics"
    }


@app.post("/transfers")
async def post_transfer(transfer: Transfer):
    for appointment in appointments.values():
        if appointment.date == transfer.date_from:
            appointment.date = transfer.date_to

    return {
        "message": "appointments rescheduling successful",
        "collection": "appointments"
    }


# *************** PUTS ***************

def update_collection(entity_id, collection, entity, new_tokens):
    if entity_id in new_tokens:
        new_tokens.remove(entity_id)
        collection[entity_id] = entity

        return f"created entity {entity_id}"

    elif entity_id in collection:
        collection[entity_id] = entity

        return f"updated entity {entity_id}"

    return f"create/update failed! Token {entity_id} not found"


@app.put("/apps/{app_id}")
async def put_appointment(app_id: str, appointment: Appointment):
    if appointment.vehicle_id in vehicles and appointment.mechanic_id in mechanics:
        return {
            "message": update_collection(app_id, appointments, appointment, new_tokens_apps),
            "collection": "appointments"
        }
    else:
        return {
            "message": "create/update failed! Invalid vehicle or mechanic token!",
            "collection": "appointments"
        }


@app.put("/vehicles/{vehicle_id}")
async def put_vehicle(vehicle_id: str, vehicle: Vehicle):
    return {
        "message": update_collection(vehicle_id, vehicles, vehicle, new_tokens_vehicles),
        "collection": "vehicles"
    }


@app.put("/mechanics/{mechanic_id}")
async def put_mechanic(mechanic_id: str, mechanic: Mechanic):
    return {
        "message": update_collection(mechanic_id, mechanics, mechanic, new_tokens_mechanics),
        "collection": "mechanics"
    }


# *************** DELETES ***************

def delete_from_collection(entity_id, collection):
    if entity_id in collection:
        del collection[entity_id]

        return f"deleted entity {entity_id}"

    return f"delete failed! Token not found {entity_id}"


@app.delete("/apps")
async def delete_future_appointments():
    appointments_copy = appointments.copy()
    for (key, appointment) in appointments_copy.items():
        is_in_the_future = datetime.strptime(appointment.date, "%d/%m/%Y") >= datetime.today()

        if is_in_the_future:
            appointments.pop(key)

    return {
        "message": "future appointments deleted",
        "collection": "appointments"
    }


@app.delete("/apps/{app_id}")
async def delete_appointment(app_id: str):
    return {
        "message": delete_from_collection(app_id, appointments),
        "collection": "appointments"
    }


@app.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: str):
    keys_to_pop = []
    for (key, appointment) in appointments.items():
        if appointment.vehicle_id == vehicle_id:
            appointment.vehicle_id = "!!!!!"

            is_in_the_future = datetime.strptime(appointment.date, "%d/%m/%Y") >= datetime.today()
            if is_in_the_future:
                keys_to_pop.append(key)

    for key in keys_to_pop:
        appointments.pop(key)

    return {
        "message": delete_from_collection(vehicle_id, vehicles),
        "collection": "vehicles"
    }


@app.delete("/mechanics/{mechanic_id}")
async def delete_mechanic(mechanic_id: str):
    for appointment in appointments.values():
        if appointment.mechanic_id == mechanic_id:
            appointment.mechanic_id = "!!!!!"

    return {
        "message": delete_from_collection(mechanic_id, mechanics),
        "collection": "mechanics"
    }


# *************** GETS ***************

def is_in_collection(entity_id, collection):
    if entity_id in collection:

        return f"got entity {entity_id}"

    return f"get failed! Token not found {entity_id}"


def get_from_collection(entity_id, collection):
    if entity_id in collection:

        return collection[entity_id]

    return []


@app.get("/apps")
async def get_appointments():
    return {
        "message": "getting collection successful",
        "entity": appointments,
        "collection": "appointments"
    }


@app.get("/apps/{app_id}")
async def get_appointment(app_id: str):
    return {
        "message": is_in_collection(app_id, appointments),
        "entity": get_from_collection(app_id, appointments),
        "collection": "appointments"
    }


@app.get("/vehicles")
async def get_vehicles():
    return {
        "message": "getting collection successful",
        "entity": vehicles,
        "collection": "vehicles"
    }


@app.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    return {
        "message": is_in_collection(vehicle_id, vehicles),
        "entity": get_from_collection(vehicle_id, vehicles),
        "collection": "vehicles"
    }


@app.get("/mechanics")
async def get_mechanics():
    return {
        "message": "getting collection successful",
        "entity": mechanics,
        "collection": "mechanics"
    }


@app.get("/mechanics/{mechanic_id}")
async def get_mechanic(mechanic_id: str):
    return {
        "message": is_in_collection(mechanic_id, mechanics),
        "entity": get_from_collection(mechanic_id, mechanics),
        "collection": "mechanics"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
