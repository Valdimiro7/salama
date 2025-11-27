
from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from core.models import (
    VehicleLeaseContract,
    VehicleLeasePayment,
    CompanyAccount,
    Transaction,
)


@login_required
def vehicle_lease_payment_list(request):
    """
    Lista de pagamentos de leasing de veículos +
    modal para registar novo pagamento.
    """

    payments = (
        VehicleLeasePayment.objects
        .select_related(
            "contract",
            "contract__leased_vehicle",
            "contract__driver",
            "company_account",
            "created_by",
        )
        .order_by("-payment_date", "-id")
    )

    # KPIs
    kpi_total_pagamentos = payments.count()
    kpi_total_valor = payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    today = date.today()
    primeiro_dia_mes = today.replace(day=1)
    pagamentos_mes = payments.filter(payment_date__gte=primeiro_dia_mes)
    kpi_total_mes = pagamentos_mes.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    active_contracts = (
        VehicleLeaseContract.objects
        .select_related("leased_vehicle", "driver")
        .filter(status="active")
        .order_by("leased_vehicle__plate_number")
    )

    company_accounts = CompanyAccount.objects.filter(is_active=True).order_by("name")

    context = {
        "payments": payments,
        "kpi_total_pagamentos": kpi_total_pagamentos,
        "kpi_total_valor": kpi_total_valor,
        "kpi_total_mes": kpi_total_mes,
        "active_contracts": active_contracts,
        "company_accounts": company_accounts,
        "segment": "vehicle_lease_payments",
        "today": today,
    }
    return render(request, "leasing/vehicle_lease_payment_list.html", context)


# ======================================================================================================================
# ======================================================================================================================

@login_required
@db_transaction.atomic
def create_vehicle_lease_payment(request):
    """
    Regista um pagamento de leasing de viatura (via AJAX).
    Cria movimento de entrada na conta da empresa + Transaction.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método inválido."}, status=405)

    contract_id = request.POST.get("contract", "").strip()
    company_account_id = request.POST.get("company_account", "").strip()
    payment_date_str = request.POST.get("payment_date", "").strip()
    amount_raw = request.POST.get("amount", "").strip()
    method = request.POST.get("method", "").strip() or "bank_transfer"
    notes = request.POST.get("notes", "").strip()

    if not contract_id or not company_account_id or not payment_date_str or not amount_raw:
        return JsonResponse(
            {
                "success": False,
                "message": "Preencha contrato, conta da empresa, data e valor.",
            },
            status=400,
        )

    contract = get_object_or_404(VehicleLeaseContract, pk=contract_id)
    company_account = get_object_or_404(
        CompanyAccount,
        pk=company_account_id,
        is_active=True,
    )

    # data
    try:
        payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Data de pagamento inválida."},
            status=400,
        )

    # valor
    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            raise ValueError
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Valor inválido."},
            status=400,
        )

    # saldo antes
    balance_before = company_account.balance
    balance_after = balance_before + amount

    # pagamento
    payment = VehicleLeasePayment.objects.create(
        contract=contract,
        driver=contract.driver,
        company_account=company_account,
        payment_date=payment_date,
        amount=amount,
        method=method,
        notes=notes or None,
        created_by=request.user,  # <<< AQUI
    )

    # actualizar saldo
    company_account.balance = balance_after
    company_account.save(update_fields=["balance"])

    # registar transacção
    Transaction.objects.create(
        company_account=company_account,
        tx_type=Transaction.TX_TYPE_IN,
        source_type="vehicle_lease_payment",
        source_id=payment.id,
        tx_date=payment_date,
        description=(
            f"Leasing Viatura · Contrato #{contract.id} · "
            f"{contract.leased_vehicle.plate_number}"
        ),
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        is_active=True,
        created_at=timezone.now(),
        created_by=request.user,  # se já tens o campo criado em Transaction
    )

    return JsonResponse(
        {"success": True, "message": "Pagamento de leasing registado com sucesso."}
    )