from datetime import datetime
import uuid
from typing import Any

from resources import *
from fastapi import FastAPI


app = FastAPI()

vehicles = Resource()
mechanics = Resource()
apps = Resource()


''' 
=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
               POSTS             
********************************* 
'''


def get_token(resource: Resource) -> str:
    if len(resource.new_tokens) > 0:
        return resource.new_tokens[0]

    while True:
        token = str(uuid.uuid4().hex[:5])
        not_in_keys = (token not in vehicles.entities.keys() and
                       token not in mechanics.entities.keys() and
                       token not in apps.entities.keys())

        not_in_tokens = (token not in vehicles.new_tokens and
                         token not in mechanics.new_tokens and
                         token not in apps.new_tokens)

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
    async with apps.mutex:
        for appointment in apps.entities.values():
            if appointment.date == transfer.date_from:
                appointment.date = transfer.date_to

    return {
        "message": "appointments rescheduling successful",
        "collection": "appointments"
    }


''' 
=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
               PUTS             
********************************* 
'''


def unpack_args(args: str):
    args = args.split(";")
    if len(args) != 2:
        return args[0], None

    return args[0], args[1]


async def update_collection(entity_id: str, hash_val: str, entity, resource: Resource) -> str:
    if entity_id in resource.new_tokens:
        resource.new_tokens.remove(entity_id)
        entity.hash = entity.get_hash()
        resource.entities[entity_id] = entity

        return f"created entity {entity_id}"

    if hash_val is not None:
        async with resource.mutex:
            if entity_id in resource.entities and resource.entities[entity_id].hash == hash_val:
                entity.hash = entity.get_hash()
                resource.entities[entity_id] = entity

                return f"updated entity {entity_id}"

    return f"create/update failed! Token {entity_id} with corresponding hash {hash_val} not found"


@app.put("/apps/{id_and_hash}")
async def put_appointment(id_and_hash: str, appointment: Appointment):
    app_id, hash_val = unpack_args(id_and_hash)
    if appointment.vehicle_id in vehicles and appointment.mechanic_id in mechanics:
        return {
            "message": await update_collection(app_id, hash_val, appointment, apps),
            "collection": "appointments"
        }
    else:
        return {
            "message": "create/update failed! Invalid vehicle or mechanic token!",
            "collection": "appointments"
        }


@app.put("/vehicles/{id_and_hash}")
async def put_vehicle(id_and_hash: str, vehicle: Vehicle):
    vehicle_id, hash_val = unpack_args(id_and_hash)
    return {
        "message": await update_collection(vehicle_id, hash_val, vehicle, vehicles),
        "collection": "vehicles"
    }


@app.put("/mechanics/{id_and_hash}")
async def put_mechanic(id_and_hash: str, mechanic: Mechanic):
    mechanic_id, hash_val = unpack_args(id_and_hash)
    return {
        "message": await update_collection(mechanic_id, hash_val, mechanic, mechanics),
        "collection": "mechanics"
    }


''' 
=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
               DELETES             
********************************* 
'''


async def delete_from_collection(entity_id: str, hash_val: str, resource: Resource) -> str:
    async with resource.mutex:
        if entity_id in resource.entities and resource.entities[entity_id].hash == hash_val:
            del resource.entities[entity_id]

            return f"deleted entity {entity_id}"

    return f"delete failed! Token {entity_id} with corresponding hash {hash_val} not found "


@app.delete("/apps")
async def delete_future_appointments():
    appointments_copy = apps.entities.copy()
    for (key, appointment) in appointments_copy.items():
        is_in_the_future = datetime.strptime(appointment.date, "%d/%m/%Y") >= datetime.today()

        if is_in_the_future:
            async with apps.mutex:
                if key in apps.entities.keys():
                    apps.entities.pop(key)

    return {
        "message": "future appointments deleted",
        "collection": "appointments"
    }


@app.delete("/apps/{id_and_hash}")
async def delete_appointment(id_and_hash: str):
    args = id_and_hash.split(";")
    if len(args) != 2:
        return {
            "message": "error! Wrong number of arguments! Expected 2 in format: appointment_id;hash",
            "collection": "appointments"
        }

    app_id, hash_val = args[0], args[1]
    return {
        "message": await delete_from_collection(app_id, hash_val, apps),
        "collection": "appointments"
    }


