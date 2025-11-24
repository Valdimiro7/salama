from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal

from core.models import InterestType


#============================================================================================================
#============================================================================================================
def interest_type_list(request):
    interest_types = InterestType.objects.filter(is_active=True).order_by("name")
    return render(
        request,
        "interest/interest_type_list.html",
        {"interest_types": interest_types},
    )


#============================================================================================================
#============================================================================================================
@require_POST
def create_interest_type(request):
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    rate_raw = request.POST.get("rate", "").strip()
    period_type = request.POST.get("period_type", "").strip()
    calculation_method = request.POST.get("calculation_method", "flat").strip() or "flat"

    if not name or not rate_raw or not period_type:
        return JsonResponse(
            {
                "success": False,
                "message": "Nome, taxa e tipo de período são obrigatórios.",
            },
            status=400,
        )

    if period_type not in ("monthly", "daily"):
        return JsonResponse(
            {"success": False, "message": "Tipo de período inválido."},
            status=400,
        )

    try:
        rate = Decimal(str(rate_raw))
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Taxa de juro inválida."},
            status=400,
        )

    InterestType.objects.create(
        name=name,
        description=description or None,
        rate=rate,
        period_type=period_type,
        calculation_method=calculation_method,
        is_active=True,
    )

    return JsonResponse(
        {"success": True, "message": "Tipo de juro criado com sucesso."}
    )


#============================================================================================================
#============================================================================================================
def interest_calculator(request):
    interest_types = InterestType.objects.filter(is_active=True).order_by("name")
    return render(
        request,
        "interest/interest_calculator.html",
        {"interest_types": interest_types},
    )



#============================================================================================================
#============================================================================================================



#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================



#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================