from django.utils import timezone
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
from django.http import JsonResponse

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
    expenses = (
        Expense.objects.filter(is_active=True)
        .select_related("category")
        .order_by("-expense_date", "-id")
    )
    return render(
        request,
        "expenses/expense_list.html",
        {
            "categories": categories,
            "expenses": expenses,
        },
    )

#============================================================================================================
#============================================================================================================
@require_POST
def create_expense(request):
    category_id = request.POST.get("category", "").strip()
    expense_date = request.POST.get("expense_date", "").strip()
    description = request.POST.get("description", "").strip()
    amount_raw = request.POST.get("amount", "").strip()

    if not category_id or not expense_date or not description or not amount_raw:
        return JsonResponse(
            {
                "success": False,
                "message": "Categoria, data, descrição e valor são obrigatórios.",
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
        amount = float(amount_raw)
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Valor inválido."},
            status=400,
        )

    try:
        # valida formato da data (YYYY-MM-DD)
        timezone.datetime.strptime(expense_date, "%Y-%m-%d")
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Data inválida."},
            status=400,
        )

    Expense.objects.create(
        category=category,
        expense_date=expense_date,
        description=description,
        amount=amount,
        is_active=True,
        created_at=timezone.now(),
    )

    return JsonResponse(
        {"success": True, "message": "Despesa registada com sucesso."}
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