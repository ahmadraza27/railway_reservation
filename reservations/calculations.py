from datetime import datetime, timedelta
from django.db.models import Q
from itertools import product
import pprint
from .models import City, Route, Schedule, Station, Couch, Seat, CouchType,Bed


def get_cities_all():
    cities = City.objects.all()
    all_cities = {city.name for city in cities}
    print("cities are")
    print(all_cities)
    return cities


def calculate_time_difference(arrival_time, departure_time):
    """
    Calculate the time difference in minutes between departure and arrival times.
    Handles cases where the arrival time is on the next day.
    """
    time_format = "%H:%M"  # Define time format (24-hour format)

    # Convert string times to datetime objects
    departure = datetime.strptime(departure_time, time_format)
    arrival = datetime.strptime(arrival_time, time_format)

    # If the arrival time is earlier than departure time, it means the arrival is on the next day
    if arrival < departure:
        # Add 1 day to arrival time to account for the next day
        arrival += timedelta(days=1)

    # Return the time difference in minutes
    return int((arrival - departure).total_seconds() / 60)


def find_all_paths(graph, source_id, destination_id, visited=None, path=None, total_distance=0, total_time=0):
    """
    Find all possible paths between two stations in the graph.
    """
    if visited is None:
        visited = set()
    if path is None:
        path = []

    visited.add(source_id)
    path.append((source_id, total_distance, total_time))

    if source_id == destination_id:
        yield path.copy()

    for neighbor, distance, time in graph.get(source_id, []):
        if neighbor not in visited:
            yield from find_all_paths(
                graph, neighbor, destination_id, visited, path, total_distance +
                distance, total_time + time
            )

    visited.remove(source_id)
    path.pop()


def get_graph_data():
    """
    Build a graph from the Route model, where edges are weighted by distance and time.
    """
    # from .models import Route

    graph = {}
    for route in Route.objects.all():
        source = route.sourceStation.id
        destination = route.destinationStation.id
        distance = route.distanceToDestination
        # travel_time = route.travelTime.hour * 60 + \
        #     route.travelTime.minute  # Convert to minutes
        travel_time = 0
        # Add both directions (bidirectional routes)
        if source not in graph:
            graph[source] = []
        graph[source].append((destination, distance, travel_time))

        # if destination not in graph:
        #     graph[destination] = []
        # graph[destination].append((source, distance, travel_time))

    print("the graph is ")
    print(graph)
    return graph


def fetch_schedules(path, num_beds):
    """
    Fetch schedules for the given path, calculating travel times between stations,
    checking seat availability, and ensuring the number of beds is available.
    Handles multi-day schedules (departure and arrival times crossing midnight).
    """
    print("printing paths in fetching schedule")
    print(path)
    schedules = []
    total_time = 0  # Initialize total travel time in minutes

    # Start with the first station's schedule
    destination_station_id = path[0][0]
    first_schedule = Schedule.objects.filter(
        route__destinationStation_id=destination_station_id
    )
    print(first_schedule)
    element = first_schedule.first().departureTime
    prev_time = element.strftime("%H:%M")

    for i in range(0, len(path) - 1):
        source_station_id = path[i][0]
        destination_station_id = path[i + 1][0]

        # Get the first schedule for the route
        station_schedules = Schedule.objects.filter(
            route__sourceStation_id=source_station_id,
            route__destinationStation_id=destination_station_id
        ).order_by("departureTime")

        if station_schedules.exists():
            schedule = station_schedules.first()
            current_time = schedule.arrivalTime.strftime("%H:%M")
            current_d_time = schedule.departureTime.strftime("%H:%M")

            # Calculate travel time between stations
            travel_time = calculate_time_difference(
                current_time,
                prev_time
            )
            total_time += travel_time

            prev_time = current_d_time

            # Check seat availability for the current schedule
            available_seats = Seat.objects.filter(
                status__status='AVL',  # Assuming 'available' is the status name for available seats
                inACabin=True,
                # Assuming 'train' is related to cabins
                cabin__couch__train__id=schedule.copyTrain.id
            ).count()

            # Check bed availability (assuming similar logic as for seats)
            available_beds = Bed.objects.filter(
                status__status='AVL',  # Assuming 'available' is the status name for available beds
                berth__cabin__couch__train__id=schedule.copyTrain.id
            ).count()

            # Only append the schedule if there are both available seats and available beds
            if available_seats > 0 and available_beds >=int( num_beds):
                schedules.append({
                    "source_station": Station.objects.get(id=source_station_id),
                    "destination_station": Station.objects.get(id=destination_station_id),
                    "train": schedule.copyTrain,
                    "id":schedule.id,
                    "departureTime": schedule.departureTime,
                    "arrivalTime": schedule.arrivalTime,
                    "travel_time": travel_time,  # Travel time in minutes
                    "available_seats": available_seats,  # Available seats count
                    "available_beds": available_beds,  # Available beds count
                })

    return schedules, total_time


