from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from django.db.models import Q, Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User

from django.contrib import messages
from hotel.models import Guest
from datetime import datetime, date, timedelta
import random
import json
import logging

# Own imports
from accounts.models import *
from room.models import *
from hotel.models import *
from .forms import *
# Create your views here.


def register_page(request):
    form = CreateUserForm()
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                if (len(User.objects.filter(email=request.POST.get("email"))) != 0):
                    messages.error(
                        request, 'Email address is alredy taken')
                    return redirect('login')

                user = form.save()
                username = form.cleaned_data.get('username')

                group = Group.objects.get(name="guest")
                user.groups.add(group)

                curGuest = Guest(
                    user=user, phoneNumber=request.POST.get("phoneNumber"))
                curGuest.save()

                messages.success(
                    request, 'Guest Account Was Created Succesfuly For ' + username)

                return redirect('login')

        context = {'form': form}
        return render(request, 'accounts/register.html', context)


@login_required(login_url='login')
def add_employee(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    form = CreateUserForm()
    form2 = ROLES()
    form3 = CreateEmployeeForm()

    if request.method == 'POST':
        post = request.POST.copy()  # to make it mutable
        post['phoneNumber'] = "+90" + post['phoneNumber']
        request.POST = post

        form = CreateUserForm(request.POST)
        form2 = ROLES(request.POST)
        form3 = CreateEmployeeForm(request.POST)

        if form.is_valid() and form2.is_valid() and form3.is_valid():
            user = form.save()
            employee = form3.save()
            employee.user = user
            employee.save()

            username = form.cleaned_data.get('username')

            role = form2.cleaned_data.get("ROLES_TYPES")

            group = Group.objects.get(name=role)
            user.groups.add(group)

            messages.success(
                request, role + ' Account Was Created Succesfuly For ' + username)

            return redirect('employees')

    context = {
        'form': form,
        'form2': form2,
        'form3': form3,
        "role": role
    }
    return render(request, path + "add-employee.html", context)


def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == "POST":
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.info(request, "Username or Password is incorrect")

        context = {}
        return render(request, 'accounts/login.html', context)


def logout_user(request):
    logout(request)
    return redirect('login')


def _ranked_guest_bookings():
    return Booking.objects.all().values("guest").annotate(
        total=Count("guest")).order_by("-total")


def _top_guest_list(ranked, limit):
    top_list = []
    for t in ranked:
        if len(top_list) >= int(limit):
            break
        top_list.append(Guest.objects.get(id=t.get("guest")))
    return top_list


def _append_guests_in_range(bookings, fd, ld, guests):
    """Append guests with bookings overlapping [fd, ld] to ``guests`` in place."""
    for b in bookings:
        if b.endDate >= fd.date() and b.startDate <= ld.date():
            if b.guest not in guests:
                guests.append(b.guest)


def _parse_filter_range(post):
    """Parse the f_day/l_day form values, defaulting blank ones to wide bounds."""
    if post.get("f_day") == "":
        fd = datetime.strptime("1970-01-01", '%Y-%m-%d')
    else:
        fd = datetime.strptime(post.get("f_day"), '%Y-%m-%d')

    if post.get("l_day") == "":
        ld = datetime.strptime("2030-01-01", '%Y-%m-%d')
    else:
        ld = datetime.strptime(post.get("l_day"), '%Y-%m-%d')
    return fd, ld


_GUEST_USER_FILTERS = (
    ("id", lambda value: Q(id__contains=value)),
    ("name", lambda value: Q(first_name__contains=value) | Q(last_name__contains=value)),
    ("email", lambda value: Q(email__contains=value)),
)


def _filter_guests(post):
    guests = Guest.objects.all()
    users = User.objects.all()
    for key, build_query in _GUEST_USER_FILTERS:
        if post.get(key) != "":
            users = users.filter(build_query(post.get(key)))
            guests = guests.filter(user__in=users)

    if post.get("number") != "":
        guests = guests.filter(phoneNumber__contains=post.get("number"))
    return guests


@login_required(login_url='login')
def guests(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    topLimit = 10
    topList = _top_guest_list(_ranked_guest_bookings(), 11)

    bookings = Booking.objects.all()
    fd = datetime.combine(date.today()-timedelta(days=30), datetime.min.time())
    ld = datetime.combine(date.today(), datetime.min.time())
    guests = []
    _append_guests_in_range(bookings, fd, ld, guests)

    if request.method == "POST":
        post = request.POST
        if "filterDate" in post:
            if post.get("f_day") == "" and post.get("l_day") == "":
                context = {
                    "role": role,
                    "guests": Guest.objects.all(),
                    "fd": "",
                    "ld": ""
                }
                return render(request, path + "guests.html", context)

            fd, ld = _parse_filter_range(post)
            _append_guests_in_range(bookings, fd, ld, guests)

        if "filterGuest" in post:
            context = {
                "role": role,
                "guests": _filter_guests(post),
                "id": post.get("id"),
                "name": post.get("name"),
                "email": post.get("email"),
                "number": post.get("number")
            }
            return render(request, path + "guests.html", context)

        if "top" in post:
            topLimit = post.get("top")
            topList = _top_guest_list(_ranked_guest_bookings(), topLimit)
            context = {
                "role": role,
                "guests": guests,
                "topList": topList,
                "topLimit": topLimit,
                "fd": fd,
                "ld": ld
            }
            return render(request, path + "guests.html", context)
    context = {
        "role": role,
        "guests": guests,
        "topList": topList,
        "topLimit": topLimit,
        "fd": fd,
        "ld": ld
    }
    return render(request, path + "guests.html", context)


@login_required(login_url='login')
def employees(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    employees = Employee.objects.all()

    if request.method == "POST":
        if "filter" in request.POST:
            users = User.objects.all()
            if (request.POST.get("id") != ""):
                users = users.filter(
                    id__contains=request.POST.get("id"))
                employees = employees.filter(user__in=users)

            if (request.POST.get("name") != ""):
                users = users.filter(
                    Q(first_name__contains=request.POST.get("name")) | Q(last_name__contains=request.POST.get("name")))
                employees = employees.filter(user__in=users)

            if (request.POST.get("email") != ""):
                users = users.filter(email__contains=request.POST.get("email"))
                employees = employees.filter(user__in=users)

            if (request.POST.get("number") != ""):
                employees = employees.filter(
                    phoneNumber__contains=request.POST.get("number"))

            if (request.POST.get("filterRole") != ""):
                try:
                    group = Group.objects.get(
                        name__contains=request.POST.get("filterRole"))
                except:
                    group = None
                users = users.filter(groups=group)
                employees = employees.filter(user__in=users)

        context = {
            "role": role,
            "employees": employees,
            "id": request.POST.get("id"),
            "name": request.POST.get("name"),
            "email": request.POST.get("email"),
            "number": request.POST.get("number"),
            "filterRole": request.POST.get("filterRole")
        }
        return render(request, path + "employees.html", context)

    context = {
        "role": role,
        "employees": employees
    }
    return render(request, path + "employees.html", context)


@login_required(login_url='login')
def employee_details(request, pk):
    if request.method == 'POST':
        user = User.objects.get(id=pk)
        employee = Employee.objects.get(user=user)
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        employee.phoneNumber = request.POST.get("phoneNumber")
        user.save()
        employee.save()
        return redirect("home")

    role = str(request.user.groups.all()[0])
    path = role + "/"

    tempUser = User.objects.get(id=pk)
    employee = Employee.objects.get(user=tempUser)
    tasks = Task.objects.filter(employee=employee)
    context = {
        "role": role,
        "employee": employee,
        "tasks": tasks
    }
    return render(request, path + "employee-profile.html", context)


@ login_required(login_url='login')
def employee_details_edit(request, pk):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    tempuser = User.objects.get(id=pk)
    employee = Employee.objects.get(user=tempuser)

    form1 = editEmployee(instance=employee)
    form2 = editUser(instance=tempuser)

    context = {
        "role": role,
        "employee": employee,
        "user": tempuser,
        "form1": form1,
        "form2": form2
    }

    if request.method == "POST":
        form1 = editEmployee(request.POST, instance=employee)
        form2 = editUser(request.POST, instance=tempuser)
        if form1.is_valid() and form2.is_valid():
            form1.save()
            form2.save()

    return render(request, path + "employee-edit.html", context)


@ login_required(login_url='login')
def guest_edit(request, pk):
    role = str(request.user.groups.all()[0])
    path = role + "/"
    tempuser = User.objects.get(id=pk)
    guest = Guest.objects.get(user=tempuser)
    form1 = editGuest(instance=guest)
    form2 = editUser(instance=tempuser)

    context = {
        "role": role,
        "guest": guest,
        "form1": form1,
        "form2": form2,
        "user": tempuser,
    }

    if request.method == "POST":
        form1 = editGuest(request.POST, instance=guest)
        form2 = editUser(request.POST, instance=tempuser)
        if form1.is_valid and form2.is_valid:
            form1.save()
            form2.save()

    return render(request, path + "guest-edit.html", context)


@login_required(login_url='login')
def guest_profile(request, pk):
    tempUser = User.objects.get(id=pk)
    guest = Guest.objects.get(user=tempUser)

    if request.method == 'POST':
        tempUser.first_name = request.POST.get("first_name")
        tempUser.last_name = request.POST.get("last_name")
        guest.phoneNumber = request.POST.get("phoneNumber")
        tempUser.save()
        guest.save()
        return redirect("home")
    role = str(request.user.groups.all()[0])
    path = role + "/"

    eventAttendees = EventAttendees.objects.filter(guest=guest)
    bookings = Booking.objects.filter(guest=guest)
    context = {
        "role": role,
        "guest": guest,
        "eventAttendees": eventAttendees,
        "bookings": bookings
    }
    return render(request, path + "guest-profile.html", context)


@login_required(login_url='login')
def tasks(request):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    tempEmp = Employee.objects.get(user=request.user)
    tasks = Task.objects.filter(employee=tempEmp)

    context = {
        "role": role,
        'tasks': tasks
    }
    if request.method == "POST":
        if "markAsComplete" in request.POST:
            tid = request.POST.get("tid")
            Task.objects.get(id=tid).delete()
            return redirect("tasks")

        if "filter" in request.POST:
            if(request.POST.get("id") != ""):
                tasks = tasks.filter(id=request.POST.get("id"))

            if(request.POST.get("desc") != ""):
                tasks = tasks.filter(
                    description__contains=request.POST.get("desc"))

            if(request.POST.get("fd") != ""):
                tasks = tasks.filter(startTime__gte=request.POST.get("fd"))

            if(request.POST.get("ed") != ""):
                tasks = tasks.filter(endTime__lte=request.POST.get("ed"))

            context = {
                "role": role,
                "tasks": tasks,
                "id": request.POST.get("id"),
                "desc": request.POST.get("desc"),
                "fd": request.POST.get("fd"),
                "ed": request.POST.get("ed")
            }

    return render(request, path + "tasks.html", context)


@login_required(login_url='login')
def completeTask(request, pk):
    role = str(request.user.groups.all()[0])
    path = role + "/"

    task = Task.objects.get(id=pk)
    if request.method == "POST":
        task.delete()
        return redirect("tasks")

    context = {
        "role": role,
        'task': task

    }
    return render(request, path + "completeTask.html", context)


# ============================================================================
# GDPR Data Export API Views (DRF)
# ============================================================================

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ViewSet
from rest_framework.request import Request

from .services.gdpr_export import GDPRExportService, get_gdpr_export_json
from .tasks import export_user_data_async


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_data_export(request: Request) -> Response:
    """
    Request GDPR data export (Article 20 - Right to Data Portability)
    
    User submits request to download their complete personal data in JSON format.
    For large exports (>10MB), request is queued as async task.
    
    POST /api/v1/gdpr/request-export/
    {
        "send_email": true  # Optional: send export via email
    }
    
    Returns:
        {
            "status": "success",
            "message": "Export requested",
            "export_id": "task_uuid",
            "data": {...}  # If small export
        }
    """
    try:
        user = request.user
        send_email = request.data.get('send_email', False)
        
        # Generate export
        service = GDPRExportService(user)
        export_data = service.export_to_dict()
        
        # Get rough size estimate
        json_str = service.export_to_json_string()
        data_size = len(json_str.encode('utf-8'))
        
        # If small, return directly
        if data_size < 5 * 1024 * 1024:  # 5MB threshold
            return Response({
                'status': 'success',
                'message': 'Data export completed',
                'data_size_bytes': data_size,
                'data': export_data,
            }, status=status.HTTP_200_OK)
        
        # Otherwise queue async task
        else:
            from django.core.cache import cache

            task = export_user_data_async.delay(user.id, send_email=send_email)
            cache.set(f'gdpr_export_owner:{task.id}', user.id, timeout=60 * 60 * 24)
            return Response({
                'status': 'queued',
                'message': 'Large export queued for processing',
                'export_id': str(task.id),
                'estimated_size_bytes': data_size,
                'check_url': f'/api/v1/gdpr/export-status/{task.id}/',
            }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_data_export(request: Request) -> Response:
    """
    Download GDPR data export as JSON
    
    Downloads the complete personal data export.
    Use this after request_data_export returns a small export,
    or check export-status to confirm async export.
    
    GET /api/v1/gdpr/download-export/
    
    Returns: JSON file as attachment
    """
    try:
        user = request.user
        
        # Generate export
        json_data = get_gdpr_export_json(user)
        
        # Return as file download
        response = Response(
            json.loads(json_data),
            status=status.HTTP_200_OK,
            content_type='application/json'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="gdpr_export_{user.id}.json"'
        )
        
        return response
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_export_status(request: Request, task_id: str) -> Response:
    """
    Check status of async data export task
    
    Polls the status of a data export task by its Celery task ID.
    
    GET /api/v1/gdpr/export-status/{task_id}/
    
    Returns:
        {
            "status": "pending|processing|completed|failed",
            "task_id": "...",
            "progress": 0-100,  # If processing
            "result": {...}  # If completed
        }
    """
    try:
        from celery import current_app
        from django.core.cache import cache

        owner_id = cache.get(f'gdpr_export_owner:{task_id}')
        if owner_id is None or int(owner_id) != request.user.id:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        task = current_app.AsyncResult(task_id)
        payload = {
            'task_id': task_id,
            'status': task.state,
            'progress': task.info.get('progress', 0) if task.state == 'PROGRESS' else None,
        }
        if task.state == 'SUCCESS' and isinstance(task.result, dict):
            # Only expose non-sensitive completion metadata
            payload['result'] = {
                'status': task.result.get('status'),
                'user_id': task.result.get('user_id'),
            }
        return Response(payload, status=status.HTTP_200_OK)

    except Exception:
        return Response({
            'status': 'error',
            'message': 'Unable to check export status',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_data_deletion(request: Request) -> Response:
    """
    Request GDPR data deletion (Article 17 - Right to be Forgotten)
    
    User requests their data be deleted/anonymized.
    Deletion requires confirmation via email.
    
    POST /api/v1/gdpr/request-deletion/
    {
        "confirm": true,
        "reason": "optional reason"
    }
    
    Returns:
        {
            "status": "requested|confirmed|processing",
            "message": "...",
            "confirmation_token": "..."  # For email confirmation
        }
    """
    try:
        user = request.user
        confirm = request.data.get('confirm', False)
        reason = request.data.get('reason', 'User requested deletion')
        
        if not confirm:
            return Response({
                'status': 'error',
                'message': 'Deletion must be confirmed',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Log deletion request
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f'GDPR deletion request for user {user.id} ({user.email}): {reason}'
        )
        
        # Send confirmation email
        # In production, send confirmation email with link
        # Tasks will be triggered via Celery in async manner
        
        return Response({
            'status': 'requested',
            'message': 'Deletion request received. ' \
                      'Please confirm via email link.',
            'user_id': user.id,
        }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
