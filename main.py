from datetime import datetime
import uuid
from typing import Any

from resources import *
from fastapi import FastAPI, Query


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
        not_in_keys = (token not in vehicles.tokens and
                       token not in mechanics.tokens and
                       token not in apps.tokens)

        not_in_tokens = (token not in vehicles.new_tokens and
                         token not in mechanics.new_tokens and
                         token not in apps.new_tokens)

        if not_in_tokens and not_in_keys:
            resource.new_tokens.append(token)
            return token


@app.post("/apps")
async def post_apps():
    if len(mechanics.tokens) == 0 or len(vehicles.tokens) == 0:
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
        for appointment in apps.entities:
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
    args = args.split(",")
    if len(args) != 2:
        return args[0], None

    return args[0], args[1]


async def update_collection(entity_id: str, hash_val: str, entity, resource: Resource) -> str:
    if entity_id in resource.new_tokens:
        resource.new_tokens.remove(entity_id)
        entity.hash = entity.get_hash()
        resource.entities.append(entity)
        resource.tokens.append(entity_id)

        return f"created entity {entity_id}"

    if hash_val is not None:
        async with resource.mutex:
            try:
                idx = resource.tokens.index(entity_id)
                if resource.entities[idx].hash == hash_val:
                    entity.hash = entity.get_hash()
                    resource.entities[idx] = entity

                    return f"updated entity {entity_id}"
            except ValueError:
                pass

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
        try:
            idx = resource.tokens.index(entity_id)
            if resource.entities[idx].hash == hash_val:
                del resource.entities[idx]
                del resource.tokens[idx]
                return f"deleted entity {entity_id}"

        except ValueError:
            pass

    return f"delete failed! Token {entity_id} with corresponding hash {hash_val} not found "


@app.delete("/apps")
async def delete_future_appointments():
    apps_entities_copy = apps.entities.copy()
    apps_tokens_copy = apps.tokens.copy()

    for (key, appointment) in zip(apps_tokens_copy, apps_entities_copy):
        is_in_the_future = datetime.strptime(appointment.date, "%d/%m/%Y") >= datetime.today()

        if is_in_the_future:
            async with apps.mutex:
                try:
                    idx = apps.tokens.index(key)
                    del apps.entities[idx]
                    del apps.tokens[idx]
                except ValueError:
                    pass

    return {
        "message": "future appointments deleted",
        "collection": "appointments"
    }


@app.delete("/apps/{id_and_hash}")
async def delete_appointment(id_and_hash: str):
    args = id_and_hash.split(",")
    if len(args) != 2:
        return {
            "message": "error! Wrong number of arguments! Expected 2 in format: appointment_id,hash",
            "collection": "appointments"
        }

    app_id, hash_val = args[0], args[1]
    return {
        "message": await delete_from_collection(app_id, hash_val, apps),
        "collection": "appointments"
    }


async def remove_vehicle_records(vehicle_id: str, hash_val: str):
    try:
        idx = vehicles.tokens.index(vehicle_id)
        if vehicles.entities[idx].hash == hash_val:
            idxs_to_pop = []
            async with apps.mutex:
                for (idx, appointment) in enumerate(apps.entities):
                    if appointment.vehicle_id == vehicle_id:
                        appointment.vehicle_id = "!!!!!"

                        is_in_the_future = datetime.strptime(appointment.date, "%d/%m/%Y") >= datetime.today()
                        if is_in_the_future:
                            idxs_to_pop.append(idx)

                for idx in idxs_to_pop:
                    del apps.entities[idx]
                    del apps.tokens[idx]
    except ValueError:
        pass


@app.delete("/vehicles/{id_and_hash}")
async def delete_vehicle(id_and_hash: str):
    args = id_and_hash.split(",")
    if len(args) != 2:
        return {
            "message": "error! Wrong number of arguments! Expected 2 in format: vehicle_id,hash",
            "collection": "vehicles"
        }

    vehicle_id, hash_val = args[0], args[1]
    await remove_vehicle_records(vehicle_id, hash_val)
    return {
        "message": await delete_from_collection(vehicle_id, hash_val, vehicles),
        "collection": "vehicles"
    }


async def remove_mechanic_records(mechanic_id: str, hash_val: str):
    try:
        idx = mechanics.tokens.index(mechanic_id)
        if mechanics.entities[idx].hash == hash_val:
            async with apps.mutex:
                for appointment in apps.entities:
                    if appointment.mechanic_id == mechanic_id:
                        appointment.mechanic_id = "!!!!!"
    except ValueError:
        pass


@app.delete("/mechanics/{id_and_hash}")
async def delete_mechanic(id_and_hash: str):
    args = id_and_hash.split(",")
    if len(args) != 2:
        return {
            "message": "error! Wrong number of arguments! Expected 2 in format: mechanic_id,hash",
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
    if entity_id in resource.tokens:
        return f"get request successful"

    return f"get request failed! Token not found {entity_id}"


def get_from_collection(entity_id: str, resource: Resource):
    try:
        idx = resource.tokens.index(entity_id)
        return resource.entities[idx]
    except ValueError:
        return None


def get_entity_dict(entity_id: str, resource: Resource) -> dict[str, Any]:
    entity = get_from_collection(entity_id, resource)
    dct = dict([])
    if entity is not None:
        dct = {
            "entity_id": entity_id,
        }

        dct.update(entity.to_dict())

    return dct


def get_entities_dict(resource: Resource, start: int, stop: int) -> list[Any]:
    dct = []

    if 0 <= start <= stop:
        for entity_id, entity in zip(resource.tokens[start:stop], resource.entities[start:stop]):
            entity_dct = {
                "entity_id": entity_id,
            }

            entity_dct.update(entity.to_dict())
            dct.append(entity_dct)

    return dct


@app.get("/apps")
async def get_appointments(start: int = Query(default=0), stop: int = Query(default=5)):
    return {
        "message": "getting collection successful",
        "entities": get_entities_dict(apps, start, stop),
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
async def get_vehicles(start: int = Query(default=0), stop: int = Query(default=5)):
    return {
        "message": "getting collection successful",
        "entities": get_entities_dict(vehicles, start, stop),
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
async def get_mechanics(start: int = Query(default=0), stop: int = Query(default=5)):
    return {
        "message": "getting collection successful",
        "entities": get_entities_dict(mechanics, start, stop),
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
