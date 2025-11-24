from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Member, LoanType, InterestType, CompanyAccount, Loan, LoanGuarantor, LoanGuarantee, Transaction, LoanPaymentRequest

#============================================================================================================
#============================================================================================================

def loan_payment_requests_list(request):
    prs = (
        LoanPaymentRequest.objects
        .select_related("loan", "member", "company_account")
        .order_by("-due_date", "-id")
    )
    company_accounts = CompanyAccount.objects.filter(is_active=True).order_by("name")
    context = {
        "payment_requests": prs,
        "company_accounts": company_accounts,
    }
    return render(request, "payments/loan_payment_requests_list.html", context)

#============================================================================================================
#============================================================================================================
@require_POST
def mark_loan_payment_paid(request, pr_id):
    try:
        pr = LoanPaymentRequest.objects.select_related("loan", "member", "company_account").get(pk=pr_id)
    except LoanPaymentRequest.DoesNotExist:
        return JsonResponse({"success": False, "message": "Pedido de pagamento não encontrado."}, status=404)

    if pr.status == "paid":
        return JsonResponse({"success": False, "message": "Este pedido já foi marcado como pago."}, status=400)

    company_account_id = request.POST.get("company_account", "").strip()
    paid_date_str = request.POST.get("paid_date", "").strip()
    amount_raw = request.POST.get("amount_paid", "").strip()
    attachment = request.FILES.get("attachment")

    if not company_account_id or not paid_date_str or not amount_raw:
        return JsonResponse(
            {"success": False, "message": "Conta, data de pagamento e valor são obrigatórios."},
            status=400,
        )

    try:
        account = CompanyAccount.objects.get(pk=company_account_id, is_active=True)
    except CompanyAccount.DoesNotExist:
        return JsonResponse({"success": False, "message": "Conta da empresa inválida."}, status=400)

    try:
        paid_date = datetime.strptime(paid_date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"success": False, "message": "Data de pagamento inválida."}, status=400)

    try:
        amount = Decimal(str(amount_raw))
    except Exception:
        return JsonResponse({"success": False, "message": "Valor inválido."}, status=400)

    # Actualizar pedido
    from django.utils import timezone as dj_tz
    pr.company_account = account
    pr.amount_paid = amount
    pr.status = "paid"
    if attachment:
        pr.attachment = attachment
    pr.paid_at = dj_tz.now()
    pr.save(update_fields=["company_account", "amount_paid", "status", "attachment", "paid_at"])

    # Actualizar saldo da conta + criar transacção (entrada)
    old_balance = account.balance or Decimal("0")
    account.balance = old_balance + amount
    account.save(update_fields=["balance"])

    Transaction.objects.create(
        trans_date=paid_date,
        company_account=account,
        member=pr.member,
        amount=amount,
        direction="in",   # entrada de dinheiro
        source="loan_payment",
        reference=f"Loan #{pr.loan_id}",
        description=f"Pagamento de empréstimo do membro {pr.member.first_name} {pr.member.last_name}",
    )

    return JsonResponse({"success": True, "message": "Pagamento registado e transacção criada com sucesso."})

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