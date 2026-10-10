from django.urls import path
from . import views

urlpatterns = [
    # Notifications
    path('', views.notification_list, name='notification-list'),
    path('<int:notification_id>/read/', views.mark_as_read, name='mark-as-read'),
    path('mark-all-as-read/', views.mark_all_as_read, name='mark-all-as-read'),
    path('<int:notification_id>/delete/', views.delete_notification, name='delete-notification'),
    
    # Preferences
    path('preferences/', views.notification_preferences, name='notification-preferences'),
]
