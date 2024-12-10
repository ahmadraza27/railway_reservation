from django.db import models
from datetime import timedelta
from django.utils.timezone import now
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
# from django.contrib.gis.db import models


class Location(models.Model):
    coordinatesX = models.DecimalField(
        "The X Coordinate", decimal_places=2, max_digits=10, null=False)
    coordinatesY = models.DecimalField(
        "The Y Cordinate", decimal_places=2, max_digits=10, null=False)
    lastUpdated = models.DateTimeField("Last Updated", auto_now=True)

    def __str__(self):
        return f"Location {self.id} - {self.coordinatesX} , {self.coordinatesY}"


class Train(models.Model):
    trainName = models.CharField(max_length=100)
    # location = models.ForeignKey(Location, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    father = models.BooleanField(null=True, default=True)

    def __str__(self):
        return self.trainName


class City(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class Station(models.Model):
    stationName = models.CharField(max_length=100, null=False)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    # city = models.CharField(max_length=30, null=False)
    location = models.OneToOneField(Location, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.id} - {self.stationName} ({self.city})"


class Route(models.Model):
    sourceStation = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="soureceStation_set")
    destinationStation = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="destinationStation_set")
    distanceToDestination = models.IntegerField(null=False)

    def __str__(self):
        return f"Source {self.sourceStation} ,Destination {self.destinationStation}"


