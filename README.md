 # 🚂 TrainWrek: Railway Reservation System

**TrainWrek** is a comprehensive Django-based railway management and booking system. The `reservations` application handles everything from route pathfinding and schedule management to granular seat and bed reservations.

---

## 🌟 Key Features

* **Advanced Route Pathfinding**: Utilizes graph-based algorithms to find all possible paths between source and destination stations, calculating total travel time and distance.


* **Granular Seating Structure**: Automatically generates couches, cabins, columns, berths, beds, and seats using Django `post_save` signals.


* **Role-Based Access Control**: Restricts view access using custom decorators for specific user roles like admins and ticket collectors.


* **Automated Seat Management**: Integrates Celery tasks to automatically check and reset unpaid reserved seats one hour prior to train arrival.


* **Billing & Payments**: Calculates total trip costs based on route distance and couch type pricing, allowing users to securely check out.


* **Comprehensive Admin Dashboard**: Manage locations, trains, schedules, couches, user bookings, and bills from the centralized Django admin panel.



---

## 🏗️ Core Models Architecture

The application relies on a highly relational database structure to accurately map real-world train layouts and schedules.

| Model | Description |
| --- | --- |
| **Train & Station** | Defines the physical trains and the city stations they operate between.

 |
| **Route & Schedule** | Maps out the distances between stations and handles departure/arrival times.

 |
| **Couch & Cabin** | Divides trains into specific couch types (with pricing) and interior cabins.

 |
| **Seat & Bed** | Granular entities representing individual sitting or sleeping arrangements with real-time status tracking (Available, Reserved, Booked).

 |
| **UserBooking & Bill** | Associates users with their selected seats/beds, calculates dynamic costs, and tracks payment fulfillment.

 |

---

## 💻 Tech Stack

* **Backend framework**: Django (Python)


* **Background Tasks**: Celery


* **Database Objects**: Complex relational models with automatic signal dispatching



---

## 🚀 Getting Started

Follow these commands to get the TrainWrek project up and running on your local development environment.

**1. Clone the repository and navigate into it:**

```bash
git clone <repository_url>
cd <repository_folder>

```

**2. Set up a virtual environment and activate it:**

```bash
python -m venv env
# On Windows
env\Scripts\activate
# On Mac/Linux
source env/bin/activate

```

**3. Install required dependencies:**

```bash
pip install -r requirements.txt

```

**4. Apply database migrations:**

```bash
python manage.py makemigrations
python manage.py migrate

```

**5. Create a superuser for admin panel access:**

```bash
python manage.py createsuperuser

```

**6. Run the Celery worker (in a separate terminal) for automated seat resetting:**

```bash
celery -A <project_name> worker -l info

```

**7. Start the local development server:**

```bash
python manage.py runserver

```

You can now access the public booking portal at `[http://127.0.0.1:8000/](http://127.0.0.1:8000/)` and the management dashboard at `[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)`[cite: 9].
