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
)
from django.views.decorators.http import require_POST
import os
from django.http import JsonResponse, FileResponse, Http404

#============================================================================================================
#============================================================================================================

def expense_category_list(request):
    categories = ExpenseCategory.objects.filter(is_active=True).order_by("name")
    return render(
        request,
        "expenses/expense_category_list.html",
        {"categories": categories},
    )
#============================================================================================================
#============================================================================================================

@require_POST
def create_expense_category(request):
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()

    if not name:
        return JsonResponse(
            {"success": False, "message": "Nome da categoria é obrigatório."},
            status=400,
        )

    ExpenseCategory.objects.create(
        name=name,
        description=description or None,
        is_active=True,
    )

    return JsonResponse(
        {"success": True, "message": "Categoria de despesa criada com sucesso."}
    )

#============================================================================================================
#============================================================================================================
def expense_list(request):
    categories = ExpenseCategory.objects.filter(is_active=True).order_by("name")
    company_accounts = CompanyAccount.objects.filter(is_active=True).order_by("name")

    expenses = (
        Expense.objects.filter(is_active=True)
        .select_related("category", "company_account")
        .order_by("-expense_date", "-id")
    )

    return render(
        request,
        "expenses/expense_list.html",
        {
            "categories": categories,
            "company_accounts": company_accounts,
            "expenses": expenses,
        },
    )


#============================================================================================================
#============================================================================================================
@require_POST
def create_expense(request):
    category_id = request.POST.get("category", "").strip()
    company_account_id = request.POST.get("company_account", "").strip()
    expense_date = request.POST.get("expense_date", "").strip()
    description = request.POST.get("description", "").strip()
    amount_raw = request.POST.get("amount", "").strip()
    attachment_file = request.FILES.get("attachment")  # NOVO

    if not category_id or not company_account_id or not expense_date or not description or not amount_raw:
        return JsonResponse(
            {
                "success": False,
                "message": "Categoria, conta da empresa, data, descrição e valor são obrigatórios.",
            },
            status=400,
        )

    try:
        category = ExpenseCategory.objects.get(pk=category_id, is_active=True)
    except ExpenseCategory.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Categoria inválida."},
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

    # Validar formato da data (YYYY-MM-DD)
    try:
        timezone.datetime.strptime(expense_date, "%Y-%m-%d")
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Data inválida."},
            status=400,
        )

    # Criar despesa com/sem anexo
    expense = Expense(
        category=category,
        company_account=company_account,
        expense_date=expense_date,
        description=description,
        amount=amount,
        is_active=True,
        created_at=timezone.now(),
    )

    if attachment_file:
        expense.attachment = attachment_file

    expense.save()

    # Deduzir saldo da conta da empresa
    company_account.balance = (company_account.balance or Decimal("0")) - amount
    company_account.save(update_fields=["balance"])

    return JsonResponse(
        {"success": True, "message": "Despesa registada e saldo deduzido com sucesso."}
    )




#============================================================================================================
#============================================================================================================


def download_expense_attachment(request, expense_id):
    try:
        expense = Expense.objects.get(pk=expense_id, is_active=True)
    except Expense.DoesNotExist:
        raise Http404("Despesa não encontrada.")

    if not expense.attachment:
        raise Http404("Nenhum anexo disponível para esta despesa.")

    # Usa o storage do próprio FileField
    file_handle = expense.attachment.open("rb")
    filename = os.path.basename(expense.attachment.name)

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