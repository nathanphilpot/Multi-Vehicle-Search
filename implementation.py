from fastapi import FastAPI, Body
import json
from collections import defaultdict
from itertools import combinations, chain

"""Python implementation of an API. Host your api locally using uvicorn. 
   Install fastapi and json. Make sure listings.json is in the same directory as this script.
"""

#say hi to Sean
app = FastAPI()
@app.get("/")
def say_hello():
    return {'Message for Neighbor': 'Hey Sean!'}

#vehicle class for user input
class Vehicle():
    def __init__(self, length, width=10, id=None):
        self.length = length
        self.width = width
        self.total_area = width * length
        self.id = id

#main post function for analyzing our data
@app.post("/")
def process_vehicles(vehicles = Body(...)):

    #receives a list of vehicles and stores them in python memory
    stored_vehicles = _get_vehicles_from_post(vehicles)

    #gets the listings into python
    with open("listings.json", "r") as f:
        listings = json.load(f)

    #uses listings and stored vehicles to get list of places that fit
    final_results = _find_places_that_vehicles_fit(stored_vehicles, listings)

    
    with open("results.json", "w") as f:
        json.dump(final_results, f, indent=4)

    return {"Results": final_results}





#helper functions
def _get_vehicles_from_post(vehicles):

    """This function is mostly useless since we don't use width or total area,
       but it helped me get familiar with fastapi!
    """

    #store the vehicles in python memory for future use
    stored_vehicles = []

    for entry in vehicles:
        #entry validation
        if "length" not in entry or "quantity" not in entry:
            raise fastapi.HTTPException(status_code=400, detail="Each entry must have length and quantity")
        
        length = entry["length"]
        quantity = entry["quantity"]

        #create individual vehicle object for each 
        for i in range(quantity):
            vehicle_obj = Vehicle(length=length, id=len(stored_vehicles) + 1) #use stored vehicles as a counter for id
            stored_vehicles.append(vehicle_obj)

    return stored_vehicles

def _find_places_that_vehicles_fit(stored_vehicles, listings):

    """Four key assumptions are made in this analysis that allow
       us to entirely ignore using width in our calculation.

       1. Width of vehicles is always ten
       2. Width of spaces are always multiples of ten
       3. Vehicles are always stored in the same direction
       4. There is no buffer space between vehicles

       I hope it is okay that,
       This function uses powersets instead of any greedy/time optimized approach
       because the instructions say "We're primarily looking to see that candidates 
       can get a solution working, deployed, and reasonably performant"
       This runs on my laptop < 300ms from when I hit enter on my post command
       to when it spits out the hundreds of results.

    """

    listings_by_location = defaultdict(list)
    results = []

    #group listing id's by their location id's
    for listing in listings:
        listings_by_location[listing["location_id"]].append(listing)
    
    #store all vehicle lengths to get total length
    requested_lengths = []
    for vehicle in stored_vehicles:
        requested_lengths.append(vehicle.length)

    for location_id, id_list_of_spaces in listings_by_location.items():
        min_total_price_of_location = None
        best_spaces_combo_of_location = None

        #use powersets of listings to find best combo, a naive approach to the knapsack/bin packing problem
        for combo in chain.from_iterable(combinations(id_list_of_spaces, r) for r in range(len(id_list_of_spaces)+1)):
            #total length of space in this combo
            total_length = sum(l["length"] for l in combo)
            #check if vehicles will fit in this combo, if so, then check if it is our cheapest option
            if total_length >= sum(requested_lengths):
                total_price = sum(l["price_in_cents"] for l in combo)
                if min_total_price_of_location is None or total_price < min_total_price_of_location:
                    min_total_price_of_location = total_price
                    best_spaces_combo_of_location = combo
        if best_spaces_combo_of_location:
            results.append({
                "location_id": location_id,
                "listing_ids": [l["id"] for l in best_spaces_combo_of_location],
                "total_price_in_cents": min_total_price_of_location
            })

    #sort results
    results.sort(key=lambda x: x["total_price_in_cents"])
    return results