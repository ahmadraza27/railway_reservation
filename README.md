<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-28-05" src="https://github.com/user-attachments/assets/aa488456-798c-4cea-8bfc-8a47526f48ec" /> # 🚂 TrainWrek: Railway Reservation System

**TrainWrek** is a comprehensive Django-based railway management and booking system. The `reservations` application handles everything from route pathfinding and schedule management to granular seat and bed reservations.

---

## 🌟 Key Features

 **Advanced Route Pathfinding**: Utilizes graph-based algorithms to find all possible paths between source and destination stations, calculating total travel time and distance.
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-25-23" src="https://github.com/user-attachments/assets/b63b0bfd-0dfc-4d80-973b-c4f6931f3c7b" />


 **Granular Seating Structure**: Automatically generates couches, cabins, columns, berths, beds, and seats using Django `post_save` signals.
<img width="1849" height="956" alt="Screenshot from 2024-12-10 22-45-05" src="https://github.com/user-attachments/assets/2fbcbef0-d75e-4584-81c9-ab1e016dc02c" />



 **Role-Based Access Control**: Restricts view access using custom decorators for specific user roles like admins and ticket collectors.
<img width="1849" height="956" alt="Screenshot from 2024-12-10 22-45-27" src="https://github.com/user-attachments/assets/8ea5d954-0eb7-44d6-aadf-83ce52a2156f" />


 **Automated Seat Management**: Integrates Celery tasks to automatically check and reset unpaid reserved seats one hour prior to train arrival.
<img width="1849" height="956" alt="Screenshot from 2024-12-10 22-45-11" src="https://github.com/user-attachments/assets/26cc3415-6e08-46f4-9d18-0557065b32a8" />


 **Billing & Payments**: Calculates total trip costs based on route distance and couch type pricing, allowing users to securely check out.
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-24-30" src="https://github.com/user-attachments/assets/3c005bc8-88b2-4622-82b6-3b14ee9a0888" />


 **Comprehensive Admin Dashboard**: Manage locations, trains, schedules, couches, user bookings, and bills from the centralized Django admin panel.
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-27-57" src="https://github.com/user-attachments/assets/f85f7c3b-5dce-4f02-ae3a-1d315ec53645" />
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-28-05" src="https://github.com/user-attachments/assets/bea8c6e8-122c-45ff-a3c4-0c894af72d1f" />
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-28-37" src="https://github.com/user-attachments/assets/5b593801-243a-4eb3-af9e-ea2f814610ac" />
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-28-48" src="https://github.com/user-attachments/assets/36cf8046-81d8-4156-875d-8f142e168e0e" />
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-28-58" src="https://github.com/user-attachments/assets/626295d0-f0cd-45f7-b155-3d12d5dee81e" />





---

## 🏗️ Core Models Architecture

The application relies on a highly relational database structure to accurately map real-world train layouts and schedules.

| Model | Description |
| --- | --- |
| **Train & Station** | Defines the physical trains and the city stations they operate between.
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-27-57" src="https://github.com/user-attachments/assets/7aafe153-3887-4df1-b586-fda776cbf853" />

 |
| **Route & Schedule** | Maps out the distances between stations and handles departure/arrival times.
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-28-48" src="https://github.com/user-attachments/assets/88be1b5c-2858-4e78-af3f-067dd1decb12" />

 |
| **Couch & Cabin** | Divides trains into specific couch types (with pricing) and interior cabins.
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-28-23" src="https://github.com/user-attachments/assets/1a91cd33-1177-4196-a87e-05a60639e046" />

 |
| **Seat & Bed** | Granular entities representing individual sitting or sleeping arrangements with real-time status tracking (Available, Reserved, Booked).

 |
| **UserBooking & Bill** | Associates users with their selected seats/beds, calculates dynamic costs, and tracks payment fulfillment.
<img width="1849" height="956" alt="Screenshot from 2024-12-15 18-24-30" src="https://github.com/user-attachments/assets/562f9195-0bc7-44f4-92a3-af70d19288d9" />

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
