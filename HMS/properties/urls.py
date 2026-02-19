from django.urls import path
from . import views

urlpatterns = [
    path('', views.properties_list, name='properties-list'),
    path('create/', views.property_create, name='property-create'),
    path('<int:pk>/', views.property_detail, name='property-detail'),
    path('<int:pk>/edit/', views.property_edit, name='property-edit'),
    path('<int:pk>/delete/', views.property_delete, name='property-delete'),
    path('<int:pk>/amenities/', views.property_amenities, name='property-amenities'),
    path('<int:pk>/policy/', views.property_policy, name='property-policy'),
]
