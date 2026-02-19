from django.urls import path

from . import views

urlpatterns = [
    path('', views.contract_list_create, name='contract-list-create'),
    path('<int:contract_id>/', views.contract_detail, name='contract-detail'),
    path('<int:contract_id>/sign/', views.sign_contract, name='contract-sign'),
    path('<int:contract_id>/pdf/', views.download_contract_pdf, name='contract-pdf'),
]
