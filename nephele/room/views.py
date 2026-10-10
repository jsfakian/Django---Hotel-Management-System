# imports
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm

from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Group, User

from datetime import datetime, date, timedelta
import random
# Create your views here.
from accounts.models import *
from room.models import *
from hotel.models import *
from .forms import *



def _booking_is_free(booking, fd, ed):
    return booking.startDate > ed.date() or booking.endDate < fd.date()


def _check_availability(rooms, fd, ed):
    availableRooms = []
    for room in rooms:
        availList = []
        bookingList = Booking.objects.filter(roomNumber=room)
        if room.statusStartDate is None:
            availList = [_booking_is_free(b, fd, ed) for b in bookingList]
            if all(availList):
                availableRooms.append(room)
        elif room.statusStartDate > ed.date() or room.statusEndDate < fd.date():
            for booking in bookingList:
                availList.append(_booking_is_free(booking, fd, ed))
                if all(availList):
                    availableRooms.append(room)
    return availableRooms


_ROOM_FILTER_LOOKUPS = (
    # (POST key, queryset lookup)
    ("number", "number__contains"),
    ("capacity", "capacity__gte"),
    ("nob", "numberOfBeds__gte"),
    ("type", "roomType__contains"),
    ("price", "price__lte"),
)


def _filter_rooms(rooms, post):
    for key, lookup in _ROOM_FILTER_LOOKUPS:
        if post.get(key) != "":
            rooms = rooms.filter(**{lookup: post.get(key)})
    return rooms


