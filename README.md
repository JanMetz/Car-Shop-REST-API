## Car-Shop-REST-API

# About

This is a simple REST API written as an excercise - it emulates a service that could be used by a car repair shop.

It has entities that represent a car mechanic, vehicle and appointment

Examples of how to use it can be found in the 'tests' folder. 

# Documentation:

| URI	| Post | Get |	Put |	Delete |
| ----- | ----- | ------- | ------- | ------- |
| apps/	| returns new token for appointment |	returns all appoinments |	x |	deletes future appointments |
| vehicles/ |	returns new token for vehicle |	return all vehicles |	x |	x |
| mechanics/ |	returns new token for mechanic	| return all mechanics	| x |	x |
| vehicles/{id},{hash}	| x	| returns vehicle	(hash not required) | updates vehicle |	deletes vehicle and its future appointments |
| apps/{id},{hash}	| x	| returns appointment (hash not required) | updates appointment	| deletes appointment |
| mechanics/{id},{hash} |	x	| returns mechanic (hash not required)	| updates mechanic	| deletes mechanic | 
| transfers/	| reschedules all appointments from one day to another |	x |	x |	x |

# Resources representations:
Mechanic:
{
"name": string,
"surname": string
}

Appointment:
{
"date": date in format DD/MM/YYYY,
"vehicle_id": string,
"mechanic_id": string
}

Vehicle:
{
"make": string,
"model": string,
"registration": string
}

Transfer:
{
"date_from": date in format DD/MM/YYYY,
"date_to": date in format DD/MM/YYYY
}

# Querying:
To limit number of records returned by GET you can add parameters 'start' and 'stop' to your request.

For example GET request on /vehicles?start=0&stop=10 will return first 9 vehicles.


# Dependencies

It was written using pydantic, uuid and fastapi in Python 3.11
