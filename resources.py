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
