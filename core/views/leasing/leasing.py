# core/views/leasing.py

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.http import JsonResponse
from django.shortcuts import render

from core.models import LeasedVehicle


@login_required
def leased_vehicle_list(request):
    """
    Lista de veículos em leasing (frota) + modal para criar nova viatura.
    """
    vehicles = LeasedVehicle.objects.all().order_by("plate_number")

    kpi_total = vehicles.count()
    kpi_available = vehicles.filter(status="available").count()
    kpi_leased = vehicles.filter(status="leased").count()
    kpi_maintenance = vehicles.filter(status="maintenance").count()

    context = {
        "vehicles": vehicles,
        "kpi_total": kpi_total,
        "kpi_available": kpi_available,
        "kpi_leased": kpi_leased,
        "kpi_maintenance": kpi_maintenance,
        "segment": "vehicle_lease_fleet",
    }
    return render(request, "leasing/leased_vehicle_list.html", context)


# ======================================================================================================================
# ======================================================================================================================

@login_required
@db_transaction.atomic
def create_leased_vehicle(request):
    """
    Cria uma nova viatura em leasing (via AJAX).
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método inválido."}, status=405)

    plate_number = request.POST.get("plate_number", "").strip()
    brand = request.POST.get("brand", "").strip()              # NOVO
    model = request.POST.get("model", "").strip()
    year = request.POST.get("year", "").strip()
    chassis_number = request.POST.get("chassis_number", "").strip()

    weekly_rent = request.POST.get("weekly_rent_default", "").strip() or "0"
    acquisition_cost_raw = request.POST.get("acquisition_cost", "").strip() or None  # NOVO

    status = request.POST.get("status", "available").strip() or "available"
    notes = request.POST.get("notes", "").strip()

    if not plate_number:
        return JsonResponse(
            {"success": False, "message": "Informe a matrícula da viatura."},
            status=400,
        )

    # validar renda semanal
    try:
        weekly_rent_dec = Decimal(str(weekly_rent))
        if weekly_rent_dec < 0:
            raise ValueError
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Valor de renda semanal inválido."},
            status=400,
        )

    # validar custo de aquisição (opcional)
    acquisition_cost_dec = None
    if acquisition_cost_raw:
        try:
            acquisition_cost_dec = Decimal(str(acquisition_cost_raw))
            if acquisition_cost_dec < 0:
                raise ValueError
        except Exception:
            return JsonResponse(
                {"success": False, "message": "Custo de aquisição inválido."},
                status=400,
            )

    # validar ano (opcional)
    year_val = None
    if year:
        try:
            year_val = int(year)
        except ValueError:
            return JsonResponse(
                {"success": False, "message": "Ano inválido."},
                status=400,
            )

    # criar
    LeasedVehicle.objects.create(
        plate_number=plate_number,
        brand=brand or None,                         # NOVO
        model=model or None,
        year=year_val,
        chassis_number=chassis_number or None,
        acquisition_cost=acquisition_cost_dec,       # NOVO
        weekly_rent_default=weekly_rent_dec,
        status=status,
        notes=notes or None,
    )

    return JsonResponse(
        {"success": True, "message": "Viatura em leasing criada com sucesso."}
    )
