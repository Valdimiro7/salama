from decimal import Decimal
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db import transaction as db_transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from core.models import (
    LeasedVehicle,
    VehicleLeaseContract,
    Member,
    CompanyAccount,
)
# ======================================================================================================================
# ======================================================================================================================

@login_required
def vehicle_lease_contract_list(request):
    """
    Lista de contratos de leasing de veículos + modal para novo contrato.
    """
    contracts = (
        VehicleLeaseContract.objects
        .select_related("leased_vehicle", "driver", "company_account")
        .order_by("-id")
    )

    # KPIs
    kpi_total = contracts.count()
    kpi_active = contracts.filter(status="active").count()
    kpi_weekly_sum = contracts.filter(status="active").aggregate(
        total=Sum("weekly_rent")
    )["total"] or Decimal("0")
    kpi_vehicles_in_leasing = (
        contracts.filter(status="active")
        .values("leased_vehicle_id")
        .distinct()
        .count()
    )

    # Para o modal de novo contrato:
    available_vehicles = LeasedVehicle.objects.filter(status="available").order_by("plate_number")
    drivers = Member.objects.filter(is_active=True).order_by("first_name", "last_name")
    company_accounts = CompanyAccount.objects.filter(is_active=True).order_by("name")

    context = {
        "contracts": contracts,
        "kpi_total": kpi_total,
        "kpi_active": kpi_active,
        "kpi_weekly_sum": kpi_weekly_sum,
        "kpi_vehicles_in_leasing": kpi_vehicles_in_leasing,
        "available_vehicles": available_vehicles,
        "drivers": drivers,
        "company_accounts": company_accounts,
        "segment": "vehicle_lease_contracts",
    }
    return render(request, "leasing/vehicle_lease_contract_list.html", context)


# ======================================================================================================================
# ======================================================================================================================

@login_required
@db_transaction.atomic
def create_vehicle_lease_contract(request):
    """
    Cria um novo contrato de leasing de viatura (via AJAX).
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método inválido."}, status=405)

    vehicle_id = request.POST.get("vehicle", "").strip()
    driver_id = request.POST.get("driver", "").strip()
    company_account_id = request.POST.get("company_account", "").strip()
    start_date_str = request.POST.get("start_date", "").strip()
    end_date_str = request.POST.get("end_date", "").strip()
    weekly_rent_raw = request.POST.get("weekly_rent", "").strip()
    payment_weekday_raw = request.POST.get("payment_weekday", "").strip()
    notes = request.POST.get("notes", "").strip()

    if not vehicle_id or not driver_id or not company_account_id or not start_date_str or not weekly_rent_raw:
        return JsonResponse(
            {
                "success": False,
                "message": "Preencha viatura, motorista, conta, data de início e renda semanal.",
            },
            status=400,
        )

    # validar / obter entidades
    leased_vehicle = get_object_or_404(LeasedVehicle, pk=vehicle_id)
    driver = get_object_or_404(Member, pk=driver_id)
    company_account = get_object_or_404(
        CompanyAccount,
        pk=company_account_id,
        is_active=True,
    )

    # datas
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Data de início inválida."},
            status=400,
        )

    end_date = None
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse(
                {"success": False, "message": "Data de fim inválida."},
                status=400,
            )

    # weekly rent
    try:
        weekly_rent = Decimal(str(weekly_rent_raw))
        if weekly_rent <= 0:
            raise ValueError
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Renda semanal inválida."},
            status=400,
        )

    # dia de pagamento (opcional) 1–7
    payment_weekday = None
    if payment_weekday_raw:
        try:
            pw = int(payment_weekday_raw)
            if pw < 1 or pw > 7:
                raise ValueError
            payment_weekday = pw
        except ValueError:
            return JsonResponse(
                {"success": False, "message": "Dia de pagamento inválido."},
                status=400,
            )

    contract = VehicleLeaseContract.objects.create(
        leased_vehicle=leased_vehicle,
        driver=driver,
        company_account=company_account,
        start_date=start_date,
        end_date=end_date,
        weekly_rent=weekly_rent,
        payment_weekday=payment_weekday,
        status="active",
        created_by=request.user,
        notes=notes or None,
    )

    # marcar viatura como "leased"
    leased_vehicle.status = "leased"
    leased_vehicle.save(update_fields=["status"])

    return JsonResponse(
        {"success": True, "message": f"Contrato #{contract.id} criado com sucesso."}
    )

# ======================================================================================================================
# ======================================================================================================================


# ======================================================================================================================
# ======================================================================================================================


# ======================================================================================================================
# ======================================================================================================================


# ======================================================================================================================
# ======================================================================================================================