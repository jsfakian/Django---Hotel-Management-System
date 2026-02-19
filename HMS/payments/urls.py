from django.urls import path
from . import views

urlpatterns = [
    # Payment processing
    path('process/', views.process_payment, name='payment-process'),
    path('process/<int:booking_id>/', views.process_payment, name='payment-process-booking'),
    path('verify/<int:payment_id>/', views.verify_payment, name='payment-verify'),
    path('success/<int:payment_id>/', views.payment_success, name='payment-success'),
    
    # Payment history
    path('history/', views.payment_history, name='payment-history'),
    
    # Invoices
    path('invoices/', views.invoice_list, name='invoice-list'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice-detail'),
    
    # Refunds
    path('refund/<int:payment_id>/', views.request_refund, name='request-refund'),
    path('refund-history/', views.refund_history, name='refund-history'),
    path('refund/<int:refund_id>/manage/', views.manage_refund, name='manage-refund'),
    
    # MyData (AADE) Integration - Greek tax authority system
    path('invoices/<int:invoice_id>/mydata/transmit/', views.transmit_invoice_to_mydata, name='invoice-mydata-transmit'),
    path('invoices/<int:invoice_id>/mydata/status/', views.mydata_transmission_status, name='invoice-mydata-status'),
    path('invoices/<int:invoice_id>/mydata/export/', views.invoice_mydata_export, name='invoice-mydata-export'),
    path('invoices/mydata/bulk-transmit/', views.bulk_transmit_invoices_to_mydata, name='invoices-mydata-bulk-transmit'),
]
