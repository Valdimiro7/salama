from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from core.models import Member
from django.urls import reverse
from django.http import JsonResponse


def add_member(request):
    User = get_user_model()
    gestores = User.objects.filter(is_active=True).order_by("first_name", "last_name")

    errors = {}
    form_data = {}

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        legal_name = request.POST.get("legal_name", "").strip()
        is_company = request.POST.get("is_company") == "on"
        phone = request.POST.get("phone", "").strip()
        alt_phone = request.POST.get("alt_phone", "").strip()
        email = request.POST.get("email", "").strip()
        city = request.POST.get("city", "").strip()
        address = request.POST.get("address", "").strip()
        profession = request.POST.get("profession", "").strip()
        marital_status = request.POST.get("marital_status", "").strip()
        gender = request.POST.get("gender", "").strip()
        manager_id = request.POST.get("manager", "").strip()

        form_data = {
            "first_name": first_name,
            "last_name": last_name,
            "legal_name": legal_name,
            "is_company": is_company,
            "phone": phone,
            "alt_phone": alt_phone,
            "email": email,
            "city": city,
            "address": address,
            "profession": profession,
            "marital_status": marital_status,
            "gender": gender,
            "manager": manager_id,
        }

        if not first_name:
            errors["first_name"] = "Nome é obrigatório."
        if not last_name:
            errors["last_name"] = "Apelido é obrigatório."
        if not phone:
            errors["phone"] = "Telefone é obrigatório."
        if not manager_id:
            errors["manager"] = "Selecione o gestor responsável."

        manager = None
        if manager_id:
            try:
                manager = gestores.get(pk=manager_id)
            except User.DoesNotExist:
                errors["manager"] = "Gestor inválido."

        if not errors and manager is not None:
            Member.objects.create(
                first_name=first_name,
                last_name=last_name,
                legal_name=legal_name or None,
                is_company=is_company,
                phone=phone,
                alt_phone=alt_phone or None,
                email=email or None,
                city=city or None,
                address=address or None,
                profession=profession or None,
                marital_status=marital_status or None,
                gender=gender or None,
                manager=manager,
            )

            # Redirect para Lista de Membros com flag ?created=1
            url = reverse("core:member_list")
            return redirect(f"{url}?created=1")

    return render(
        request,
        "member/add_member.html",
        {"gestores": gestores, "errors": errors, "form_data": form_data},
    )


#============================================================================================================
#============================================================================================================
def member_list(request):
    User = get_user_model()
    gestores = User.objects.filter(is_active=True).order_by("first_name", "last_name")
    members = Member.objects.filter(is_active=True).order_by("-id")
    return render(
        request,
        "member/list_members.html",
        {
            "members": members,
            "gestores": gestores,
        },
    )

#============================================================================================================
#============================================================================================================
def update_member(request, member_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método inválido."}, status=405)

    try:
        member = Member.objects.get(pk=member_id, is_active=True)
    except Member.DoesNotExist:
        return JsonResponse({"success": False, "message": "Membro não encontrado."}, status=404)

    User = get_user_model()
    gestores = User.objects.filter(is_active=True)

    first_name = request.POST.get("first_name", "").strip()
    last_name = request.POST.get("last_name", "").strip()
    legal_name = request.POST.get("legal_name", "").strip()
    is_company = request.POST.get("is_company") == "on"
    phone = request.POST.get("phone", "").strip()
    alt_phone = request.POST.get("alt_phone", "").strip()
    email = request.POST.get("email", "").strip()
    city = request.POST.get("city", "").strip()
    address = request.POST.get("address", "").strip()
    profession = request.POST.get("profession", "").strip()
    marital_status = request.POST.get("marital_status", "").strip()
    gender = request.POST.get("gender", "").strip()
    manager_id = request.POST.get("manager", "").strip()

    if not first_name or not last_name or not phone or not manager_id:
        return JsonResponse(
            {
                "success": False,
                "message": "Nome, apelido, telefone e gestor são obrigatórios.",
            },
            status=400,
        )

    try:
        manager = gestores.get(pk=manager_id)
    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "Gestor inválido."}, status=400)

    member.first_name = first_name
    member.last_name = last_name
    member.legal_name = legal_name or None
    member.is_company = is_company
    member.phone = phone
    member.alt_phone = alt_phone or None
    member.email = email or None
    member.city = city or None
    member.address = address or None
    member.profession = profession or None
    member.marital_status = marital_status or None
    member.gender = gender or None
    member.manager = manager
    member.save(update_fields=[
        "first_name", "last_name", "legal_name", "is_company", "phone",
        "alt_phone", "email", "city", "address", "profession",
        "marital_status", "gender", "manager"
    ])

    return JsonResponse({"success": True, "message": "Membro actualizado com sucesso."})




#============================================================================================================
#============================================================================================================
def deactivate_member(request, member_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Método inválido."}, status=405)

    try:
        member = Member.objects.get(pk=member_id, is_active=True)
    except Member.DoesNotExist:
        return JsonResponse({"success": False, "message": "Membro não encontrado."}, status=404)

    member.is_active = False
    member.save(update_fields=["is_active"])

    return JsonResponse({"success": True, "message": "Membro desactivado com sucesso."})




#============================================================================================================
#============================================================================================================




#============================================================================================================
#============================================================================================================