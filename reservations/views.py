# Assuming calculations is your module for getting cities and routes
from django.db.models import Q
import json
import pprint
from django.http import Http404, HttpResponseForbidden
from django.views.generic import ListView, UpdateView, DeleteView
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from . import calculations
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from . import calculations
# Create your views here.
from django.forms import modelform_factory, modelformset_factory
from .models import Train, CouchType, Couch, Cabin, Seat, Location, Status, UserBooking, Schedule, User, Berth, Bed, Bill
from .forms import *
from .forms import AddCouchForm  # Assuming you create a CouchForm
from django.views.decorators.csrf import csrf_exempt
from .decorators import allowed_users


@login_required(login_url='login')
def logout_view(request):
    """Logs out the user and redirects to the homepage."""
    logout(request)
    return redirect("/")


allowed_users(allowed_roles=['admin'])


def collector_signup_view(request):
    # if request.user.is_authenticated:
    #     return redirect("/")  # Redirect to home if already logged in
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        email = request.POST.get("email")  # Get the email from the form

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        # Check if email already exists
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
        else:
            user = User.objects.create_user(
                username=username, password=password, email=email)  # Add email
            user.groups.add(Group.objects.get(name="collector"))
            user.save()
            login(request, user)
            return redirect("/")  # Redirect to the home page after signup

    return render(request, "auth/collector_signup.html", {'is_admin': is_admin, 'is_collector': is_collector})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("/")  # Redirect to home if already logged in
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False

    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        email = request.POST.get("email")  # Get the email from the form

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
        # Check if email already exists
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
        else:
            user = User.objects.create_user(
                username=username, password=password, email=email)  # Add email
            user.groups.add(Group.objects.get(name="user"))
            user.save()
            login(request, user)
            return redirect("/")  # Redirect to the home page after signup

    return render(request, "auth/signup.html", {'is_admin': is_admin, 'is_collector': is_collector})


def login_view(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    if request.user.is_authenticated:
        return redirect("/")  # Redirect to home if already logged in
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("/")  # Redirect to the home page after login
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "auth/login.html", {'is_admin': is_admin, 'is_collector': is_collector})

# @csrf_exempt
# def toggle_all_cabins(request, couch_id):
#     if request.method == 'POST':
#         # Fetch the couch and its cabins
#         couch = get_object_or_404(Couch, id=couch_id)
#         cabins = couch.cabin_set.all()

#         # Check if all cabins are currently open
#         all_open = all(cabin.open for cabin in cabins)

#         # Toggle status
#         new_status = not all_open
#         cabins.update(open=new_status)

#         # Return a success response with the new status
#         return JsonResponse({"message": "Cabins updated successfully.", "new_status": new_status})

