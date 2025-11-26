from decimal import Decimal
from datetime import date, datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from core.models import (
    TukTuk,
    TukTukLeaseContract,
    TukTukLeasePayment,
    CompanyAccount,
    Member,
    Transaction,
)

#========================================================================================================================
#========================================================================================================================

@login_required
def tuktuk_list(request):
    """
    Lista de Txopelas (frota) + modal para criar nova Txopela.
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
        "segment": "txopela_fleet",
    }
    return render(request, "tuktuk/tuktuk_list.html", context)

#========================================================================================================================
#========================================================================================================================
@login_required
def tuktuk_lease_contract_list(request):
    """
    Lista de contratos de leasing de Txopelas + modal para novo contrato.
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
    kpi_tuktuks_in_leasing = (
        contracts.filter(status="active")
        .values("tuktuk_id")
        .distinct()
        .count()
    )

    # Para o modal de novo contrato:
    available_tuktuks = TukTuk.objects.filter(status="available").order_by("plate_number")
    drivers = Member.objects.filter(is_active=True).order_by("first_name", "last_name")
    company_accounts = CompanyAccount.objects.filter(is_active=True).order_by("name")

    context = {
        "contracts": contracts,
        "kpi_total": kpi_total,
        "kpi_active": kpi_active,
        "kpi_weekly_sum": kpi_weekly_sum,
        "kpi_tuktuks_in_leasing": kpi_tuktuks_in_leasing,
        "available_tuktuks": available_tuktuks,
        "drivers": drivers,
        "company_accounts": company_accounts,
        "segment": "txopela_contracts",
    }
    return render(request, "tuktuk/tuktuk_contract_list.html", context)

