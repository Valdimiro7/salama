from core.models import Member, AccountType 
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render


#============================================================================================================
#============================================================================================================
def account_type_list(request):
    account_types = AccountType.objects.filter(is_active=True).order_by("id")
    return render(
        request,
        "accounts/account_type_list.html",
        {"account_types": account_types},
    )

#============================================================================================================
#============================================================================================================

@require_POST
def create_account_type(request):
    category = request.POST.get("category", "").strip()
    name = request.POST.get("name", "").strip()

    if not category or not name:
        return JsonResponse(
            {"success": False, "message": "Categoria e nome são obrigatórios."},
            status=400,
        )

    if category not in ["cash", "mobile", "bank"]:
        return JsonResponse(
            {"success": False, "message": "Categoria inválida."},
            status=400,
        )

    account_type = AccountType.objects.create(
        category=category,
        name=name,
        is_active=True,
    )

    return JsonResponse(
        {
            "success": True,
            "message": "Tipo de conta criado com sucesso.",
            "id": account_type.id,
        }
    )
