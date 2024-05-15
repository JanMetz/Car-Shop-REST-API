## Car-Shop-REST-API

This is a simple REST API written as an excercise - it emulates a service that could be used in a car repair shop.

It has entities that represent a car mechanic, vehicle and appointment

Examples of how to use it can be found in the 'tests' folder. 

Documentation:

| Adres URI	| Post | Get |	Put |	Delete |
| ----- | ----- | ------- | ------- | ------- |
| apps/	| returns new token for appointment |	returns all appoinments |	x |	deletes future appointments |
| vehicles/ |	returns new token for vehicle |	return all vehicles |	x |	x |
| mechanics/ |	returns new token for mechanic	| return all mechanics	| x |	x |
| vehicles/{id}	| x	| returns vehicle	| updates vehicle |	deletes vehicle and its future appointments |
| apps/{id}	| x	| returns appointment | updates appointment	| deletes appointment |
| mechanics/{id} |	x	| returns mechanic	| updates mechanic	| deletes mechanic | 
| transfers/	| reschedules all appointments from one day to another |	x |	x |	x |