#========================================================================================================================
#========================================================================================================================
@login_required
@db_transaction.atomic
def create_tuktuk(request):
    """
    Cria uma nova Txopela (via AJAX).
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método inválido."}, status=405)

    plate_number = request.POST.get("plate_number", "").strip()
    model = request.POST.get("model", "").strip()
    year = request.POST.get("year", "").strip()
    chassis_number = request.POST.get("chassis_number", "").strip()
    weekly_rent = request.POST.get("weekly_rent_default", "").strip() or "0"
    status = request.POST.get("status", "available").strip() or "available"
    notes = request.POST.get("notes", "").strip()

    if not plate_number:
        return JsonResponse(
            {"success": False, "message": "Informe a matrícula da Txopela."},
            status=400,
        )

    # validar valor
    try:
        weekly_rent_dec = Decimal(str(weekly_rent))
        if weekly_rent_dec < 0:
            raise ValueError
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Valor de renda semanal inválido."},
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
    TukTuk.objects.create(
        plate_number=plate_number,
        model=model or None,
        year=year_val,
        chassis_number=chassis_number or None,
        weekly_rent_default=weekly_rent_dec,
        status=status,
        notes=notes or None,
    )

    return JsonResponse(
        {"success": True, "message": "Txopela criada com sucesso."}
    )

#========================================================================================================================
#========================================================================================================================
@login_required
@db_transaction.atomic
def create_tuktuk_lease_contract(request):
    """
    Cria um novo contrato de leasing de Txopela (via AJAX).
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método inválido."}, status=405)

    tuktuk_id = request.POST.get("tuktuk", "").strip()
    driver_id = request.POST.get("driver", "").strip()
    company_account_id = request.POST.get("company_account", "").strip()
    start_date_str = request.POST.get("start_date", "").strip()
    end_date_str = request.POST.get("end_date", "").strip()
    weekly_rent_raw = request.POST.get("weekly_rent", "").strip()
    payment_weekday_raw = request.POST.get("payment_weekday", "").strip()
    notes = request.POST.get("notes", "").strip()

    if not tuktuk_id or not driver_id or not company_account_id or not start_date_str or not weekly_rent_raw:
        return JsonResponse(
            {
                "success": False,
                "message": "Preencha Txopela, motorista, conta, data de início e renda semanal.",
            },
            status=400,
        )

    # validar / obter entidades
    tuktuk = get_object_or_404(TukTuk, pk=tuktuk_id)
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

    # dia de pagamento (opcional)
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

    contract = TukTukLeaseContract.objects.create(
        tuktuk=tuktuk,
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

    # opcionalmente marcar Txopela como leased
    tuktuk.status = "leased"
    tuktuk.save(update_fields=["status"])

    return JsonResponse(
        {"success": True, "message": f"Contrato #{contract.id} criado com sucesso."}
    )

#========================================================================================================================
#========================================================================================================================

@login_required
def tuktuk_lease_payment_list(request):
    """
    Lista de pagamentos de leasing de Txopelas +
    modal para registar novo pagamento.
    """

    # Todos pagamentos, sem filtro de status
    payments = (
        TukTukLeasePayment.objects
        .select_related(
            "contract",
            "contract__tuktuk",
            "contract__driver",
            "company_account",
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

    # Contratos activos (para o modal de registo de pagamento)
    active_contracts = (
        TukTukLeaseContract.objects
        .select_related("tuktuk", "driver")
        .filter(status="active")
        .order_by("tuktuk__plate_number")
    )

    company_accounts = CompanyAccount.objects.filter(is_active=True).order_by("name")

    context = {
        "payments": payments,
        "kpi_total_pagamentos": kpi_total_pagamentos,
        "kpi_total_valor": kpi_total_valor,
        "kpi_total_mes": kpi_total_mes,
        "active_contracts": active_contracts,
        "company_accounts": company_accounts,
        "segment": "txopela_payments",
        "today": today,
    }
    return render(request, "tuktuk/tuktuk_lease_payment_list.html", context)

#========================================================================================================================
#========================================================================================================================
@login_required
@db_transaction.atomic
def create_tuktuk_lease_payment(request):
    """
    Regista um pagamento de leasing de Txopela (via AJAX).
    Cria movimento de entrada na conta da empresa + Transaction.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método inválido."}, status=405)

    contract_id = request.POST.get("contract", "").strip()
    company_account_id = request.POST.get("company_account", "").strip()
    payment_date_str = request.POST.get("payment_date", "").strip()
    amount_raw = request.POST.get("amount", "").strip()
    method = request.POST.get("method", "").strip() or "bank"
    notes = request.POST.get("notes", "").strip()

    if not contract_id or not company_account_id or not payment_date_str or not amount_raw:
        return JsonResponse(
            {
                "success": False,
                "message": "Preencha contrato, conta da empresa, data e valor.",
            },
            status=400,
        )

    contract = get_object_or_404(TukTukLeaseContract, pk=contract_id)
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

    # Saldo antes (antes de somar o pagamento)
    balance_before = company_account.balance
    balance_after = balance_before + amount

    # Criar pagamento (agora com driver)
    payment = TukTukLeasePayment.objects.create(
        contract=contract,
        driver=contract.driver,
        company_account=company_account,
        payment_date=payment_date,
        amount=amount,
        method=method,
        notes=notes or None,
    )

    # Actualizar saldo da conta da empresa
    company_account.balance = balance_after
    company_account.save(update_fields=["balance"])

    # Registar transacção (entrada)
    Transaction.objects.create(
        company_account=company_account,
        tx_type=Transaction.TX_TYPE_IN,          # "IN"
        source_type="tuktuk_lease_payment",
        source_id=payment.id,
        tx_date=payment_date,
        description=f"Leasing Txopela · Contrato #{contract.id} · {contract.tuktuk.plate_number}",
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        is_active=True,
        created_at=timezone.now(),
    )

    return JsonResponse(
        {"success": True, "message": "Pagamento de leasing registado com sucesso."}
    )

#========================================================================================================================
#========================================================================================================================
