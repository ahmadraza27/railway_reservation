from django.contrib import admin
from .models import Location, Train, Station, Route, Schedule, UserBooking, CouchType, Couch, User, Cabin, Column, Status, Seat,City,Bed,Berth

admin.site.register(Location)
admin.site.register(Train)
admin.site.register(Station)
admin.site.register(Route)
admin.site.register(Schedule)
admin.site.register(UserBooking)
admin.site.register(CouchType)
admin.site.register(Couch)
admin.site.register(Cabin)
admin.site.register(Column)
admin.site.register(Status)
admin.site.register(Seat)
admin.site.register(City)
admin.site.register(Berth)
admin.site.register(Bed)

# admin.site.register(User)  # TODO make this a custom model
# Register your models here.
