import hashlib
from asyncio import Lock

from pydantic import BaseModel


class Vehicle(BaseModel):
    make: str
    model: str
    registration: str
    hash: str

    def to_dict(self):
        return {"make": self.make, "model": self.model, "registration": self.registration, "hash": self.hash}

    def get_hash(self) -> str:
        serialized = str(self.make).encode('utf-8') + str(self.model).encode('utf-8') + str(self.registration).encode('utf-8')

        return hashlib.md5(serialized).hexdigest()


class Mechanic(BaseModel):
    name: str
    surname: str
    hash: str

    def to_dict(self):
        return {"name": self.name, "surname": self.surname, "hash": self.hash}

    def get_hash(self) -> str:
        serialized = str(self.name).encode('utf-8') + str(self.surname).encode('utf-8')

        return hashlib.md5(serialized).hexdigest()


class Appointment(BaseModel):
    date: str
    vehicle_id: str
    mechanic_id: str
    hash: str

    def to_dict(self):
        return {"date": self.date, "vehicle_id": self.vehicle_id, "mechanic_id": self.mechanic_id, "hash": self.hash}

    def get_hash(self) -> str:
        serialized = str(self.date).encode('utf-8') + str(self.vehicle_id).encode('utf-8') + str(self.mechanic_id).encode('utf-8')

        return hashlib.md5(serialized).hexdigest()


class Transfer(BaseModel):
    date_from: str
    date_to: str


class DeleteRequest(BaseModel):
    hash: str


class Resource:
    new_tokens = None
    entities = None
    mutex = None

    def __init__(self):
        self.mutex = Lock()
        self.new_tokens = []
        self.entities = dict([])
