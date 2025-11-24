from core.models import Member, AccountType, ClientAccount, CompanyAccount
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.shortcuts import render
from decimal import Decimal



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


#============================================================================================================
#============================================================================================================
def client_account_list(request):
    members = Member.objects.filter(is_active=True).order_by("first_name", "last_name")
    account_types = AccountType.objects.filter(is_active=True).order_by("id")
    accounts = (
        ClientAccount.objects.filter(is_active=True)
        .select_related("member", "account_type")
        .order_by("member__first_name", "member__last_name")
    )

    return render(
        request,
        "accounts/client_account_list.html",
        {
            "accounts": accounts,
            "members": members,
            "account_types": account_types,
        },
    )

#============================================================================================================
#============================================================================================================

@require_POST
def create_client_account(request):
    member_id = request.POST.get("member", "").strip()
    account_type_id = request.POST.get("account_type", "").strip()
    account_identifier = request.POST.get("account_identifier", "").strip()
    balance_raw = request.POST.get("balance", "").strip()

    if not member_id or not account_type_id or not account_identifier:
        return JsonResponse(
            {
                "success": False,
                "message": "Membro, tipo de conta e identificador são obrigatórios.",
            },
            status=400,
        )

    try:
        member = Member.objects.get(pk=member_id, is_active=True)
    except Member.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Membro inválido."},
            status=400,
        )

    try:
        account_type = AccountType.objects.get(pk=account_type_id, is_active=True)
    except AccountType.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Tipo de conta inválido."},
            status=400,
        )

    try:
        balance = float(balance_raw) if balance_raw else 0.0
    except ValueError:
        return JsonResponse(
            {"success": False, "message": "Saldo inválido."},
            status=400,
        )

    ClientAccount.objects.create(
        member=member,
        account_type=account_type,
        account_identifier=account_identifier,
        balance=balance,
        is_active=True,
    )

    return JsonResponse(
        {"success": True, "message": "Conta de cliente criada com sucesso."}
    )


#============================================================================================================
#============================================================================================================
def company_account_list(request):
    account_types = AccountType.objects.filter(is_active=True).order_by("id")
    accounts = (
        CompanyAccount.objects.filter(is_active=True)
        .select_related("account_type")
        .order_by("id")
    )

    return render(
        request,
        "accounts/company_account_list.html",
        {
            "accounts": accounts,
            "account_types": account_types,
        },
    )

#============================================================================================================
#============================================================================================================
@require_POST
def create_company_account(request):
    account_type_id = request.POST.get("account_type", "").strip()
    name = request.POST.get("name", "").strip()
    account_identifier = request.POST.get("account_identifier", "").strip()

    if not account_type_id or not name or not account_identifier:
        return JsonResponse(
            {
                "success": False,
                "message": "Tipo de conta, nome e identificador são obrigatórios.",
            },
            status=400,
        )

    try:
        account_type = AccountType.objects.get(pk=account_type_id, is_active=True)
    except AccountType.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Tipo de conta inválido."},
            status=400,
        )

    CompanyAccount.objects.create(
        account_type=account_type,
        name=name,
        account_identifier=account_identifier,
        is_active=True,
    )

    return JsonResponse(
        {"success": True, "message": "Conta da empresa criada com sucesso."}
    )

#============================================================================================================
#============================================================================================================
@require_POST
def update_company_account(request, account_id):
    try:
        account = CompanyAccount.objects.get(pk=account_id, is_active=True)
    except CompanyAccount.DoesNotExist:
        return JsonResponse({"success": False, "message": "Conta não encontrada."}, status=404)

    account_type_id = request.POST.get("account_type", "").strip()
    name = request.POST.get("name", "").strip()
    account_identifier = request.POST.get("account_identifier", "").strip()
    balance_raw = request.POST.get("balance", "").strip()

    if not account_type_id or not name or not account_identifier:
        return JsonResponse(
            {"success": False, "message": "Tipo de conta, nome e identificador são obrigatórios."},
            status=400,
        )

    try:
        acc_type = AccountType.objects.get(pk=account_type_id, is_active=True)
    except AccountType.DoesNotExist:
        return JsonResponse({"success": False, "message": "Tipo de conta inválido."}, status=400)

    try:
        balance = Decimal(str(balance_raw)) if balance_raw != "" else account.balance or Decimal("0")
    except Exception:
        return JsonResponse({"success": False, "message": "Saldo inválido."}, status=400)

    account.account_type = acc_type
    account.name = name
    account.account_identifier = account_identifier
    account.balance = balance
    account.save(update_fields=["account_type", "name", "account_identifier", "balance"])

    return JsonResponse({"success": True, "message": "Conta actualizada com sucesso."})


#============================================================================================================
#============================================================================================================
@require_POST
def deactivate_company_account(request, account_id):
    try:
        account = CompanyAccount.objects.get(pk=account_id, is_active=True)
    except CompanyAccount.DoesNotExist:
        return JsonResponse({"success": False, "message": "Conta não encontrada."}, status=404)

    account.is_active = False
    account.save(update_fields=["is_active"])

    return JsonResponse({"success": True, "message": "Conta desactivada com sucesso."})

#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================


#============================================================================================================
#============================================================================================================