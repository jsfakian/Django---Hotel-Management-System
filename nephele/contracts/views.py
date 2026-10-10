from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from accounts.api_permissions import IsHotelStaff

from .models import Contract


@extend_schema(
    responses={(200, 'application/pdf'): OpenApiTypes.BINARY},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsHotelStaff])
def download_contract_pdf(request, contract_id):
    """Generate a PDF version of the contract"""
    contract = get_object_or_404(Contract, id=contract_id)
    try:
        from reportlab.pdfgen import canvas
    except Exception:
        return JsonResponse(
            {"error": "PDF generation dependency not available"},
            status=503,
        )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="contract_{contract.id}.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 12)
    p.drawString(100, 750, f"Contract: {contract.get_contract_type_display()}")
    p.drawString(
        100,
        730,
        f"Property Manager: {contract.property_manager.username if contract.property_manager else 'N/A'}",
    )
    p.drawString(100, 710, f"Travel Agency: {contract.travel_agency.name}")
    p.drawString(100, 690, f"Status: {contract.status}")

    p.drawString(100, 670, f"Start Date: {contract.start_date}")
    p.drawString(100, 650, f"End Date: {contract.end_date}")

    if contract.contract_type == "allotment":
        p.drawString(100, 630, f"Allocation: {contract.allocation_percentage}%")
    else:
        p.drawString(100, 630, f"Allocated Rooms: {contract.allocated_rooms}")

    p.drawString(100, 610, f"Commission Rate: {contract.commission_percentage}%")
    p.drawString(100, 590, f"Payment Terms: {contract.payment_terms[:50]}...")
    p.drawString(100, 570, f"Cancellation Policy: {contract.cancellation_policy[:50]}...")

    p.drawString(
        100,
        550,
        f"Property Manager Signature: {contract.property_manager_signature or 'Not signed'}",
    )
    p.drawString(
        100,
        530,
        f"Travel Agency Signature: {contract.travel_agency_signature or 'Not signed'}",
    )

    p.showPage()
    p.save()
    return response


def _user_role(user):
    try:
        return str(user.groups.all()[0])
    except Exception:
        return None


@login_required(login_url='login')
@require_http_methods(["GET"])
def contract_list_html(request):
    """HTML workspace view for listing contracts."""
    role = _user_role(request.user)

    if role == 'admin':
        contracts = (
            Contract.objects.select_related('property', 'travel_agency')
            .all()
            .order_by('-created_at')
        )
    elif role == 'manager':
        contracts = (
            Contract.objects.select_related('property', 'travel_agency')
            .filter(property_manager=request.user)
            .order_by('-created_at')
        )
    else:
        contracts = Contract.objects.none()

    return render(
        request,
        'common_pages/contracts.html',
        {
            'role': role,
            'contracts': contracts,
        },
    )