@ login_required(login_url='login')
def rooms(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"
    rooms = Room.objects.all()
    firstDayStr = None
    lastDateStr = None

    if request.method == "POST":
        if "dateFilter" in request.POST:
            firstDayStr = request.POST.get("fd", "")
            lastDateStr = request.POST.get("ld", "")

            firstDay = datetime.strptime(firstDayStr, '%Y-%m-%d')
            lastDate = datetime.strptime(lastDateStr, '%Y-%m-%d')

            rooms = _check_availability(rooms, firstDay, lastDate)

        if "filter" in request.POST:
            rooms = _filter_rooms(rooms, request.POST)

            context = {
                "role": role,
                "rooms": rooms,
                "number": request.POST.get("number"),
                "capacity": request.POST.get("capacity"),
                "nob": request.POST.get("nob"),
                "price": request.POST.get("price"),
                "type": request.POST.get("type")
            }
            return render(request, path + "rooms.html", context)

    context = {
        "role": role,
        'rooms': rooms,
        'fd': firstDayStr,
        'ld': lastDateStr
    }
    return render(request, path + "rooms.html", context)


@login_required(login_url='login')
def add_room(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    if request.method == "POST":
        guest = None
        if role == 'guest':
            guest = request.user.guest
        elif role == 'manager' or role == 'admin' or role == 'receptionist':
            guest = request.user.employee

        # announcement = Announcement(sender = sender, content = request.POST.get('textid'))
        number = request.POST.get('number')
        capacity = request.POST.get('capacity')
        numberOfBeds = request.POST.get('beds')
        roomType = request.POST.get('type')
        price = request.POST.get('price')
        print(capacity)
        room = Room(number=number, capacity=capacity,
                    numberOfBeds=numberOfBeds, roomType=roomType, price=price)

        room.save()
        return redirect('rooms')

    context = {
        "role": role
    }
    return render(request, path + "add-room.html", context)


def _lock_room(request, room, bookings):
    fd = datetime.strptime(request.POST.get("bsd"), '%Y-%m-%d')
    ed = datetime.strptime(request.POST.get("bed"), '%Y-%m-%d')
    has_conflict = any(
        b.endDate >= fd.date() and b.startDate <= ed.date() for b in bookings
    )
    if has_conflict:
        messages.error(request, "There is a booking in the interval!")
        return
    room.statusStartDate = fd
    room.statusEndDate = ed
    room.save()


def _unlock_room(room):
    room.statusStartDate = None
    room.statusEndDate = None
    room.save()


def _delete_room(request, room, bookings):
    """Delete the room unless it has bookings. Returns True when deleted."""
    today = datetime.now().date()
    can_delete = not any(b.startDate <= today or b.endDate >= today for b in bookings)
    if can_delete:
        room.delete()
        return True
    messages.error(request, "There is a booking in the interval!")
    return False


@login_required(login_url='login')
def room_profile(request, id):
    role = str(request.user.groups.all()[0])
    path = role + "/"
    tempRoom = Room.objects.get(number=id)
    bookings = Booking.objects.filter(roomNumber=tempRoom)
    guests = Guest.objects.all()
    bookings2 = Booking.objects.all()
    context = {
        "role": role,
        "bookings": bookings,
        "room": tempRoom,
        "guests": guests,
        "bookings2": bookings2
    }

    if request.method == "POST":
        if "lockRoom" in request.POST:
            _lock_room(request, tempRoom, bookings)
        if "unlockRoom" in request.POST:
            _unlock_room(tempRoom)
        if "deleteRoom" in request.POST and _delete_room(request, tempRoom, bookings):
            return redirect("rooms")

    return render(request, path + "room-profile.html", context)


@login_required(login_url='login')
def room_edit(request, pk):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    room = Room.objects.get(number=pk)
    form1 = editRoom(instance=room)

    context = {
        "role": role,
        "room": room,
        "form1": form1
    }

    if request.method == 'POST':
        form1 = editRoom(request.POST, instance=room)
        if form1.is_valid():
            form1.save()
            return redirect("room-profile", id=room.number)
    return render(request, path + "room-edit.html", context)


@ login_required(login_url='login')
def room_services(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    room_services = RoomServices.objects.all()
    context = {
        "role": role,
        "room_services": room_services
    }
    return render(request, path + "room-services.html", context)


_SERVICE_REQUESTS = (
    # (POST key, price, service type, task description)
    ("foodReq", 50.0, 'Food', "Food Request"),
    ("cleaningReq", 0.0, 'Cleaning', "Cleaning Request"),
    ("techReq", 0.0, 'Technical', "Tech Request"),
)


def _available_employees(max_task_num=10):
    group = Group.objects.get(name='staff')
    users = User.objects.filter(groups=group)
    all_employees = Employee.objects.filter(user__in=users)
    return [
        e for e in all_employees
        if Task.objects.filter(employee=e).count() < max_task_num
    ]


def _create_service_request(cur_booking, cur_room, available_employees,
                            price, services_type, description):
    import datetime

    RoomServices(
        curBooking=cur_booking, price=price, room=cur_room,
        servicesType=services_type).save()

    chosen_employee = random.choice(available_employees)
    last_task = Task.objects.filter(employee=chosen_employee).last()
    if last_task is not None:
        start_time = last_task.endTime
    else:
        start_time = datetime.datetime.now()
    Task(employee=chosen_employee, startTime=start_time,
         endTime=start_time + datetime.timedelta(minutes=30),
         description=description).save()


@login_required(login_url='login')
def current_room_services(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    curGuest = Guest.objects.get(user=request.user)
    curBooking = Booking.objects.filter(guest=curGuest).last()
    if curBooking is not None:
        curRoom = Room.objects.get(number=curBooking.roomNumber.number)
    else:
        context = {
            "role": role,
            "error": "You Don't Have Booking Right Now"
        }
        return render(request, path + "current-room-services.html", context)
    curRoomServices = RoomServices.objects.filter(curBooking=curBooking)

    room_services = RoomServices.objects.all()

    availableEmployee = _available_employees()

    context = {
        "role": role,
        "room_services": room_services,
        "curGuest": curGuest,
        "curBooking": curBooking,
        "curRoom": curRoom,
        "curRoomServices": curRoomServices
    }

    if request.method == "POST":
        for post_key, price, services_type, description in _SERVICE_REQUESTS:
            if post_key in request.POST:
                _create_service_request(
                    curBooking, curRoom, availableEmployee,
                    price, services_type, description)
                return redirect("current-room-services")

    return render(request, path + "current-room-services.html", context)


@login_required(login_url='login')
def bookings(request):
    import datetime
    role = str(request.user.groups.all()[0])
    path = role + "/"

    bookings = Booking.objects.all()
    # calculating total for every booking:
    totals = {}  # <booking : total>
    for booking in bookings:
        start_date = datetime.datetime.strptime(
            str(booking.startDate), "%Y-%m-%d")
        end_date = datetime.datetime.strptime(str(booking.endDate), "%Y-%m-%d")
        numberOfDays = abs((end_date-start_date).days)
        # get room peice:
        price = Room.objects.get(number=booking.roomNumber.number).price
        total = price * numberOfDays
        totals[booking] = total

    if request.method == "POST":
        if "filter" in request.POST:
            if (request.POST.get("number") != ""):
                rooms = Room.objects.filter(
                    number__contains=request.POST.get("number"))
                bookings = bookings.filter(
                    roomNumber__in=rooms)

            if (request.POST.get("name") != ""):
                users = User.objects.filter(
                    Q(first_name__contains=request.POST.get("name")) | Q(last_name__contains=request.POST.get("name")))
                guests = Guest.objects.filter(user__in=users)
                bookings = bookings.filter(
                    guest__in=guests)

            if (request.POST.get("rez") != ""):
                bookings = bookings.filter(
                    dateOfReservation=request.POST.get("rez"))

            if (request.POST.get("fd") != ""):
                bookings = bookings.filter(
                    startDate__gte=request.POST.get("fd"))

            if (request.POST.get("ed") != ""):
                bookings = bookings.filter(
                    endDate__lte=request.POST.get("ed"))

            context = {
                "role": role,
                'bookings': bookings,
                'totals': totals,
                "name": request.POST.get("name"),
                "number": request.POST.get("number"),
                "rez": request.POST.get("rez"),
                "fd": request.POST.get("fd"),
                "ed": request.POST.get("ed")
            }

            return render(request, path + "bookings.html", context)

    context = {
        "role": role,
        'bookings': bookings,
        'totals': totals
    }
    return render(request, path + "bookings.html", context)


def _dependee_names(post, room):
    names = [post.get("depName")]
    for i in range(room.capacity-2):
        nameid = "name" + str(i+1)
        if post.get(nameid) != "":
            names.append(post.get(nameid))
    return names


def _book_room_for_guest(request, room):
    post = request.POST
    if "guest" in post:
        curguest = Guest.objects.get(id=post.get("guest"))
    else:
        curguest = request.user.guest
    curbooking = Booking(guest=curguest, roomNumber=room, startDate=post.get(
        "fd"), endDate=post.get("ld"))
    curbooking.save()

    for i in range(room.capacity-1):
        nameid = "name" + str(i+1)
        if post.get(nameid) not in ("", None):
            Dependees(booking=curbooking, name=post.get(nameid)).save()


@login_required(login_url='login')
def booking_make(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    room = Room.objects.get(number=request.POST.get("roomid"))
    guests = Guest.objects.all()  # we pass this to context
    names = []
    if request.method == 'POST':
        if request.POST.get("fd") == "" or request.POST.get("ld") == "":
            return redirect("rooms")

        start_date = datetime.strptime(
            str(request.POST.get("fd")), "%Y-%m-%d")
        end_date = datetime.strptime(
            str(request.POST.get("ld")), "%Y-%m-%d")
        numberOfDays = abs((end_date-start_date).days)
        # get room peice:
        price = room.price
        total = price * numberOfDays

        if 'add' in request.POST:  # add dependee
            names = _dependee_names(request.POST, room)

        if 'bookGuestButton' in request.POST:
            _book_room_for_guest(request, room)
            return redirect("payment")

    context = {
        "fd": request.POST.get("fd"),
        "ld": request.POST.get("ld"),
        "role": role,
        "guests": guests,
        "room": room,
        "total": total,
        "names": names
    }

    return render(request, path + "booking-make.html", context)


@login_required(login_url='login')
def deleteBooking(request, pk):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    booking = Booking.objects.get(id=pk)
    if request.method == "POST":
        booking.delete()
        return redirect('bookings')

    context = {
        "role": role,
        'booking': booking

    }
    return render(request, path + "deleteBooking.html", context)


_REFUND_APPROVED_TEXT = """
                    Dear {guestName},
                    We are pleased to confirm that your refund request has been accepted.
                    The amount of refund will be on your account in 24 hours.
                    This time interval can change up to 48 hours according to your bank.
                    We are very sorry for this inconvenience. We hope to see you soon.
                """

_REFUND_DECLINED_TEXT = """
                    Dear {guestName},
                    We are sorry to inform you that your refund request has been declined.
                    After our examinations, we see that your request can not be done according to our Hotel Policy.
                    We are very sorry for this inconvenience. We hope to see you soon.
                """


def _send_refund_feedback(request, receiver, refund_id, text_template):
    """Email the guest about their refund decision and remove the refund request."""
    receiver_name = receiver.user.first_name + " " + receiver.user.last_name
    subject = "Refund"
    text = text_template.format(guestName=receiver_name)

    send_mail(
        receiver_name + " " + subject,    # subject
        text,                             # message
        'hms@support.com',                # from email
        [receiver.user.email],            # to email
        fail_silently=False,
    )

    messages.success(request, 'Feedback E-Mail Was Successfully Sent')
    Refund.objects.filter(id=refund_id).delete()


def _handle_refund_decision(request):
    refundId = request.POST.get("refund", "")
    guestUserId = request.POST.get("guestUserId", "")

    tempUser = User.objects.get(id=guestUserId)
    receiver = Guest.objects.get(user=tempUser)

    if "decline" in request.POST:
        _send_refund_feedback(request, receiver, refundId, _REFUND_DECLINED_TEXT)
    if "approve" in request.POST:
        _send_refund_feedback(request, receiver, refundId, _REFUND_APPROVED_TEXT)


def _filter_refunds(post, refunds):
    users = User.objects.all()
    if post.get("gid") != "":
        users = users.filter(id__contains=post.get("gid"))
        refunds = refunds.filter(guest__in=Guest.objects.filter(user__in=users))

    if post.get("name") != "":
        users = users.filter(
            Q(first_name__contains=post.get("name")) | Q(last_name__contains=post.get("name")))
        refunds = refunds.filter(guest__in=Guest.objects.filter(user__in=users))

    if post.get("booking") != "":
        booking = Booking.objects.get(id=post.get("booking"))
        refunds = refunds.filter(reservation=booking)

    if post.get("reason") != "":
        refunds = refunds.filter(reason__contains=post.get("reason"))
    return refunds


@ login_required(login_url='login')
def refunds(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    refunds = Refund.objects.all()
    context = {
        "role": role,
        'refunds': refunds
    }

    if request.method == "POST":
        if "decline" in request.POST or "approve" in request.POST:
            _handle_refund_decision(request)

        if "filter" in request.POST:
            context = {
                "role": role,
                "refunds": _filter_refunds(request.POST, refunds),
                "gid": request.POST.get("gid"),
                "name": request.POST.get("name"),
                "booking": request.POST.get("booking"),
                "reason": request.POST.get("reason")
            }
            return render(request, path + "refunds.html", context)

    return render(request, path + "refunds.html", context)


@login_required(login_url='login')
def request_refund(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    curGuest = Guest.objects.get(user=request.user)

    if request.method == "POST":
        if "sendReq" in request.POST:
            reason = request.POST.get("reqExp")
            curBookingId = request.POST.get("bid")
            currentBooking = Booking.objects.get(id=curBookingId)
            temp = Refund.objects.filter(reservation=currentBooking)
            if not temp:
                currentReq = Refund(
                    guest=curGuest, reservation=currentBooking, reason=reason)
                currentReq.save()
                messages.success(
                    request, "Your request was successfully sent.")
            else:
                messages.error(
                    request, "We already have your refund request for this reservation!")

    context = {
        "role": role,
        "curGuest": curGuest,
        "id": request.POST.get("bookingId")
    }

    return render(request, path + "request-refund.html", context)