async def remove_vehicle_records(vehicle_id: str, hash_val: str):
    if vehicle_id in vehicles.entities.keys() and vehicles.entities[vehicle_id].hash == hash_val:
        keys_to_pop = []
        async with apps.mutex:
            for (key, appointment) in apps.entities.items():
                if appointment.vehicle_id == vehicle_id:
                    appointment.vehicle_id = "!!!!!"

                    is_in_the_future = datetime.strptime(appointment.date, "%d/%m/%Y") >= datetime.today()
                    if is_in_the_future:
                        keys_to_pop.append(key)

            for key in keys_to_pop:
                apps.entities.pop(key)


@app.delete("/vehicles/{id_and_hash}")
async def delete_vehicle(id_and_hash: str):
    args = id_and_hash.split(";")
    if len(args) != 2:
        return {
            "message": "error! Wrong number of arguments! Expected 2 in format: vehicle_id;hash",
            "collection": "vehicles"
        }

    vehicle_id, hash_val = args[0], args[1]
    await remove_vehicle_records(vehicle_id, hash_val)
    return {
        "message": await delete_from_collection(vehicle_id, hash_val, vehicles),
        "collection": "vehicles"
    }


async def remove_mechanic_records(mechanic_id: str, hash_val: str):
    if mechanic_id in mechanics.entities.keys() and mechanics.entities[mechanic_id].hash == hash_val:
        async with apps.mutex:
            for appointment in apps.entities.values():
                if appointment.mechanic_id == mechanic_id:
                    appointment.mechanic_id = "!!!!!"


@app.delete("/mechanics/{id_and_hash}")
async def delete_mechanic(id_and_hash: str):
    args = id_and_hash.split(";")
    if len(args) != 2:
        return {
            "message": "error! Wrong number of arguments! Expected 2 in format: mechanic_id;hash",
            "collection": "mechanics"
        }

    mechanic_id, hash_val = args[0], args[1]
    await remove_mechanic_records(mechanic_id, hash_val)
    return {
        "message": await delete_from_collection(mechanic_id, hash_val, mechanics),
        "collection": "mechanics"
    }


''' 
=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
               GETS             
********************************* 
'''


def is_in_collection(entity_id: str, resource: Resource) -> str:
    if entity_id in resource.entities:
        return f"get request successful"

    return f"get request failed! Token not found {entity_id}"


def get_from_collection(entity_id: str, resource: Resource):
    if entity_id in resource.entities:
        return resource.entities[entity_id]

    return []


def get_entity_dict(entity_id: str, resource: Resource) -> dict[str, Any]:
    entity = get_from_collection(entity_id, resource)
    dct = {
        "entity_id": entity_id,
    }

    dct.update(entity.to_dict())

    return dct


def get_entities_dict(resource: Resource) -> dict[str, Any]:
    dct = dict([])
    for entity_id, entity in resource.entities.items():
        entity_dct = {
            "entity_id": entity_id,
        }

        entity_dct.update(entity.to_dict())
        dct[entity_id] = entity_dct

    return dct


@app.get("/apps")
async def get_appointments():
    return {
        "message": "getting collection successful",
        "entities": get_entities_dict(apps),
        "collection": "appointments"
    }


@app.get("/apps/{app_id}")
async def get_appointment(app_id: str):
    return {
        "message": is_in_collection(app_id, apps),
        "entity": get_entity_dict(app_id, apps),
        "collection": "appointments"
    }


@app.get("/vehicles")
async def get_vehicles():
    return {
        "message": "getting collection successful",
        "entities": get_entities_dict(vehicles),
        "collection": "vehicles"
    }


@app.get("/vehicles/{vehicle_id}")
async def get_vehicle(vehicle_id: str):
    return {
        "message": is_in_collection(vehicle_id, vehicles),
        "entity": get_entity_dict(vehicle_id, vehicles),
        "collection": "vehicles"
    }


@app.get("/mechanics")
async def get_mechanics():
    return {
        "message": "getting collection successful",
        "entities": get_entities_dict(mechanics),
        "collection": "mechanics"
    }


@app.get("/mechanics/{mechanic_id}")
async def get_mechanic(mechanic_id: str):
    return {
        "message": is_in_collection(mechanic_id, mechanics),
        "entity": get_entity_dict(mechanic_id, mechanics),
        "collection": "mechanics"
    }


''' 
=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
               MAIN             
********************************* 
'''

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