class secondary_Schedule(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    # station = models.ForeignKey(Station, on_delete=models.CASCADE)
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    arrivalTime = models.TimeField()
    departureTime = models.TimeField()

    def __str__(self):
        return f"the train {self.train.trainName} will follow route {self.route} "

# Add this method to the Schedule model


class Schedule(models.Model):
    train = models.ForeignKey(
        Train, on_delete=models.CASCADE, related_name="train")
    copyTrain = models.OneToOneField(
        Train, on_delete=models.CASCADE, null=True, related_name="copyTrain")
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    arrivalTime = models.TimeField()
    departureTime = models.TimeField()

    def __str__(self):
        return f"Will Arrive At  {self.route.sourceStation.stationName} On {self.arrivalTime} And Will Leave For {self.route.destinationStation.stationName} On Time {self.departureTime}"

    def save(self, *args, **kwargs):
        """Override save to ensure payment is calculated and associated with a bill."""
        self.copyTrain = Train.objects.create(
            trainName=self.train.trainName, location=self.train.location, father=False)
        self.copyTrain.save()
        print("saving the copy train")
        couches = Couch.objects.filter(train=self.train)
        for couch in couches:
            tp = couch.type
            c = Couch.objects.create(train=self.copyTrain, type=tp)
            c.save()
        super().save(*args, **kwargs)  # Call the base class save method
        print("schedule created")

    def check_and_reset_seats(self):
        """
        Check and reset seat statuses if they are still reserved an hour before arrival.
        """
        # Calculate one hour before arrival time
        arrival_datetime = now().replace(hour=self.arrivalTime.hour,
                                         minute=self.arrivalTime.minute, second=0)
        if now() >= arrival_datetime - timedelta(hours=1):
            print("Checking seat statuses for reset...")

            # Iterate through all couches and reset seat status if needed
            for couch in self.copyTrain.couch_set.all():
                for cabin in couch.cabin_set.all():
                    for seat in cabin.seat_set.filter(status__status='RESERVED'):
                        bookings = UserBooking.objects.filter(seat=seat)
                        for booking in bookings:
                            booking.delete()
                        # Logic to reset seat status to 'AVL' (Available)
                        seat.status.status = 'AVL'
                        seat.status.save()
                        print(f"Seat {seat.id} reset to available.")

    def reserve_seats(self, seat_count: int, user: User, couchTypeId: int):
        """
        Reserves the given number of seats in this schedule's train for the provided user.
        """
        reserved_seats = 0

        # Iterate through all couches of the train and reserve seats
        for couch in self.copyTrain.couch_set.all():
            if reserved_seats >= int(seat_count):
                break  # Stop once we have reserved enough seats

            for cabin in Cabin.objects.filter(couch__type__id =couchTypeId):
                if reserved_seats >= int(seat_count):
                    break

                for seat in cabin.seat_set.filter(status__status='AVL'):
                    # Create a booking for the user
                    user_booking = UserBooking.objects.create(
                        user=user,
                        seat=seat,
                        bed=None,  # You can add logic to select a berth if necessary
                        schedule=self,
                        status='PENDING',  # Set initial status as 'PENDING'
                    )
                    user_booking.save()
                    # Update seat status
                    # seat.status.status = 'RESERVED'
                    # seat.status.save()

                    reserved_seats += 1
                    if reserved_seats >= seat_count:
                        break  # Stop once we have reserved enough seats


        return reserved_seats

    def reserve_beds(self,beds:int ,user: User ,couchTypeId : int):
        """
        Reserves the given number of seats in this schedule's train for the provided user.
        """
        reserved_beds = 0

        # Iterate through all couches of the train and reserve seats
        for couch in self.copyTrain.couch_set.all():
            if reserved_beds >= int(beds):
                break  # Stop once we have reserved enough seats

            for cabin in couch.cabin_set.all():
                if reserved_beds >= int(beds):
                    break

                for bed in Bed.objects.filter(berth__cabin__couch__type__id = couchTypeId):
                    # Create a booking for the user
                    user_booking = UserBooking.objects.create(
                        user=user,
                        seat=None,
                        bed=bed,  # You can add logic to select a berth if necessary
                        schedule=self,
                        status='PENDING',  # Set initial status as 'PENDING'
                    )
                    user_booking.save()
                    # Update seat status
                    # seat.status.status = 'RESERVED'
                    # seat.status.save()

                    reserved_beds += 1
                    if reserved_beds >= beds:
                        break  # Stop once we have reserved enough seats

            if reserved_beds >= beds:
                break  # If enough seats have been reserved, exit loop

        return reserved_beds


class CouchType(models.Model):
    seatCapacity = models.IntegerField(null=False)
    seatPrice = models.IntegerField(null=False)
    name = models.CharField(max_length=10)
    price = models.IntegerField()

    def __str__(self):
        return f"{self.name} price is {self.price}"


class Couch(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    code = models.CharField(null=True, editable=False, max_length=5)
    type = models.ForeignKey(CouchType, on_delete=models.CASCADE)
    cabinSize = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        # If it's a new couch, assign couchCode based on the train's current couches
        if not self.pk:  # Only calculate on creation
            self.cabinSize = 8
            existing_couches = Couch.objects.filter(train=self.train).count()
            self.code = existing_couches + 1  # Increment for new couch
        super().save(*args, **kwargs)  # Call the base class save method

    def __str__(self):
        return f"couch {self.code} in train {self.train.trainName}"


class Cabin(models.Model):
    couch = models.ForeignKey(Couch, on_delete=models.CASCADE)
    seatSize = models.IntegerField(null=True)
    open = models.BooleanField(null=False)
    code = models.CharField(max_length=1, null=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only calculate on creation
            self.seatSize = 4
            existing_cabins = Cabin.objects.filter(couch=self.couch).count()
            self.code = chr(66 + existing_cabins)  # Increment for new couch
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cabin {self.code} in {self.couch.code}"


@receiver(post_save, sender=Couch)
def create_cabins(sender, instance, created, **kwargs):
    """Creates cabins based on the cabinSize for this couch"""
    if created:  # Only trigger the cabin creation when the couch is created
        print("CREATING CABINS")
        # Create the required number of cabins based on the cabinSize of the couch
        for i in range(instance.cabinSize):
            Cabin.objects.create(couch=instance, seatSize=8, open=True)


class Column(models.Model):
    couch = models.OneToOneField(Couch, on_delete=models.CASCADE)
    seatSize = models.IntegerField(null=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"column A  in {self.couch.code}"


@receiver(post_save, sender=Couch)
def create_column(sender, instance, created, **kwanrgs):
    """Creates cabins based on the cabinSize for this train"""
    print("CREATING Column")
    if (created):
        Column.objects.create(couch=instance, seatSize=16)


# this is mian status class
class Status(models.Model):
    STATUS_CHOICES = [
        ('AVL', 'Available'),
        ('RES', 'Reserved'),
        ('BKL', 'Booked'),
    ]
    status = models.CharField(
        max_length=3, choices=STATUS_CHOICES, default='AVL')

    def __str__(self):
        return self.get_status_display()


class Berth(models.Model):
    cabin = models.OneToOneField(Cabin, on_delete=models.CASCADE)
    code = models.CharField(max_length=10, null=True)
    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     for i in range(2):
    #         status = Status.objects.create()
    #         Bed.objects.create(berth=self, status=status)

    def __str__(self):
        return f"berth A  in {self.cabin.code}"


@receiver(post_save, sender=Cabin)
def on_create_cabin(sender, instance, created, **kwanrgs):
    """Creates cabins based on the cabinSize for this train"""
    print("CREATING BIRTH")
    if (created):
        strng = f" BED "
        Berth.objects.create(cabin=instance, code=strng)


class Bed(models.Model):
    berth = models.ForeignKey(Berth, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    bedNumber = models.IntegerField(null=True)

    def save(self, *args, **kwargs):

        existing_bed = Bed.objects.filter(berth=self.berth).count()
        self.bedNumber = existing_bed+1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.berth.cabin.couch.train.trainName} - {self.berth.cabin.couch.code} - {self.berth.cabin.code} - BED - {self.bedNumber}"


@receiver(post_save, sender=Berth)
def on_create_berth(sender, instance, created, **kwanrgs):
    """Creates cabins based on the cabinSize for this train"""
    print("CREATING BED")
    if (created):
        for i in range(2):
            st = Status.objects.create()
            Bed.objects.create(berth=instance, status=st, bedNumber=i)


class Seat(models.Model):
    cabin = models.ForeignKey(
        Cabin, on_delete=models.CASCADE, null=True, blank=True)
    column = models.ForeignKey(
        Column, on_delete=models.CASCADE, null=True, blank=True)
    seatNumber = models.IntegerField(null=True)
    # Default to True since it's in a cabin by default
    inACabin = models.BooleanField(null=False, default=True)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Ensure that only one of cabin or column is set (not both)
        if self.cabin and self.column:
            raise ValueError(
                "A seat cannot be associated with both a cabin and a column.")

        # If it's a new seat, calculate the seatNumber automatically
        if not self.pk:  # Only calculate on creation
            if self.cabin:
                existing_seats = Seat.objects.filter(cabin=self.cabin).count()
            elif self.column:
                existing_seats = Seat.objects.filter(
                    column=self.column).count()
            else:
                existing_seats = 0
            self.seatNumber = existing_seats + 1  # Seat number starts from 1

        super().save(*args, **kwargs)  # Call the base class save method

    def __str__(self):
        if self.cabin:
            return f"{self.cabin.couch.train.trainName} - {self.cabin.couch.code} - {self.cabin.code} - {self.seatNumber}"
        elif self.column:
            return f"Seat {self.seatNumber} in Column {self.column.id}"
        return f"Seat {self.seatNumber}"


@receiver(post_save, sender=Cabin)
def on_create_cabin_seat(sender, instance, created, **kwargs):
    """Creates seats for the cabins"""
    print("CREATING SEAT FOR CABIN")
    if created:
        for i in range(instance.seatSize):
            sta = Status.objects.create()
            Seat.objects.create(cabin=instance, inACabin=True, status=sta)


@receiver(post_save, sender=Column)
def on_create_column_seat(sender, instance, created, **kwargs):
    """Creates seats for the columns"""
    print("CREATING SEAT FOR COLUMN")
    if created:
        for i in range(instance.seatSize):
            sta = Status.objects.create(status="AVL")
            Seat.objects.create(column=instance, inACabin=False, status=sta)

# post_save.connect(on_create_cabin_column, sender=Couch)


# class UserBooking(models.Model):
#     schedule = models.ForeignKey(User, on_delete=models.CASCADE)
#     schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
#     data = models.DateTimeField(auto_now_add=True)
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_paid(self):
        """Mark the bill as paid."""
        self.is_paid = True
        bookings = self.user.userbooking_set.all()
        for book in bookings:
            if book.bed == None:
                book.seat.status.status = "BKL"
                book.seat.save()
                book.status = "PAYED"
                book.save()
            elif book.seat == None:
                book.bed.status.status = "BKL"
                book.bed.save()
                book.status = "PAYED"
                book.save()
            
        self.save()

    def __str__(self):
        return f"Bill #{self.id} - {self.user.username} - {'Paid' if self.is_paid else 'Pending'}"


class UserBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, null=True,on_delete=models.CASCADE)
    # berth = models.ForeignKey(Berth, null=True, on_delete=models.CASCADE)
    bed = models.ForeignKey(Bed, null=True, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    bill = models.ForeignKey(
        Bill, null=True, blank=True, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'PENDING'), ('PAYED', 'PAYED')],
        default='PENDING'
    )
    date = models.DateTimeField(auto_now_add=True)

    cost = models.IntegerField(null=True)

    def calculate_total_cost(self):
        """Calculate the total cost based on route distance and couch type price."""
        if self.bed ==None:
            route_distance = self.schedule.route.distanceToDestination
            couch_price = self.seat.cabin.couch.type.price
            total_cost = route_distance * couch_price
        elif self.seat ==None:
            route_distance = self.schedule.route.distanceToDestination
            couch_price = self.bed.berth.cabin.couch.type.price
            total_cost = route_distance * couch_price
        return total_cost

    def save(self, *args, **kwargs):
        """Override save to ensure payment is calculated and associated with a bill."""
        self.cost = self.calculate_total_cost()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking: {self.user.username} - Seat {self.seat} on {self.schedule}"


@receiver(post_save, sender=UserBooking)
def on_user_booking(sender, instance, created, **kwargs):
    """Creates seats for the columns"""
    print("CHANGING STTUS OF SEATS")
    if created:
        if instance.bed==None:
            status = Status.objects.create(status="RES")
            instance.seat.status = status
            instance.seat.save()
        if instance.seat == None:
            status = Status.objects.create(status="RES")
            instance.bed.status = status
            instance.bed.save()
            