#     return JsonResponse({"error": "Invalid request method."}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
@allowed_users(allowed_roles=['admin'])
def toggle_all_cabins(request, couch_id):
    """
    Toggles the state of all cabins in the specified couch.
    If all cabins are open, they will be closed. If any cabin is closed, all will be opened.
    """
    # Fetch the couch and related cabins
    couch = get_object_or_404(Couch, id=couch_id)
    cabins = couch.cabin_set.all()

    # Determine the new status: toggle to "open" if any cabin is closed, or "closed" if all are open
    all_open = all(cabin.open for cabin in cabins)
    new_status = not all_open

    # Update all cabins to the new status
    cabins.update(open=new_status)

    # Return a JSON response with the updated status
    return JsonResponse({
        "message": f"All cabins have been {'opened' if new_status else 'closed'}.",
        "new_status": new_status
    })


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def add_couch(request, train_id):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    train = get_object_or_404(Train, pk=train_id)

    if request.method == "POST":
        form = AddCouchForm(request.POST)
        if form.is_valid():
            couch = form.save(commit=False)
            couch.train = train  # Associate the couch with the current train
            couch.save()
            messages.success(request, "Couch successfully added!")
            return redirect("train_detail", train_id=train.id)
        else:
            messages.error(request, "There was an error adding the couch.")
    else:
        form = AddCouchForm()

    couch_types = CouchType.objects.all()

    context = {
        "form": form,
        "train": train,
        "couch_types": couch_types,
        'is_admin': is_admin,
    }
    return render(request, "reservations/add_couch_modal.html", context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin', 'collector'])
def train_detail(request, train_id):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    train = get_object_or_404(Train, pk=train_id)
    couches = Couch.objects.filter(train=train).prefetch_related(
        'type', 'cabin_set', 'column')
    couch_types = CouchType.objects.all()

    # Fetch cabin and berth details for each couch
    couch_data = []
    for couch in couches:
        cabins = couch.cabin_set.all()
        columns = couch.column

        # Determine if all cabins are open
        all_open = all(cabin.open for cabin in cabins)

        cabin_details = []
        for cabin in cabins:
            berths = Berth.objects.filter(cabin=cabin)
            beds = Bed.objects.filter(berth__cabin=cabin)
            cabin_details.append({
                "id": cabin.id,
                "code": cabin.code,
                "seatSize": cabin.seatSize,
                "open": cabin.open,
                "seats": cabin.seat_set.all(),
                "beds": beds,  # Add the berths to the cabin details
            })

        column_details = {
            "id": columns.id if columns else None,
            "seatSize": columns.seatSize if columns else None,
            "seats": columns.seat_set.all() if columns else None
        }

        couch_data.append({
            "id": couch.id,
            "type": couch.type.name,
            "cabinSize": couch.cabinSize,
            "code": couch.code,
            "all_open": all_open,  # Pass the open/close state of the cabins
            "cabins": cabin_details,
            "column": column_details
        })

    context = {
        "train": train,
        "couches": couch_data,
        "couch_types": couch_types,
        'is_admin': is_admin,
        'is_collector': is_collector,
    }
    print("context in trail detial is ")
    pprint.pprint(context)
    return render(request, 'reservations/train_detail.html', context)


def main_train_detail(request, train_id):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    train = get_object_or_404(Train, pk=train_id)
    couches = Couch.objects.filter(train=train).prefetch_related(
        'type', 'cabin_set', 'column')
    couch_types = CouchType.objects.all()
    # Fetch cabin and seat details for each couch
    couch_data = []
    for couch in couches:
        cabins = couch.cabin_set.all()
        columns = couch.column

        # Determine if all cabins are open
        all_open = all(cabin.open for cabin in cabins)

        cabin_details = [
            {
                "id": cabin.id,
                "code": cabin.code,
                "seatSize": cabin.seatSize,
                "open": cabin.open,
                "seats": cabin.seat_set.all()
            }
            for cabin in cabins
        ]

        column_details = {
            "id": columns.id if columns else None,
            "seatSize": columns.seatSize if columns else None,
            "seats": columns.seat_set.all() if columns else None
        }

        couch_data.append({
            "id": couch.id,
            "type": couch.type.name,
            "cabinSize": couch.cabinSize,
            "code": couch.code,
            "all_open": all_open,  # Pass the open/close state of the cabins
            "cabins": cabin_details,
            "column": column_details
        })

    context = {
        "train": train,
        "couches": couch_data,
        "couch_types": couch_types,
        'is_admin': is_admin,
        'is_collector': is_collector,
    }
    return render(request, 'reservations/train_detail.html', context)


def ytrain_detail(request, train_id):
    train = get_object_or_404(Train, pk=train_id)
    couches = Couch.objects.filter(train=train).prefetch_related(
        'type', 'cabin_set', 'column')

    # Fetch cabin and seat details for each couch
    couch_data = []
    for couch in couches:
        cabins = couch.cabin_set.all()
        columns = couch.column

        cabin_details = [
            {
                "id": cabin.id,
                "code": cabin.code,
                "seatSize": cabin.seatSize,
                "open": cabin.open,
                "seats": cabin.seat_set.all()
            }
            for cabin in cabins
        ]

        column_details = {
            "id": columns.id if columns else None,
            "seatSize": columns.seatSize if columns else None,
            "seats": columns.seat_set.all() if columns else None
        }

        couch_data.append({
            "id": couch.id,
            "type": couch.type.name,
            "cabinSize": couch.cabinSize,
            "code": couch.code,
            "cabins": cabin_details,
            "column": column_details
        })

    context = {
        "train": train,
        "couches": couch_data
    }
    return render(request, 'reservations/train_detail.html', context)


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def delete_couch(request, couch_id):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    # Fetch the couch object by ID
    couch = get_object_or_404(Couch, id=couch_id)

    # Get the related train
    train = couch.train

    if request.method == 'POST':
        # Perform deletion
        couch.delete()

        # Add a success message
        messages.success(request, f'Couch {
                         couch.code} has been deleted successfully.')

        # Redirect back to the train details page
        return redirect('train_detail', train.id)

    # If the request is GET, render a confirmation page (this part is optional based on your flow)
    return render(request, 'reservations/confirm_delete_couch.html', {'couch': couch, 'is_admin': is_admin, 'is_collector': is_collector, })

# def change_seat_status(request, seat_id, train_id):
#     print("in status update")
#     # Get the seat object by its ID
#     seat = get_object_or_404(Seat, id=seat_id)

#     # Get the current status of the seat
#     current_status = seat.status.status

#     # Define the cycle of statuses: AVL -> RES -> BKL -> AVL
#     status_cycle = ['AVL', 'RES', 'BKL']

#     # Get the next status in the cycle
#     next_status = status_cycle[(status_cycle.index(current_status) + 1) % len(status_cycle)]

#     # Get the corresponding Status object for the next status
#     # new_status = get_object_or_404(Status, status=next_status)
#     new_status = Status.objects.create(status=next_status)

#     print("redirecting")

#     # Update the seat's status
#     seat.status = new_status
#     seat.save()  # Save the seat object with the updated status

#     # Redirect to the train details page
#     return redirect('train_detail', train_id=train_id)


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin', 'collector'])
def change_seat_status(request, seat_id, train_id):
    # Get the seat object by its ID
    seat = get_object_or_404(Seat, id=seat_id)

    # Get the current status of the seat
    current_status = seat.status.status

    # Define the cycle of statuses: AVL -> RES -> BKL -> AVL
    status_cycle = ['AVL', 'RES', 'BKL']

    # Get the next status in the cycle
    next_status = status_cycle[(status_cycle.index(
        current_status) + 1) % len(status_cycle)]

    # Create the new Status object using the next status
    new_status = Status.objects.create(status=next_status)

    # Update the seat's status
    seat.status = new_status
    seat.save()  # Save the seat object with the updated status

    # Add a success message to the Django message framework
    messages.success(request, f"{next_status}")

    # Redirect to the train details page
    return redirect('train_detail', train_id=train_id)


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def add_couch_to_train(request, train_id):
    train = get_object_or_404(Train, id=train_id)
    couch_types = CouchType.objects.all()

    if request.method == 'POST':
        couch_type_id = request.POST.get('type')
        # cabin_size = request.POST.get('cabin_size')

        couch_type = get_object_or_404(CouchType, id=couch_type_id)
        new_couch = Couch(
            train=train,
            type=couch_type,
            # cabinSize=int(cabin_size)
        )
        new_couch.save()

        return redirect('train_detail', train_id=train.id)

    return render(request, 'reservations/add_couch.html', {'train': train, 'couch_types': couch_types})


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin', 'collector'])
def train_list(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    # Fetch all trains
    trains = Train.objects.all()
    return render(request, 'reservations/train_list.html', {'trains': trains, 'is_admin': is_admin, 'is_collector': is_collector})


def book_seat(request, train_id):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    train = Train.objects.get(id=train_id)
    seats = Seat.objects.filter(
        cabin__couch__train=train, status__status="AVL")

    if request.method == "POST":
        seat_id = request.POST.get("seat_id")
        seat = Seat.objects.get(id=seat_id)
        seat.status.status = "RES"  # Mark seat as reserved
        seat.save()
        return redirect("booking_success")

    return render(request, "book_seat.html", {"train": train, "seats": seats, 'is_admin': is_admin, 'is_collector': is_collector, })


@login_required(login_url='login')
def create_train(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    if request.method == 'POST':
        # Get form data
        train_name = request.POST.get('trainName')
        coordinates_x = request.POST.get('coordinatesX')
        coordinates_y = request.POST.get('coordinatesY')

        # Create a Location object
        location = Location.objects.create(
            coordinatesX=coordinates_x,
            coordinatesY=coordinates_y
        )

        # Create a Train object
        Train.objects.create(
            trainName=train_name,
            location=location
        )

        messages.success(request, "Train created successfully!")
        return redirect('train_list')

    return render(request, 'reservations/create_train.html', {'is_admin': is_admin, 'is_collector': is_collector})


def home(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False

    context = {'is_admin': is_admin, 'is_collector': is_collector}
    return render(request, 'reservations/home.html', context)

    # views.py

# i want to have input "seats" which will indicate how many seats a user need and options like "seats" which will indicate the user needs seats in columns or options "Cabin" which will indicate user need seats in cabin , and an option "Berth" which will indicate user need berth also (each berth has two eds , one bed for each seat) ,


def booking_(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False

    # Fetch all cities for the dropdown options
    couchType = calculations.get_all_couch_types()
    cities = calculations.get_cities_all()
    trains = None
    total_payment = 0
    # Default to 1 seat if not provided
    seats = int(request.GET.get('seats', 1))

    if request.method == 'GET':
        source_id = request.GET.get('source')
        destination_id = request.GET.get('destination')
        order = request.GET.get('orderBy')
        # typeCouch = request.GET.get('couchType')
        # print("type couch id is ")
        # print(typeCouch)
        # _type  = CouchType.objects.get(id=typeCouch)
        if source_id and destination_id and order:
            context = calculations.get_all_routes(
                source_id, destination_id, order)

            if context and context.get('shortest_path'):
                route_distance = context['shortest_path']['distance']
                # Assuming it's provided in context
                # couch_price = context['shortest_path']['couch_type_price']
                pprint.pprint(context['shortest_path']['schedules'])
                print("the shortest paths number is ")
                total_payment = 0
                for _ in range(len(context['shortest_path']['schedules'])):
                    print(_)

                # Calculate the total payment
                # total_payment = seats * route_distance * couch_price
                # total_payment = seats * route_distance * _type.price

            context = {
                'couches': couchType,
                'cities': cities,
                'trains': context,
                'total_payment': total_payment,
                'seats': seats,
                'is_admin': is_admin,
                'is_collector': is_collector,
            }
            print("context in booking is ")
            pprint.pprint(context)
            return render(request, 'reservations/booking.html', context)

    return render(request, 'reservations/booking.html', {
        'couches': couchType,
        'cities': cities,
        'trains': trains,
        'total_payment': total_payment,
        'seats': seats,
        'is_admin': is_admin,
        'is_collector': is_collector
    })


def booking(request):
    # Check if user is authenticated

    # Get user groups
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False

    # Fetch all cities for the dropdown options
    cities = calculations.get_cities_all()
    trains = None
    couchType = calculations.get_all_couch_types()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            # Redirect to login page with the next parameter to preserve the current URL
            return redirect(f'{reverse("login")}?next={request.path}')
        source_id = request.POST.get('source')
        destination_id = request.POST.get('destination')
        order = request.POST.get('orderBy')

        seats = int(request.POST.get('seats', 1))
        beds = int(request.POST.get('beds', 1))
        typeCouch = request.POST.get('couchType')
        _type = CouchType.objects.get(id=typeCouch)

        # Debugging prints
        print(f"Source ID: {source_id}, Destination ID: {
              destination_id}, Beds: {beds}")

        if source_id and destination_id and order:
            # Fetch the source and destination cities based on the IDs
            string = f"{Station.objects.filter(city__id=source_id).first().city.name} → {
                Station.objects.filter(city__id=destination_id).first().city.name}"
            context = calculations.get_all_routes(
                source_id, destination_id, order, int(beds))
            route_distance = context['shortest_path']['distance']
            total_payment = seats * route_distance * _type.price

            context['shortest_path']['price'] = context['shortest_path']['distance'] * \
                seats * _type.price

            stations_with_cities = {
                station.id: {
                    'station': station,
                    'city': station.city.name
                }
                for station in Station.objects.all()
            }
            # Calculating price for all paths
            for paths in context['all_paths']:
                paths['price'] = paths['distance'] * seats * _type.price

            # Return to the booking page with the context
            return render(request, 'reservations/booking.html', {
                'couchTypeId': typeCouch,
                'seats': seats,
                'beds': beds,
                'couches': couchType,
                'string': string,
                'total_payment': total_payment,
                'cities': cities,
                'trains': context,
                'is_admin': is_admin,
                'is_collector': is_collector,
                'stations_with_cities': stations_with_cities,
            })

    # Default page rendering when not POST or user is authenticated
    return render(request, 'reservations/booking.html', {
        'couches': couchType,
        'cities': cities,
        'trains': trains,
        'is_admin': is_admin,
        'is_collector': is_collector
    })


def secondary___booking(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    # Fetch all cities for the dropdown options
    cities = calculations.get_cities_all()
    trains = None
    couchType = calculations.get_all_couch_types()
    # Check if 'source' and 'destination' exist in GET request parameters
    if request.method == 'POST':
        source_id = request.POST.get('source')
        destination_id = request.POST.get('destination')
        order = request.POST.get('orderBy')

        seats = int(request.POST.get('seats', 1))
        typeCouch = request.POST.get('couchType')
        print("type couch id is ")
        print(typeCouch)
        _type = CouchType.objects.get(id=typeCouch)
        # Debugging prints
        print(f"Source ID: {source_id}, Destination ID: {destination_id}")

        if source_id and destination_id and order:
            # Fetch the source and destination cities based on the IDs
            # trains = calculations.get_all_routes(source_id, destination_id)

            # Debugging output for the routes
            print(f"source {source_id} and destination {destination_id}")
            string = f"{Station.objects.filter(city__id=source_id).first().city.name} →   {
                Station.objects.filter(city__id=destination_id).first().city.name}"
            context = calculations.get_all_routes(
                source_id, destination_id, order)
            route_distance = context['shortest_path']['distance']
            total_payment = seats * route_distance * _type.price
            # calculating price for shortest path

            context['shortest_path']['price'] = context['shortest_path']['distance'] * \
                seats*_type.price

            # calculating price for all paths
            for paths in context['all_paths']:
                paths['price'] = paths['distance']*seats*_type.price
            print("context is -----------------------")
            pprint.pprint(context)

            stations_with_cities = {
                station.id: {
                    'station': station,
                    'city': station.city.name
                }
                for station in Station.objects.all()
            }
            print("stations are")
            print(stations_with_cities)

            return render(request, 'reservations/booking.html', {
                'couches': couchType,
                'string': string,
                'total_payment': total_payment,
                'cities': cities,
                'trains': context,
                'is_admin': is_admin,
                'is_collector': is_collector,
                'stations_with_cities': stations_with_cities,
            })

    # Render the booking page with cities and any available trains

    return render(request, 'reservations/booking.html', {
        'couches': couchType,
        'cities': cities,
        'trains': trains,
        'is_admin': is_admin, 'is_collector': is_collector
    })


# def vbooking(request):
#     cities = calculations.get_cities_all()
#     # cities = City.objects.all()
#     trains = None  # Default to None
#     if request.method == 'GET' and 'source' in request.GET and 'destination' in request.GET:
#         print("get")
#         source_id = request.GET.get('source')

#         destination_id = request.GET.get('destination')

#         # If cities are selected, filter the available routes, etc.
#         if source_id and destination_id:
#             print(source_id)
#             print(destination_id)
#             # Add logic here to find the routes between these cities
#             # Example: routes = get_routes_for_cities(source_city, destination_city)
#         else:
#             source_city = None
#             destination_city = None
#         calculations.get_all_routes(source_id, destination_id)

#         # if source_id and destination_id:
#         #     # Fetch trains matching source and destination
#         #     trains = Train.objects.filter(source_id=source_id, destination_id=destination_id)

#     return render(request, 'reservations/booking.html', {'cities': cities, 'trains': trains})
#     # return render(request, 'reservations/booking.html', {})


def about(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    context = {'is_admin': is_admin, 'is_collector': is_collector}
    return render(request, 'reservations/about.html', context)


def contact(request):

    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False

    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Send email (for demo purposes, use your actual email configurations)
        send_mail(
            f'Contact from {name}',
            message,
            email,
            [settings.DEFAULT_FROM_EMAIL],
            fail_silently=False,
        )

        messages.success(request, "Your message has been sent successfully!")
        return redirect('contact')

    return render(request, 'reservations/contact.html', {'is_admin': is_admin, 'is_collector': is_collector})

# @login_required
# def seat_selection(request, schedule_id):
#     schedule = Schedule.objects.get(id=schedule_id)
#     available_seats = Seat.objects.filter(
#         cabin__couch__train=schedule.train, status__status="AVL"
#     )

#     if request.method == "POST":
#         selected_seats = request.POST.getlist('seats')
#         for seat_id in selected_seats:
#             seat = Seat.objects.get(id=seat_id)
#             # Mark seat as booked and create a UserBooking
#             seat.status.status = "BKL"
#             seat.status.save()
#             UserBooking.objects.create(
#                 user=request.user, seat=seat, schedule=schedule)
#         return JsonResponse({'message': "Seats booked successfully!"})

#     return render(request, 'seat_selection.html', {
#         'schedule': schedule,
#         'available_seats': available_seats
#     })


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def seat_selection(request, schedule_id):
    schedule = Schedule.objects.get(id=schedule_id)
    available_seats = Seat.objects.filter(
        cabin__couch__train=schedule.train, status__status="AVL"
    )

    if request.method == "POST":
        selected_seats = request.POST.getlist('seats')

        try:
            with transaction.atomic():
                for seat_id in selected_seats:
                    seat = Seat.objects.select_for_update().get(id=seat_id)
                    if seat.status.status != "AVL":
                        return JsonResponse({'error': f"Seat {seat.seatNumber} is no longer available."}, status=400)
                    # Book seat
                    seat.status.status = "BKL"
                    seat.status.save()
                    UserBooking.objects.create(
                        user=request.user, seat=seat, schedule=schedule)
            return JsonResponse({'message': "Seats booked successfully!"})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'seat_selection.html', {
        'schedule': schedule,
        'available_seats': available_seats
    })


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def create_schedule(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('schedule_list')
    else:
        form = ScheduleForm()

    return render(request, 'reservations/create_schedule.html', {'form': form, 'is_admin': is_admin, 'is_collector': is_collector})

# Create Station View


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def create_station(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False

    if request.method == 'POST':
        # Instantiate both the StationForm and the LocationForm
        location_form = LocationForm(request.POST)
        station_form = StationForm(request.POST)

        if location_form.is_valid() and station_form.is_valid():
            # Save the Location form first
            location = location_form.save()

            # Save the Station form with the new Location
            station = station_form.save(commit=False)
            station.location = location
            station.save()

            # Redirect to the station list or any other success page
            # Or any other URL you want after saving
            return redirect('station_list')

    else:
        # If GET request, instantiate empty forms
        location_form = LocationForm()
        station_form = StationForm()

    return render(request, 'reservations/create_station.html', {
        'station_form': station_form,
        'location_form': location_form,
        'is_admin': is_admin,
        'is_collector': is_collector
    })


# Create Route View


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def create_route(request):
    is_admin = request.user.groups.filter(
        name='admin').exists() if request.user.is_authenticated else False
    is_collector = request.user.groups.filter(
        name='collector').exists() if request.user.is_authenticated else False
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('route_list')
    else:
        form = RouteForm()

    return render(request, 'reservations/create_route.html', {'form': form, 'is_admin': is_admin, 'is_collector': is_collector, })


class ScheduleListView(ListView):
    model = Schedule
    template_name = 'reservations/schedule_list.html'
    context_object_name = 'schedules'

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated and belongs to the 'admin' group
        if not request.user.is_authenticated or not request.user.groups.filter(name='admin').exists():
            # You can redirect to another page or return a forbidden response
            return HttpResponseForbidden("You do not have permission to access this page.")
            # OR redirect
            # return redirect('some_other_page')

        # If the user is admin, proceed to the normal view
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if the user is authenticated and if they belong to the 'admin' group
        is_admin = self.request.user.groups.filter(
            name='admin').exists() if self.request.user.is_authenticated else False
        is_collector = self.request.user.groups.filter(
            name='collector').exists() if self.request.user.is_authenticated else False

        # Add the is_admin value to the context
        context['is_admin'] = is_admin
        context['is_collector'] = is_collector

        return context

# Edit Schedule


class ScheduleUpdateView(UpdateView):
    model = Schedule
    fields = ['train', 'route', 'arrivalTime', 'departureTime']
    template_name = 'reservations/schedule_form.html'
    context_object_name = 'schedule'

    def get_success_url(self):
        return reverse_lazy('schedule_list')

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated and belongs to the 'admin' group
        if not request.user.is_authenticated or not request.user.groups.filter(name='admin').exists():
            # You can redirect to another page or return a forbidden response
            return HttpResponseForbidden("You do not have permission to access this page.")
            # OR redirect
            # return redirect('some_other_page')

        # If the user is admin, proceed to the normal view
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if the user is authenticated and if they belong to the 'admin' group
        is_admin = self.request.user.groups.filter(
            name='admin').exists() if self.request.user.is_authenticated else False
        is_collector = self.request.user.groups.filter(
            name='collector').exists() if self.request.user.is_authenticated else False

        # Add the is_admin value to the context
        context['is_admin'] = is_admin
        context['is_collector'] = is_collector

        return context
# Delete Schedule


class ScheduleDeleteView(DeleteView):
    model = Schedule
    template_name = 'reservations/schedule_confirm_delete.html'
    context_object_name = 'schedule'

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated and belongs to the 'admin' group
        if not request.user.is_authenticated or not request.user.groups.filter(name='admin').exists():
            # You can redirect to another page or return a forbidden response
            return HttpResponseForbidden("You do not have permission to access this page.")
            # OR redirect
            # return redirect('some_other_page')

        # If the user is admin, proceed to the normal view
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('schedule_list')


class StationListView(ListView):
    model = Station
    template_name = 'reservations/station_list.html'
    context_object_name = 'stations'

    def get_queryset(self):
        return Station.objects.select_related('city', 'location')

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated and belongs to the 'admin' group
        if not request.user.is_authenticated or not request.user.groups.filter(name='admin').exists():
            # You can redirect to another page or return a forbidden response
            return HttpResponseForbidden("You do not have permission to access this page.")
            # OR redirect
            # return redirect('some_other_page')

        # If the user is admin, proceed to the normal view
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if the user is authenticated and if they belong to the 'admin' group
        is_admin = self.request.user.groups.filter(
            name='admin').exists() if self.request.user.is_authenticated else False
        is_collector = self.request.user.groups.filter(
            name='collector').exists() if self.request.user.is_authenticated else False

        # Add the is_admin value to the context
        context['is_admin'] = is_admin
        context['is_collector'] = is_collector

        return context


class StationUpdateView(UpdateView):
    model = Station
    fields = ['stationName', 'city']
    template_name = 'reservations/station_form.html'
    context_object_name = 'station'

    def get_success_url(self):
        # Redirect to the station list after successful update
        return reverse_lazy('station_list')

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated and belongs to the 'admin' group
        if not request.user.is_authenticated or not request.user.groups.filter(name='admin').exists():
            return HttpResponseForbidden("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # Save the form data and handle any post-save logic
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if the user is authenticated and if they belong to the 'admin' group
        is_admin = self.request.user.groups.filter(
            name='admin').exists() if self.request.user.is_authenticated else False
        is_collector = self.request.user.groups.filter(
            name='collector').exists() if self.request.user.is_authenticated else False

        # Add the is_admin value to the context
        context['is_admin'] = is_admin
        context['is_collector'] = is_collector

        return context

# Delete Station


# @allowed_users(allowed_roles=['admin'])
class StationDeleteView(DeleteView):
    model = Station
    template_name = 'reservations/station_confirm_delete.html'
    context_object_name = 'reservations/station'

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated and belongs to the 'admin' group
        if not request.user.is_authenticated or not request.user.groups.filter(name='admin').exists():
            # You can redirect to another page or return a forbidden response
            return HttpResponseForbidden("You do not have permission to access this page.")
            # OR redirect
            # return redirect('some_other_page')

        # If the user is admin, proceed to the normal view
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('station_list')


# @allowed_users(allowed_roles=['admin'])
class RouteListView(ListView):
    model = Route
    template_name = 'reservations/route_list.html'
    context_object_name = 'routes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add custom context variables here
        context['custom_message'] = 'Welcome to the Station List Page!'
        context['additional_data'] = 'Some extra information'
        return context

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated and belongs to the 'admin' group
        if not request.user.is_authenticated or not request.user.groups.filter(name='admin').exists():
            # You can redirect to another page or return a forbidden response
            return HttpResponseForbidden("You do not have permission to access this page.")
            # OR redirect
            # return redirect('some_other_page')

        # If the user is admin, proceed to the normal view
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if the user is authenticated and if they belong to the 'admin' group
        is_admin = self.request.user.groups.filter(
            name='admin').exists() if self.request.user.is_authenticated else False

        is_collector = self.request.user.groups.filter(
            name='collector').exists() if self.request.user.is_authenticated else False
        # Add the is_admin value to the context
        context['is_admin'] = is_admin
        context['is_collector'] = is_collector

        return context


# @allowed_users(allowed_roles=['admin'])
class RouteUpdateView(UpdateView):
    model = Route
    fields = ['sourceStation', 'destinationStation', 'distanceToDestination']
    template_name = 'reservations/route_form.html'
    context_object_name = 'route'

    def get_success_url(self):
        return reverse_lazy('route_list')

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated and belongs to the 'admin' group
        if not request.user.is_authenticated or not request.user.groups.filter(name='admin').exists():
            # You can redirect to another page or return a forbidden response
            return HttpResponseForbidden("You do not have permission to access this page.")
            # OR redirect
            # return redirect('some_other_page')

        # If the user is admin, proceed to the normal view
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if the user is authenticated and if they belong to the 'admin' group
        is_admin = self.request.user.groups.filter(
            name='admin').exists() if self.request.user.is_authenticated else False

        is_collector = self.request.user.groups.filter(
            name='collector').exists() if self.request.user.is_authenticated else False
        # Add the is_admin value to the context
        context['is_admin'] = is_admin
        context['is_collector'] = is_collector

        return context
# Delete Route


# @allowed_users(allowed_roles=['admin'])
class RouteDeleteView(DeleteView):
    model = Route
    template_name = 'reservations/route_confirm_delete.html'
    context_object_name = 'route'

    def dispatch(self, request, *args, **kwargs):
        # Check if the user is authenticated and belongs to the 'admin' group
        if not request.user.is_authenticated or not request.user.groups.filter(name='admin').exists():
            # You can redirect to another page or return a forbidden response
            return HttpResponseForbidden("You do not have permission to access this page.")

        # If the user is admin, proceed to the normal view
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # The post method is called when the form is submitted. We override this to
        # automatically redirect the user after deleting the object.
        self.object = self.get_object()  # Get the object that will be deleted
        self.object.delete()  # Delete the object

        # Redirect to the success URL
        return redirect(self.get_success_url())

    def get_success_url(self):
        # Redirect to the route_list page after deletion
        return reverse_lazy('route_list')


@login_required(login_url='login')
@allowed_users(allowed_roles=['admin'])
def delete_train(request, train_id):
    # Check if the user is an admin
    if not request.user.groups.filter(name='admin').exists():
        messages.error(request, "You are not authorized to delete a train.")
        return redirect('train_list')  # Redirect to train list if not admin

    # Get the train object or 404 if not found
    train = get_object_or_404(Train, id=train_id)

    # Delete the train
    train.delete()

    # Show a success message
    messages.success(request, "Train deleted successfully.")

    return redirect('train_list')  # Redirect back to the train list


def change_berth_status(request, berth_id):
    # Fetch the berth by its ID
    berth = get_object_or_404(Berth, pk=berth_id)

    # Ensure that the user has proper permissions (you can adjust this as needed)
    if not request.user.groups.filter(name='admin').exists() and not request.user.is_authenticated:
        raise Http404("You are not authorized to change the berth status.")

    # Define the status transitions for the beds
    status_transitions = ['AVL', 'RES', 'BKL']

    # Loop through the beds in this berth and change their statuses
    beds = Bed.objects.filter(berth=berth)  # Get all the beds in this berth

    for bed in beds:
        current_status = bed.status.status  # Get the current status of the bed

        # Transition the status based on the current status
        if current_status == 'AVL':
            new_status = 'RES'
        elif current_status == 'RES':
            new_status = 'BKL'
        else:
            new_status = 'AVL'

        # Update the bed's status
        bed.status.status = new_status
        bed.status.save()

    # Redirect to the train details or wherever appropriate
    return redirect('train_detail', train_id=berth.cabin.couch.train.id)


def change_bed_status(request, bed_id):
    # Fetch the Bed by its ID
    bed = get_object_or_404(Bed, pk=bed_id)

    # Ensure that the user has the appropriate permissions
    if not request.user.groups.filter(name='admin').exists() and not request.user.is_authenticated:
        raise Http404("You are not authorized to change the bed status.")

    # Define possible status transitions
    status_transitions = ['AVL', 'RES', 'BKL']

    # Get the current status of the bed
    current_status = bed.status.status

    # Determine the next status based on the current status
    if current_status == 'AVL':
        new_status = 'RES'
    elif current_status == 'RES':
        new_status = 'BKL'
    else:
        new_status = 'AVL'

    # Update the bed's status
    bed.status.status = new_status
    bed.status.save()

    # Redirect to a page showing the Berth or Cabin details
    return redirect('train_detail', bed.berth.cabin.couch.train.id)


def book_seat(request, schedule_id, seat_id):
    if request.method == 'POST':
        user = request.user
        schedule = get_object_or_404(Schedule, id=schedule_id)
        seat = get_object_or_404(Seat, id=seat_id)

        # Ensure the seat is not already booked
        if UserBooking.objects.filter(seat=seat, schedule=schedule).exists():
            return JsonResponse({'error': 'Seat already booked'}, status=400)

        # Create the booking
        booking = UserBooking.objects.create(
            user=user, seat=seat, schedule=schedule)

        return JsonResponse({
            'message': 'Booking successful',
            'total_cost': booking.bill.total_amount,
            'booking_id': booking.id,
        })


def process_payment(request, booking_id):
    booking = get_object_or_404(UserBooking, id=booking_id)
    bill = booking.bill

    # Call to the payment gateway here and confirm payment
    payment_success = True  # Assume success for this example

    if payment_success:
        bill.mark_as_paid()
        booking.status = 'BOOKED'
        booking.save()
        return JsonResponse({'message': 'Payment successful'})
    else:
        return JsonResponse({'error': 'Payment failed'}, status=400)


# def create_bill(request):
#     if request.method == 'POST':
#         user = request.user  # Assuming the user is authenticated

#         # Retrieve all unbilled UserBooking instances
#         unbilled_bookings = UserBooking.objects.filter(
#             user=user, bill__isnull=True)

#         if not unbilled_bookings.exists():
#             return JsonResponse({'error': 'No unbilled bookings found'}, status=400)

#         # Calculate the total cost
#         total_cost = sum(booking.cost for booking in unbilled_bookings)

#         # Create a new bill
#         with transaction.atomic():  # Ensure atomic operation
#             bill = Bill.objects.create(user=user, total_amount=total_cost)

#             # Associate the bill with the unbilled bookings
#             unbilled_bookings.update(bill=bill)

#         return JsonResponse({
#             'message': 'Bill created successfully',
#             'bill_id': bill.id,
#             'total_amount': bill.total_amount
#         })


def reserve_seat(request):
    # Get the items as a JSON string
    items = request.POST.get('items')
    print('reserving seats')
    if items:
        # Parse the JSON string into a Python list
        item_list = json.loads(items)
        print(item_list)  # This will show the list of schedule IDs

        # Iterate over each schedule ID and reserve seats
        for item in item_list['sch']:
            s = Schedule.objects.get(id=item)
            # Assuming you pass 'seats' and 'cost' along with user
            reserved_seats = s.reserve_seats(
                item_list['seats'], request.user, item_list['couchTypeId'])
            reserved_beds = s.reserve_beds(
                item_list['beds'], request.user, item_list['couchTypeId'])
            # Adding a success message
            if reserved_seats:
                messages.success(request, f"Successfully reserved {
                                 reserved_seats} seats for schedule {item}")
            else:
                messages.error(
                    request, f"Failed to reserve seats for schedule {item}")

        # Perform any additional logic here (like confirming payment or other actions)
    else:
        messages.error(request, "No items received.")

    # Redirect to home after reservation
    return redirect('home')


# def reserve_seat(request):
#     # Get the items as a JSON string
#     items = request.POST.get('items')
#     print(f"Received items: {items}")  # This will help you see what is being passed

#     if items:
#         item_list = json.loads(items)
#         print(f"Parsed items: {item_list}")  # This will show the parsed data

#         # Process the data
#         for item in item_list['sch']:
#             try:
#                 s = Schedule.objects.get(id=item)
#                 reserved_seats = s.reserve_seats(
#                     item_list['seats'], request.user, item_list['cost']
#                 )
#                 if reserved_seats:
#                     messages.success(
#                         request,
#                         f"Successfully reserved {reserved_seats} seats for schedule {item}.",
#                     )
#                 else:
#                     messages.error(
#                         request, f"Failed to reserve seats for schedule {item}."
#                     )
#             except Schedule.DoesNotExist:
#                 messages.error(request, f"Schedule {item} does not exist.")
#     else:
#         messages.error(request, "No items received.")

#     return redirect("booking")


@login_required
def create_bill(request):
    user = request.user

    bil = Bill.objects.filter(user=user, is_paid=False).count()
    print("the numberof bills of this user are ", bil)
    if bil == 0:
        presentBill = Bill.objects.create(user=user)
    else:
        presentBill = Bill.objects.filter(user=user, is_paid=False).first()
    unbilledBookings = UserBooking.objects.filter(user=user, bill__isnull=True)
    print("unbilled bookings")
    print(unbilledBookings)
    if unbilledBookings.exists():
        for booking in unbilledBookings:
            booking.bill = presentBill
            booking.save()
        # presentBill.total_amount += sum(
        #     booking.cost for booking in unbilledBookings)
    allBookings = UserBooking.objects.filter(user=user, status="PENDING")

    ammount = 0
    for booking in allBookings:
        ammount += booking.cost
    presentBill.total_amount = ammount
    presentBill.save()
    return render(request, 'reservations/bill_summary.html', {'bill': presentBill, 'bookings': allBookings})
    # else:
    #     # Redirect to a page or display a message indicating no unpaid bookings
    #     return redirect("booking")


@login_required
def checkout_bill(request, bill_id):
    bill = get_object_or_404(Bill, id=bill_id, user=request.user)

    if request.method == "POST":
        print("the bill id is ")
        print(bill_id)
        bill.mark_as_paid()
        # Send confirmation email after the user checks out
        subject = f"Bill Payment Confirmation - Bill ID: {bill.id}"
        message = f"""
        Hello {request.user.username},

        Thank you for your payment! Your bill has been successfully processed.

        Bill ID: {bill.id}
        Total Amount: Rs {bill.total_amount}
        Date of Payment: {bill.created_at}

        We appreciate your business!

        Regards,
        Ahmad and Najum 
        """

        # Send the email
        send_mail(
            subject,
            message,
            # The "from" email (your email address)
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],  # The recipient email (user's email address)
            fail_silently=False
        )

        # Optionally, you can mark the bill as paid here
        # bill.status = 'PAYED'  # Assuming you have a "status" field in the Bill model
        # bill.save()

        # Redirect to a confirmation page or show a success message
        return render(request, 'reservations/home.html', {'bill': bill})

    else:
        # Return a 405 Method Not Allowed response for non-POST requests
        return render(request, 'reservations/payment_success.html', {'bill': bill})


@login_required
def checkout___bill(request, bill_id):
    bill = get_object_or_404(bill, id=bill_id, user=request.user)
    if request.method == "post":
        print("the bill id is ")
        print(bill_id)
        # # retrieve the bill object

        # # mark the bill as paid
        # bill.mark_as_paid()

        # redirect to a confirmation page or show a success message
        return render(request, 'reservations/home.html', {'bill': bill})
    else:
        # return a 405 method not allowed response for non-post requests
        return render(request, 'reservations/payment_success.html', {'bill': bill})

# @login_required
# def create_bill(request):
#     user = request.user

#     bil = Bill.objects.filter(user=user, is_paid=False).count()
#     print("the numberof bills of this user are ",bil)
#     if bil == 0:
#         presentBill = Bill.objects.create(user=user)
#     else:
#         presentBill = Bill.objects.filter(user=user, is_paid=False).first()
#     unbilledBookings = UserBooking.objects.filter(user=user, bill__isnull=True)
#     print("unbilled bookings")
#     print(unbilledBookings)
#     if unbilledBookings.exists():
#         for booking in unbilledBookings:
#             booking.bill = presentBill
#             booking.save()
#         presentBill.total_amount += sum(
#             booking.cost for booking in unbilledBookings)
#     allBookings = UserBooking.objects.filter(user = user , bill__is_paid = False)
#     return render(request, 'reservations/bill_summary.html', {'bill': presentBill, 'bookings': allBookings})
#     # else:
#     #     # Redirect to a page or display a message indicating no unpaid bookings
#     #     return redirect("booking")


# @login_required
# def checkout_bill(request, bill_id):
#     if request.method == "POST":
#         # Retrieve the bill object
#         bill = get_object_or_404(Bill, id=bill_id, user=request.user)

#         # Mark the bill as paid
#         bill.mark_as_paid()

#         # Redirect to a confirmation page or show a success message
#         return render(request, 'reservations/payment_success.html', {'bill': bill})
#     else:
#         # Return a 405 Method Not Allowed response for non-POST requests
#         return JsonResponse({'error': 'Invalid request method.'}, status=405)
@login_required
def profile_view(request):
    user = request.user
    user_bookings = UserBooking.objects.filter(user=user)

    # Separate bookings into pending and paid
    pending_bookings = user_bookings.filter(status='PENDING')
    paid_bookings = user_bookings.filter(status='PAYED')

    context = {
        'user': user,
        'pending_bookings': pending_bookings,
        'paid_bookings': paid_bookings,
    }
    return render(request, 'reservations/profile.html', context)
