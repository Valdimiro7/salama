from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from core.models import (
    Loan,
    LoanDisbursement,
    CompanyAccount,
    Transaction,
)

#============================================================================================================
#============================================================================================================
@login_required
def loan_disbursement_list(request):
    """
    Lista empréstimos aprovados (status='approved') e respectivos desembolsos (se existirem).
    Apenas empréstimos aprovados aparecem aqui para poderem ser desembolsados.
    """
    loans = (
        Loan.objects
        .select_related("member", "loan_type")
        .prefetch_related("disbursements", "disbursements__company_account")
        .filter(status="approved")
        .order_by("-id")
    )
    company_accounts = CompanyAccount.objects.filter(is_active=True).order_by("name")

    context = {
        "loans": loans,
        "company_accounts": company_accounts,
    }
    return render(request, "payments/loan_disbursement_list.html", context)

#============================================================================================================
#============================================================================================================
@login_required
@require_POST
@db_transaction.atomic
def register_disbursement(request, loan_id):
    """
    Regista o desembolso de um empréstimo:
    - verifica saldo disponível na conta da empresa
    - cria LoanDisbursement
    - cria Transaction (saída)
    - actualiza saldo da conta da empresa
    - muda Loan.status para 'disbursed'
    """
    # Buscar o empréstimo
    loan = get_object_or_404(
        Loan.objects.select_related("member"),
        pk=loan_id
    )

    # Apenas empréstimos aprovados podem ser desembolsados
    if loan.status != "approved":
        return JsonResponse(
            {"success": False, "message": "Apenas empréstimos aprovados podem ser desembolsados."},
            status=400,
        )

    # Se só permitires um desembolso por empréstimo:
    if loan.disbursements.exists():
        return JsonResponse(
            {"success": False, "message": "Este empréstimo já foi desembolsado."},
            status=400,
        )

    # Ler dados do POST
    company_account_id = request.POST.get("company_account", "").strip()
    disburse_date_str = request.POST.get("disburse_date", "").strip()
    amount_raw = request.POST.get("amount", "").strip()
    method = request.POST.get("method", "cash").strip()
    notes = request.POST.get("notes", "").strip()
    attachment = request.FILES.get("attachment")

    # === Validar conta da empresa ===
    if not company_account_id:
        return JsonResponse(
            {"success": False, "message": "Selecione a conta da empresa para o desembolso."},
            status=400,
        )
    try:
        account = CompanyAccount.objects.get(pk=company_account_id, is_active=True)
    except CompanyAccount.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Conta da empresa inválida."},
            status=400,
        )

    # === Validar data do desembolso ===
    if not disburse_date_str:
        return JsonResponse(
            {"success": False, "message": "Informe a data de desembolso."},
            status=400,
        )
    try:
        disburse_date = datetime.strptime(disburse_date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Data de desembolso inválida."},
            status=400,
        )

    # === Validar valor ===
    if not amount_raw:
        return JsonResponse(
            {"success": False, "message": "Informe o valor de desembolso."},
            status=400,
        )
    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            raise ValueError
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Valor de desembolso inválido."},
            status=400,
        )

    # === Verificar saldo disponível antes de criar qualquer coisa ===
    current_balance = account.balance or Decimal("0")

    if amount > current_balance:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Saldo insuficiente na conta seleccionada para efectuar este desembolso. "
                    "Por favor registe primeiro uma entrada de saldo (depósito/crédito) "
                    "na conta da empresa antes de desembolsar."
                ),
            },
            status=400,
        )

    # === Criar registo de desembolso ===
    disb = LoanDisbursement.objects.create(
        loan=loan,
        member=loan.member,
        company_account=account,
        disburse_date=disburse_date,
        amount=amount,
        method=method,
        attachment=attachment,
        notes=notes or None,
    )

    # === Actualizar saldo da conta (saída) ===
    old_balance = current_balance
    account.balance = old_balance - amount
    account.save(update_fields=["balance"])
    new_balance = account.balance

    # === Criar transacção respeitando o modelo Transaction ===
    Transaction.objects.create(
        company_account=account,
        tx_type=Transaction.TX_TYPE_OUT,          # "OUT" (saída)
        source_type="loan_disbursement",          # ORIGEM: Desembolso de Empréstimo
        source_id=disb.id,                        # referência ao desembolso
        tx_date=disburse_date,
        description=(
            f"Desembolso de empréstimo (Loan #{loan.id}) "
            f"para {loan.member.first_name} {loan.member.last_name}"
        ),
        amount=amount,
        balance_before=old_balance,
        balance_after=new_balance,
        is_active=True,
        created_at=timezone.now(),
    )

    # === Actualizar status do empréstimo ===
    loan.status = "disbursed"
    loan.save(update_fields=["status"])

    return JsonResponse(
        {"success": True, "message": "Desembolso registado com sucesso."}
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


#============================================================================================================
#============================================================================================================