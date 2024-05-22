from asyncio import Lock

from pydantic import BaseModel


class Vehicle(BaseModel):
    make: str
    model: str
    registration: str

    def to_dict(self):
        return {"make": self.make, "model": self.model, "registration": self.registration}


class Mechanic(BaseModel):
    name: str
    surname: str

    def to_dict(self):
        return {"name": self.name, "surname": self.surname}


class Appointment(BaseModel):
    date: str
    vehicle_id: str
    mechanic_id: str

    def to_dict(self):
        return {"date": self.date, "vehicle_id": self.vehicle_id, "mechanic_id": self.mechanic_id}


class Transfer(BaseModel):
    date_from: str
    date_to: str


class Resource:
    new_tokens = None
    entities = None
    mutex = None

    def __init__(self):
        self.mutex = Lock()
        self.new_tokens = []
        self.entities = dict([])
