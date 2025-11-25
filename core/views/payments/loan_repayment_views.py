from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import (
    Loan,
    LoanRepayment,
    CompanyAccount,
    Transaction,
)

#=================================================================================================
#=================================================================================================

@login_required
def loan_repayment_list(request):
    """
    Lista empréstimos com status 'disbursed' e mostra:
    - principal em dívida
    - juros do período (usando interest_type.rate)
    - saldo em dívida = principal em dívida + juros do período
    """

    loans_qs = (
        Loan.objects
        .select_related("member", "loan_type", "interest_type", "approved_by")
        .prefetch_related("repayments", "repayments__company_account")
        .filter(status="disbursed")
        .order_by("-id")
    )

    loans = list(loans_qs)

    total_loans = len(loans)
    total_principal_all = Decimal("0")
    total_outstanding_all = Decimal("0")  # saldo em dívida (principal + juros)

    for loan in loans:
        total_principal_all += loan.principal_amount

        # principal já pago
        agg = loan.repayments.aggregate(total_principal=Sum("principal_amount"))
        principal_paid = agg["total_principal"] or Decimal("0")
        outstanding_principal = loan.principal_amount - principal_paid
        if outstanding_principal < 0:
            outstanding_principal = Decimal("0")

        loan.outstanding_principal = outstanding_principal

        # taxa de juros do período (ex: 3.0000 => 3%)
        rate = loan.interest_type.rate if loan.interest_type and loan.interest_type.rate else Decimal("0")
        rate_decimal = (rate / Decimal("100")).quantize(Decimal("0.0001"))

        # juros do período sobre o principal em dívida
        interest_due = (outstanding_principal * rate_decimal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        loan.period_interest_due = interest_due
        loan.outstanding_with_interest = outstanding_principal + interest_due

        total_outstanding_all += loan.outstanding_with_interest

        # último pagamento
        last_rep = loan.repayments.order_by("-payment_date", "-id").first()
        loan.last_repayment = last_rep

    context = {
        "loans": loans,
        "kpi_total_loans": total_loans,
        "kpi_total_principal": total_principal_all,
        "kpi_total_outstanding": total_outstanding_all,  # já inclui juros
        "kpi_avg_outstanding": (total_outstanding_all / total_loans) if total_loans else Decimal("0"),
        "company_accounts": CompanyAccount.objects.filter(is_active=True).order_by("name"),
    }
    return render(request, "payments/loan_repayment_list.html", context)

#=================================================================================================
#=================================================================================================
@login_required
@require_POST
@db_transaction.atomic
def register_repayment(request, loan_id):
    """
    Regista um reembolso de empréstimo seguindo a regra:
    - juros do período = (rate do InterestType / 100) * principal em dívida
    - pagamento cobre primeiro juros, depois amortiza principal
    - actualiza saldo da conta da empresa (entrada)
    - cria Transaction (IN, source_type='loan_repayment')
    - se principal em dívida chegar a 0, fecha o empréstimo (status='closed')
    """

    loan = get_object_or_404(
        Loan.objects.select_related("member", "interest_type"),
        pk=loan_id,
        status="disbursed",
    )

    company_account_id = request.POST.get("company_account", "").strip()
    payment_date_str = request.POST.get("payment_date", "").strip()
    amount_raw = request.POST.get("amount", "").strip()
    method = request.POST.get("method", "cash").strip()
    notes = request.POST.get("notes", "").strip()
    attachment = request.FILES.get("attachment")

    # Conta da empresa (entrada)
    if not company_account_id:
        return JsonResponse(
            {"success": False, "message": "Selecione a conta da empresa que recebe o pagamento."},
            status=400,
        )
    try:
        account = CompanyAccount.objects.get(pk=company_account_id, is_active=True)
    except CompanyAccount.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Conta da empresa inválida."},
            status=400,
        )

    # Data
    if not payment_date_str:
        return JsonResponse(
            {"success": False, "message": "Informe a data de pagamento."},
            status=400,
        )
    try:
        payment_date = datetime.strptime(payment_date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Data de pagamento inválida."},
            status=400,
        )

    # Valor
    if not amount_raw:
        return JsonResponse(
            {"success": False, "message": "Informe o valor do pagamento."},
            status=400,
        )
    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            raise ValueError
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Valor do pagamento inválido."},
            status=400,
        )

    # Calcular principal em dívida
    agg = loan.repayments.aggregate(total_principal=Sum("principal_amount"))
    principal_paid = agg["total_principal"] or Decimal("0")
    outstanding_principal = loan.principal_amount - principal_paid
    if outstanding_principal <= 0:
        return JsonResponse(
            {"success": False, "message": "Este empréstimo não tem saldo em dívida."},
            status=400,
        )

    # taxa de juros do período (ex: 3.0000 => 3%)
    rate = loan.interest_type.rate if loan.interest_type and loan.interest_type.rate else Decimal("0")
    rate_decimal = (rate / Decimal("100")).quantize(Decimal("0.0001"))

    # juros do período com base no principal em dívida
    interest_due = (outstanding_principal * rate_decimal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    max_total = outstanding_principal + interest_due  # “saldo em dívida” deste ciclo

    if amount > max_total:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    f"O valor introduzido ({amount}) é superior ao saldo em dívida deste ciclo "
                    f"(principal {outstanding_principal} + juros {interest_due} = {max_total})."
                ),
            },
            status=400,
        )

    # Composição do pagamento: primeiro juros, depois principal
    if amount <= interest_due:
        interest_amount = amount
        principal_amount = Decimal("0.00")
    else:
        interest_amount = interest_due
        principal_amount = amount - interest_amount

    principal_balance_after = outstanding_principal - principal_amount
    if principal_balance_after < 0:
        principal_balance_after = Decimal("0.00")

    # Criar LoanRepayment
    repayment = LoanRepayment.objects.create(
        loan=loan,
        member=loan.member,
        company_account=account,
        payment_date=payment_date,
        amount=amount,
        interest_amount=interest_amount,
        principal_amount=principal_amount,
        principal_balance_after=principal_balance_after,
        method=method,
        attachment=attachment,
        notes=notes or None,
    )

    # Actualizar saldo da conta da empresa (entrada)
    old_balance = account.balance or Decimal("0")
    account.balance = old_balance + amount
    account.save(update_fields=["balance"])
    new_balance = account.balance

    # Criar Transaction (entrada)
    descricao = (
        f"Reembolso de empréstimo (Loan #{loan.id}) "
        f"de {loan.member.first_name} {loan.member.last_name} "
        f"- Juros: {interest_amount} · Principal: {principal_amount}"
    )

    Transaction.objects.create(
        company_account=account,
        tx_type=Transaction.TX_TYPE_IN,
        source_type="loan_repayment",
        source_id=repayment.id,
        tx_date=payment_date,
        description=descricao,
        amount=amount,
        balance_before=old_balance,
        balance_after=new_balance,
        is_active=True,
        created_at=timezone.now(),
    )

    # Se principal em dívida chegou a zero, fechar empréstimo
    if principal_balance_after <= 0:
        loan.status = "closed"
        loan.save(update_fields=["status"])

    return JsonResponse(
        {
            "success": True,
            "message": (
                "Pagamento registado com sucesso. "
                f"Juros pagos: {interest_amount}, principal amortizado: {principal_amount}, "
                f"saldo em dívida (principal) após pagamento: {principal_balance_after}."
            ),
        }
    )

#=================================================================================================
#=================================================================================================


#=================================================================================================
#=================================================================================================


#=================================================================================================
#=================================================================================================


#=================================================================================================
#=================================================================================================


#=================================================================================================
#=================================================================================================


#=================================================================================================
#=================================================================================================


#=================================================================================================
#=================================================================================================


#=================================================================================================
#=================================================================================================