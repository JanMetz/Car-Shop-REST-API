from asyncio import Lock

from pydantic import BaseModel


class Vehicle(BaseModel):
    make: str
    model: str
    registration: str


class Mechanic(BaseModel):
    name: str
    surname: str


class Appointment(BaseModel):
    date: str
    vehicle_id: str
    mechanic_id: str


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
