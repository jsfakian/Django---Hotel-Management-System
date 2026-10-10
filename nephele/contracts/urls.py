from django.urls import path

from . import views

# HTML workspace + PDF download. JSON CRUD/sign live on /api/v1/contracts/.
urlpatterns = [
    path('', views.contract_list_html, name='contract-list'),
    path('<int:contract_id>/pdf/', views.download_contract_pdf, name='contract-pdf'),
]
