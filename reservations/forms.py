from django import forms
from .models import Location, Train, CouchType, Couch, Schedule, Station, Route


class AddLocationForm(forms.ModelForm):
    train = forms.ModelChoiceField(
        queryset=Train.objects.all(), empty_label="Select a Train")

    class Meta:
        model = Location
        fields = ['coordinatesX', 'coordinatesY', 'train']
        widgets = {
            'coordinatesX': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'coordinatesY': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }

    def save(self, commit=True):
        location = super().save(commit=False)
        train = self.cleaned_data.get('train')

        if train.location:  # If the train already has a location
            raise forms.ValidationError(
                f"Train '{train}' already has a location. Please update it instead.")

        if commit:
            location.save()
            train.location = location  # Link the location to the train
            train.save()

        return location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["coordinatesX", "coordinatesY"]


class CouchTypeForm(forms.ModelForm):
    class Meta:
        model = CouchType
        fields = ["name", "seatCapacity", "seatPrice"]


class AddCouchForm(forms.ModelForm):
    class Meta:
        model = Couch
        fields = ["type", "cabinSize"]  # Exclude code and train
        widgets = {
            "type": forms.Select(attrs={
                "class": "block w-full mt-1 rounded-md border-gray-300 shadow-sm"
            }),
            "cabinSize": forms.NumberInput(attrs={
                "class": "block w-full mt-1 rounded-md border-gray-300 shadow-sm",
                "placeholder": "Enter cabin size",
            }),
        }


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['train', 'route', 'arrivalTime', 'departureTime']

    def __init__(self, *args, **kwargs):
        super(ScheduleForm, self).__init__(*args, **kwargs)
        # Filter trains where father field is True
        self.fields['train'].queryset = Train.objects.filter(father=True)


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['coordinatesX', 'coordinatesY']


class StationForm(forms.ModelForm):
    location = LocationForm()

    class Meta:
        model = Station
        fields = ['stationName', 'city']

    # def save(self, commit=True):
    #     # Save the location first
    #     location = self.cleaned_data['location']
    #     location.save()

    #     # Then save the station
    #     station = super().save(commit=False)
    #     station.location = location

    #     if commit:
    #         station.save()

    #     return station


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['sourceStation', 'destinationStation',
                  'distanceToDestination']
