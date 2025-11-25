from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.db import transaction as db_transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from core.models import (
    TukTuk,
    TukTukLeaseContract,
    TukTukLeasePayment,
    CompanyAccount,
    Transaction,
)


#========================================================================================================================
#========================================================================================================================

@login_required
def tuktuk_list(request):
    """
    Lista de Tuk-Tuk (frota).
    """
    tuktuks = TukTuk.objects.all().order_by("plate_number")

    kpi_total = tuktuks.count()
    kpi_available = tuktuks.filter(status="available").count()
    kpi_leased = tuktuks.filter(status="leased").count()
    kpi_maintenance = tuktuks.filter(status="maintenance").count()

    context = {
        "tuktuks": tuktuks,
        "kpi_total": kpi_total,
        "kpi_available": kpi_available,
        "kpi_leased": kpi_leased,
        "kpi_maintenance": kpi_maintenance,
    }
    return render(request, "tuktuk/tuktuk_list.html", context)

#========================================================================================================================
#========================================================================================================================

@login_required
def tuktuk_lease_contract_list(request):
    """
    Lista de contratos de leasing Tuk-Tuk.
    """
    contracts = (
        TukTukLeaseContract.objects
        .select_related("tuktuk", "driver", "company_account")
        .order_by("-id")
    )

    # KPIs
    kpi_total = contracts.count()
    kpi_active = contracts.filter(status="active").count()
    kpi_weekly_sum = contracts.filter(status="active").aggregate(
        total=Sum("weekly_rent")
    )["total"] or Decimal("0")
    kpi_tuktuks_in_leasing = contracts.filter(status="active").values("tuktuk_id").distinct().count()

    context = {
        "contracts": contracts,
        "kpi_total": kpi_total,
        "kpi_active": kpi_active,
        "kpi_weekly_sum": kpi_weekly_sum,
        "kpi_tuktuks_in_leasing": kpi_tuktuks_in_leasing,
    }
    return render(request, "tuktuk/tuktuk_contract_list.html", context)

#========================================================================================================================
#========================================================================================================================
@login_required
def tuktuk_lease_payment_list(request):
    """
    Lista de pagamentos semanais de leasing de Tuk-Tuk.
    """
    payments = (
        TukTukLeasePayment.objects
        .select_related("contract", "driver", "company_account", "contract__tuktuk")
        .order_by("-payment_date", "-id")
    )

    contracts = (
        TukTukLeaseContract.objects
        .select_related("tuktuk", "driver")
        .filter(status="active")
        .order_by("-id")
    )

    company_accounts = CompanyAccount.objects.filter(is_active=True).order_by("name")

    today = date.today()
    start_week = today - timedelta(days=today.weekday())  # segunda
    start_month = today.replace(day=1)

    kpi_week_total = payments.filter(payment_date__gte=start_week).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    kpi_month_total = payments.filter(payment_date__gte=start_month).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    kpi_payments_count_week = (
        payments.filter(payment_date__gte=start_week).count()
    )

    context = {
        "payments": payments,
        "contracts": contracts,
        "company_accounts": company_accounts,
        "kpi_week_total": kpi_week_total,
        "kpi_month_total": kpi_month_total,
        "kpi_payments_count_week": kpi_payments_count_week,
        "today": today,
    }
    return render(request, "tuktuk/leasing_payment_list.html", context)

#========================================================================================================================
#========================================================================================================================

@login_required
@db_transaction.atomic
def register_tuktuk_lease_payment(request):
    """
    Regista um pagamento semanal de leasing de Tuk-Tuk:
    - cria TukTukLeasePayment
    - cria Transaction (IN)
    - actualiza saldo da conta da empresa
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método inválido."}, status=405)

    contract_id = request.POST.get("contract_id", "").strip()
    company_account_id = request.POST.get("company_account", "").strip()
    payment_date_str = request.POST.get("payment_date", "").strip()
    amount_raw = request.POST.get("amount", "").strip()
    method = request.POST.get("method", "cash").strip()
    notes = request.POST.get("notes", "").strip()
    attachment = request.FILES.get("attachment")

    contract = get_object_or_404(TukTukLeaseContract, pk=contract_id, status="active")
    driver = contract.driver

    try:
        account = CompanyAccount.objects.get(pk=company_account_id, is_active=True)
    except CompanyAccount.DoesNotExist:
        return JsonResponse({"success": False, "message": "Conta da empresa inválida."}, status=400)

    from datetime import datetime
    if not payment_date_str:
        return JsonResponse({"success": False, "message": "Informe a data do pagamento."}, status=400)
    try:
        payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"success": False, "message": "Data de pagamento inválida."}, status=400)

    if not amount_raw:
        return JsonResponse({"success": False, "message": "Informe o valor do pagamento."}, status=400)
    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            raise ValueError
    except Exception:
        return JsonResponse({"success": False, "message": "Valor do pagamento inválido."}, status=400)

    old_balance = account.balance or Decimal("0")

    pay = TukTukLeasePayment.objects.create(
        contract=contract,
        driver=driver,
        company_account=account,
        payment_date=payment_date,
        amount=amount,
        method=method,
        attachment=attachment,
        notes=notes or None,
    )

    # actualiza saldo (entrada)
    account.balance = old_balance + amount
    account.save(update_fields=["balance"])

    # regista transacção
    Transaction.objects.create(
        company_account=account,
        tx_type="IN",
        source_type="tuktuk_lease",
        source_id=pay.id,
        tx_date=payment_date,
        description=f"Pagamento leasing Tuk-Tuk · Contrato #{contract.id} · {driver.first_name} {driver.last_name}",
        amount=amount,
        balance_before=old_balance,
        balance_after=account.balance,
        is_active=True,
    )

    return JsonResponse({"success": True, "message": "Pagamento de leasing registado com sucesso."})

#========================================================================================================================
#========================================================================================================================

#========================================================================================================================
#========================================================================================================================


#========================================================================================================================
#========================================================================================================================


#========================================================================================================================
#========================================================================================================================


#========================================================================================================================
#========================================================================================================================