def secondary__fetch_schedules(path):
    """
    Fetch schedules for the given path, calculating travel times between stations
    and checking seat availability.
    Handles multi-day schedules (departure and arrival times crossing midnight).
    """
    print("printing paths in fetching schedule")
    print(path)
    schedules = []
    total_time = 0  # Initialize total travel time in minutes

    # Start with the first station's schedule
    destination_station_id = path[0][0]
    first_schedule = Schedule.objects.filter(
        route__destinationStation_id=destination_station_id
    )
    print(first_schedule)
    element = first_schedule.first().departureTime
    prev_time = element.strftime("%H:%M")

    for i in range(0, len(path) - 1):
        source_station_id = path[i][0]
        destination_station_id = path[i + 1][0]

        # Get the first schedule for the route
        station_schedules = Schedule.objects.filter(
            route__sourceStation_id=source_station_id,
            route__destinationStation_id=destination_station_id
        ).order_by("departureTime")

        if station_schedules.exists():
            schedule = station_schedules.first()
            current_time = schedule.arrivalTime.strftime("%H:%M")
            current_d_time = schedule.departureTime.strftime("%H:%M")

            # Calculate travel time between stations
            travel_time = calculate_time_difference(
                current_time,
                prev_time
            )
            total_time += travel_time

            prev_time = current_d_time

            # Check seat availability for the current schedule
            available_seats = Seat.objects.filter(
                status__status='AVL',  # Assuming 'available' is the status name for available seats
                inACabin=True,
                # Assuming 'train' is related to cabins
                cabin__couch__train__id=schedule.copyTrain.id
            ).count()
            available_seats_col = Seat.objects.filter(
                status__status='AVL',  # Assuming 'available' is the status name for available seats
                inACabin=False,
                column__couch__train=schedule.copyTrain  # Assuming 'train' is related to cabins
            ).count()

            # Only append the schedule if there are available seats
            if available_seats > 0:
                schedules.append({
                    "source_station": Station.objects.get(id=source_station_id),
                    "destination_station": Station.objects.get(id=destination_station_id),
                    "train": schedule.copyTrain,
                    "departureTime": schedule.departureTime,
                    "arrivalTime": schedule.arrivalTime,
                    "travel_time": travel_time,  # Travel time in minutes
                    "available_seats": available_seats,  # Available seats count
                })

    return schedules, total_time


def get_all_couch_types():
    types = CouchType.objects.all()
    return types


def get_all_routes(source_city, destination_city,beds, order=1):
    # from .models import Station

    source_stations = Station.objects.filter(city_id=source_city)
    destination_stations = Station.objects.filter(city_id=destination_city)

    if not source_stations.exists() or not destination_stations.exists():
        return {"shortest_path": None, "all_paths": []}

    graph = get_graph_data()

    all_paths = []
    for source in source_stations:
        for destination in destination_stations:
            for path in find_all_paths(graph, source.id, destination.id):
                print("the all paths from " + source.city.name +
                      " to " + destination.city.name)
                print(path)

                schedules, total_time = fetch_schedules(path,beds)
                total_distance = sum(p[1] for p in path)
                all_paths.append((total_distance, total_time, path, schedules))

    # Sort by distance and then time
    if order == 1:
        all_paths.sort(key=lambda x: (x[0], x[1]))
    elif order == 2:
        all_paths.sort(key=lambda x: (x[1], x[0]))

    if not all_paths:
        return {"shortest_path": None, "all_paths": []}

    shortest_path = all_paths[0]
    other_paths = all_paths[1:] if len(all_paths) > 1 else []

    result = {
        "shortest_path": {
            "distance": shortest_path[0],
            "time": shortest_path[1],
            "path": shortest_path[2],
            "schedules": shortest_path[3],
        },
        "all_paths": [
            {
                "distance": path[0],
                "time": path[1],
                "path": path[2],
                "schedules": path[3],
            }
            for path in other_paths
        ],
    }
    print("result is ")
    pprint.pprint(result, indent=4, width=100)
    return result


def check_seat_availability(train_id):
    """
    Check available seats in all couches of a given train.
    """
    # from .models import Couch, Seat

    couches = Couch.objects.filter(train_id=train_id)
    availability = []

    for couch in couches:
        seats = Seat.objects.filter(cabin__couch=couch, status__status="AVL")
        availability.append({
            "couch": couch,
            "available_seats": seats.count(),
            "seats": seats,
        })

    return availability


def book_seat(seat_id, user):
    """
    Book a specific seat for a user.
    """
    from .models import Seat, Status, UserBooking

    try:
        seat = Seat.objects.get(id=seat_id, status__status="AVL")
        reserved_status = Status.objects.get(status="RES")

        seat.status = reserved_status
        seat.save()

        # Create a booking record
        UserBooking.objects.create(
            user=user,
            schedule=seat.cabin.couch.train,
        )

        return {"success": True, "message": f"Seat {seat.seatNumber} reserved successfully."}

    except Seat.DoesNotExist:
        return {"success": False, "message": "Seat is not available."}


def print_routes(routes):
    """
    Print route details in a readable format.
    """
    print("Shortest Path:")
    print(f"  Distance: {routes['shortest_path']['distance']} km")
    print(f"  Time: {routes['shortest_path']['time']} minutes")
    print("  Path:")
    for station in routes["shortest_path"]["path"]:
        print(f"    - Station {station[0]}")

    print("\nOther Paths:")
    for path in routes["all_paths"]:
        print(f"  Distance: {path['distance']} km")
        print(f"  Time: {path['time']} minutes")
        print("  Path:")
        for station in path["path"]:
            print(f"    - Station {station[0]}")
