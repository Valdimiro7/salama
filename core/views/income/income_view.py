from decimal import Decimal
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.utils import timezone
from decimal import Decimal
from django.shortcuts import render, redirect
from core.models import (
    Member,
    AccountType,
    ClientAccount,
    CompanyAccount,
    ExpenseCategory,
    Expense,
    IncomeCategory,
    Income,
    Transaction,
)
import os
from django.http import JsonResponse, FileResponse, Http404


#============================================================================================================
#============================================================================================================
def income_category_list(request):
    categories = IncomeCategory.objects.filter(is_active=True).order_by("name")
    return render(
        request,
        "incomes/income_category_list.html",
        {"categories": categories},
    )

#============================================================================================================
#============================================================================================================
@require_POST
def create_income_category(request):
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()

    if not name:
        return JsonResponse(
            {"success": False, "message": "Nome do tipo de rendimento é obrigatório."},
            status=400,
        )

    IncomeCategory.objects.create(
        name=name,
        description=description or None,
        is_active=True,
    )

    return JsonResponse(
        {"success": True, "message": "Tipo de rendimento criado com sucesso."}
    )
#============================================================================================================
#============================================================================================================
def income_list(request):
    categories = IncomeCategory.objects.filter(is_active=True).order_by("name")
    company_accounts = CompanyAccount.objects.filter(is_active=True).order_by("name")

    incomes = (
        Income.objects.filter(is_active=True)
        .select_related("category", "company_account")
        .order_by("-income_date", "-id")
    )

    return render(
        request,
        "incomes/income_list.html",
        {
            "categories": categories,
            "company_accounts": company_accounts,
            "incomes": incomes,
        },
    )


#============================================================================================================
#============================================================================================================
@require_POST
def create_income(request):
    category_id = request.POST.get("category", "").strip()
    company_account_id = request.POST.get("company_account", "").strip()
    income_date = request.POST.get("income_date", "").strip()
    description = request.POST.get("description", "").strip()
    amount_raw = request.POST.get("amount", "").strip()
    attachment_file = request.FILES.get("attachment")

    if not category_id or not company_account_id or not income_date or not description or not amount_raw:
        return JsonResponse(
            {
                "success": False,
                "message": "Categoria, conta da empresa, data, descrição e valor são obrigatórios.",
            },
            status=400,
        )

    try:
        category = IncomeCategory.objects.get(pk=category_id, is_active=True)
    except IncomeCategory.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Categoria de rendimento inválida."},
            status=400,
        )

    try:
        company_account = CompanyAccount.objects.get(pk=company_account_id, is_active=True)
    except CompanyAccount.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Conta da empresa inválida."},
            status=400,
        )

    try:
        amount = Decimal(str(amount_raw))
    except Exception:
        return JsonResponse(
            {"success": False, "message": "Valor inválido."},
            status=400,
        )

    # Validar formato da data
    try:
        timezone.datetime.strptime(income_date, "%Y-%m-%d")
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Data inválida."},
            status=400,
        )

    # Saldo antes
    old_balance = company_account.balance or Decimal("0")
    new_balance = old_balance + amount

    # Criar rendimento
    income = Income(
        category=category,
        company_account=company_account,
        income_date=income_date,
        description=description,
        amount=amount,
        is_active=True,
        created_at=timezone.now(),
    )
    if attachment_file:
        income.attachment = attachment_file
    income.save()

    # Actualizar saldo
    company_account.balance = new_balance
    company_account.save(update_fields=["balance"])

    # Criar transacção (entrada)
    Transaction.objects.create(
        company_account=company_account,
        tx_type=Transaction.TX_TYPE_IN,
        source_type="income",
        source_id=income.id,
        tx_date=income_date,
        description=f"Rendimento: {description}",
        amount=amount,
        balance_before=old_balance,
        balance_after=new_balance,
        is_active=True,
        created_at=timezone.now(),
    )

    return JsonResponse(
        {"success": True, "message": "Rendimento registado, saldo creditado e transacção criada com sucesso."}
    )



#============================================================================================================
#============================================================================================================

def download_income_attachment(request, income_id):
    try:
        income = Income.objects.get(pk=income_id, is_active=True)
    except Income.DoesNotExist:
        raise Http404("Rendimento não encontrado.")

    if not income.attachment:
        raise Http404("Nenhum anexo disponível para este rendimento.")

    file_handle = income.attachment.open("rb")
    filename = os.path.basename(income.attachment.name)

    response = FileResponse(file_handle, as_attachment=True, filename=filename)
    return response

#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================