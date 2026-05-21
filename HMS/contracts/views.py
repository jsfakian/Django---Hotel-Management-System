from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiTypes
from .models import Contract
from .serializers import ContractSerializer, ContractSignSerializer

@extend_schema(
    methods=['GET'],
    responses=ContractSerializer(many=True),
)
@extend_schema(
    methods=['POST'],
    request=ContractSerializer,
    responses=ContractSerializer,
)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def contract_list_create(request):
    """List all contracts or create a new one"""
    if request.method == "GET":
        contracts = Contract.objects.all()
        serializer = ContractSerializer(contracts, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == "POST":
        data = request.data.copy()
        data["property_manager"] = request.user.id
        serializer = ContractSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    methods=['GET'],
    responses=ContractSerializer,
)
@extend_schema(
    methods=['PUT'],
    request=ContractSerializer,
    responses=ContractSerializer,
)
@extend_schema(
    methods=['DELETE'],
    responses={204: OpenApiTypes.OBJECT},
)
@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def contract_detail(request, contract_id):
    """Retrieve, update or delete a contract by ID"""
    contract = get_object_or_404(Contract, id=contract_id)

    if request.method == "GET":
        serializer = ContractSerializer(contract)
        return JsonResponse(serializer.data)

    elif request.method == "PUT":
        serializer = ContractSerializer(contract, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        contract.delete()
        return JsonResponse({"message": "Contract deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@extend_schema(
    request=ContractSignSerializer,
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def sign_contract(request, contract_id):
    """Sign a contract as a hotel manager or agent"""
    contract = get_object_or_404(Contract, id=contract_id)
    serializer = ContractSignSerializer(data=request.data)

    if serializer.is_valid():
        signature = serializer.validated_data["signature"]
        user = request.user

        # Assign the signature to the correct party using model methods
        if user == contract.property_manager:
            contract.sign_property(signature=signature, user=user)
        elif user.is_staff or user.groups.filter(name__in=['admin', 'manager', 'travel_agent']).exists():
            contract.sign_agency(signature=signature)
        else:
            return JsonResponse({"error": "Unauthorized signer"}, status=status.HTTP_403_FORBIDDEN)
        return JsonResponse({"message": "Contract signed successfully"})
    return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    responses={(200, 'application/pdf'): OpenApiTypes.BINARY},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_contract_pdf(request, contract_id):
    """Generate a PDF version of the contract"""
    contract = get_object_or_404(Contract, id=contract_id)
    try:
        from reportlab.pdfgen import canvas
    except Exception:
        return JsonResponse(
            {"error": "PDF generation dependency not available"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="contract_{contract.id}.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 12)
    p.drawString(100, 750, f"Contract: {contract.get_contract_type_display()}")
    p.drawString(100, 730, f"Property Manager: {contract.property_manager.username if contract.property_manager else 'N/A'}")
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

    p.drawString(100, 550, f"Property Manager Signature: {contract.property_manager_signature or 'Not signed'}")
    p.drawString(100, 530, f"Travel Agency Signature: {contract.travel_agency_signature or 'Not signed'}")

    p.showPage()
    p.save()
    return response


# ---------------------------------------------------------------------------
# HTML views (used by the web portal workspace)
# ---------------------------------------------------------------------------

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.views.decorators.http import require_http_methods as _require_http_methods


def _user_role(user):
    try:
        return str(user.groups.all()[0])
    except Exception:
        return None


@login_required(login_url='login')
@_require_http_methods(["GET"])
def contract_list_html(request):
    """HTML workspace view for listing contracts."""
    role = _user_role(request.user)

    if role == 'admin':
        contracts = Contract.objects.select_related('property', 'travel_agency').all().order_by('-created_at')
    elif role == 'manager':
        contracts = Contract.objects.select_related('property', 'travel_agency').filter(
            property_manager=request.user
        ).order_by('-created_at')
    else:
        contracts = Contract.objects.none()

    return render(request, 'common_pages/contracts.html', {
        'role': role,
        'contracts': contracts,
    })
