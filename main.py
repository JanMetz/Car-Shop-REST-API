from datetime import datetime
import uuid
import hashlib
from resources import *
from fastapi import FastAPI


app = FastAPI()

vehicles = Resource()
mechanics = Resource()
apps = Resource()


# *************** POSTS ***************

def get_token(resource: Resource) -> str:
    if len(resource.new_tokens) > 0:
        return resource.new_tokens[0]

    while True:
        token = str(uuid.uuid4().hex[:5])
        not_in_keys = token not in vehicles.entities.keys() and token not in mechanics.entities.keys() and token not in apps.entities.keys()
        not_in_tokens = token not in vehicles.new_tokens and token not in mechanics.new_tokens and token not in apps.new_tokens

        if not_in_tokens and not_in_keys:
            resource.new_tokens.append(token)
            return token


@app.post("/apps")
async def post_apps():
    if len(mechanics.entities.keys()) == 0 or len(vehicles.entities.keys()) == 0:
        return {
            "token": "-1",
            "message": "token generation failed! At least 1 mechanic and 1 vehicle are required",
            "collection": "apps"
        }
    else:
        return {
            "token": get_token(apps),
            "message": "token created",
            "collection": "apps"
        }


@app.post("/vehicles")
async def post_vehicles():
    return {
        "token":  get_token(vehicles),
        "message": "token created",
        "collection": "vehicles"
    }


@app.post("/mechanics")
async def post_mechanics():
    return {
        "token":  get_token(mechanics),
        "message": "token created",
        "collection": "mechanics"
    }


@app.post("/transfers")
async def post_transfer(transfer: Transfer):
    for appointment in apps.entities.values():
        if appointment.date == transfer.date_from:
            appointment.date = transfer.date_to

    return {
        "message": "appointments rescheduling successful",
        "collection": "appointments"
    }


# *************** PUTS ***************

def update_collection(entity_id: str, entity, resource: Resource) -> str:
    if entity_id in resource.new_tokens:
        resource.new_tokens.remove(entity_id)
        resource.entities[entity_id] = entity

        return f"created entity {entity_id}"

    elif entity_id in resource.entities:
        resource.entities[entity_id] = entity

        return f"updated entity {entity_id}"

    return f"create/update failed! Token {entity_id} not found"


@app.put("/apps/{app_id}")
async def put_appointment(app_id: str, appointment: Appointment):
    if appointment.vehicle_id in vehicles and appointment.mechanic_id in mechanics:
        return {
            "message": update_collection(app_id, appointment, apps),
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
        "message": update_collection(vehicle_id, vehicle, vehicles),
        "collection": "vehicles"
    }


@app.put("/mechanics/{mechanic_id}")
async def put_mechanic(mechanic_id: str, mechanic: Mechanic):
    return {
        "message": update_collection(mechanic_id, mechanic, mechanics),
        "collection": "mechanics"
    }


# *************** DELETES ***************

def delete_from_collection(entity_id: str, resource: Resource) -> str:
    if entity_id in resource.entities:
        del resource.entities[entity_id]

        return f"deleted entity {entity_id}"

    return f"delete failed! Token not found {entity_id}"


@app.delete("/apps")
async def delete_future_appointments():
    appointments_copy = apps.entities.copy()
    for (key, appointment) in appointments_copy.items():
        is_in_the_future = datetime.strptime(appointment.date, "%d/%m/%Y") >= datetime.today()

        if is_in_the_future:
            apps.entities.pop(key)

    return {
        "message": "future appointments deleted",
        "collection": "appointments"
    }


@app.delete("/apps/{app_id}")
async def delete_appointment(app_id: str):
    return {
        "message": delete_from_collection(app_id, apps),
        "collection": "appointments"
    }


@app.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: str):
    keys_to_pop = []
    for (key, appointment) in apps.entities.items():
        if appointment.vehicle_id == vehicle_id:
            appointment.vehicle_id = "!!!!!"

            is_in_the_future = datetime.strptime(appointment.date, "%d/%m/%Y") >= datetime.today()
            if is_in_the_future:
                keys_to_pop.append(key)

    for key in keys_to_pop:
        apps.entities.pop(key)

    return {
        "message": delete_from_collection(vehicle_id, vehicles),
        "collection": "vehicles"
    }


@app.delete("/mechanics/{mechanic_id}")
async def delete_mechanic(mechanic_id: str):
    for appointment in apps.entities.values():
        if appointment.mechanic_id == mechanic_id:
            appointment.mechanic_id = "!!!!!"

    return {
        "message": delete_from_collection(mechanic_id, mechanics),
        "collection": "mechanics"
    }


# *************** GETS ***************

def is_in_collection(entity_id: str, resource: Resource) -> str:
    if entity_id in resource.entities:

        return f"got entity {entity_id}"

    return f"get failed! Token not found {entity_id}"


def get_from_collection(entity_id: str, resource: Resource):
    if entity_id in resource.entities:

        return resource.entities[entity_id]

    return []


@app.get("/apps")
async def get_appointments():
    return {
        "message": "getting collection successful",
        "entity": apps.entities,
        "collection": "appointments"
    }


@app.get("/apps/{app_id}")
async def get_appointment(app_id: str):
    return {
        "message": is_in_collection(app_id, apps),
        "entity": get_from_collection(app_id, apps),
        "collection": "appointments"
    }


@app.get("/vehicles")
async def get_vehicles():
    return {
        "message": "getting collection successful",
        "entity": vehicles.entities,
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
        "entity": mechanics.entities,
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
