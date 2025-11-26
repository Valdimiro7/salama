from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


#===================================================================================================
#===================================================================================================
def staff_required(view_func):
    """
    Apenas staff/superuser podem gerir utilizadores.
    """
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and (u.is_staff or u.is_superuser)
    )(view_func)
    return decorated_view_func

#===================================================================================================
#===================================================================================================
@login_required
@staff_required
def user_list(request):
    """
    Lista de todos os utilizadores, com info de grupos e superuser.
    """
    users = (
        User.objects
        .prefetch_related("groups")
        .order_by("username")
    )
    groups = Group.objects.all().order_by("name")

    context = {
        "users": users,
        "groups": groups,
        "segment": "users",
    }
    return render(request, "user/user_list.html", context)

#===================================================================================================
#===================================================================================================
@login_required
@staff_required
@require_POST
def toggle_user_active(request, user_id):
    """
    Activa/desactiva utilizador.
    Impede desactivar a si próprio.
    """
    user = get_object_or_404(User, pk=user_id)

    if request.user.id == user.id:
        return JsonResponse(
            {
                "success": False,
                "message": "Não pode desactivar a sua própria conta."
            },
            status=400,
        )

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])

    return JsonResponse(
        {
            "success": True,
            "is_active": user.is_active,
            "message": "Utilizador activado." if user.is_active else "Utilizador desactivado.",
        }
    )
#===================================================================================================
#===================================================================================================
@login_required
@staff_required
@require_POST
def update_user_groups(request, user_id):
    """
    Actualiza a lista de grupos de um utilizador.
    Substitui pelos grupos seleccionados no modal.
    """
    user = get_object_or_404(User, pk=user_id)

    group_ids = request.POST.getlist("groups[]", [])
    groups = Group.objects.filter(id__in=group_ids)

    user.groups.set(groups)

    return JsonResponse(
        {
            "success": True,
            "message": "Grupos actualizados com sucesso.",
        }
    )
#===================================================================================================
#===================================================================================================
@login_required
@staff_required
@require_POST
def create_user(request):
    """
    Cria um novo utilizador via AJAX.
    Apenas staff/superuser.
    """
    username = (request.POST.get("username") or "").strip()
    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()
    email = (request.POST.get("email") or "").strip()
    password1 = request.POST.get("password1") or ""
    password2 = request.POST.get("password2") or ""
    is_staff = request.POST.get("is_staff") == "1"
    is_superuser = request.POST.get("is_superuser") == "1"
    group_ids = request.POST.getlist("groups[]", [])

    # Validações básicas
    if not username:
        return JsonResponse(
            {"success": False, "message": "O nome de utilizador é obrigatório."},
            status=400,
        )

    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {"success": False, "message": "Já existe um utilizador com este username."},
            status=400,
        )

    if password1 != password2:
        return JsonResponse(
            {"success": False, "message": "As palavras-passe não coincidem."},
            status=400,
        )

    if len(password1) < 6:
        return JsonResponse(
            {"success": False, "message": "A palavra-passe deve ter pelo menos 6 caracteres."},
            status=400,
        )

    if email:
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse(
                {"success": False, "message": "Email inválido."},
                status=400,
            )

    # Criação do utilizador
    user = User.objects.create_user(
        username=username,
        email=email or None,
        password=password1,
    )
    user.first_name = first_name
    user.last_name = last_name
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.is_active = True
    user.save()

    # Associa grupos, se existirem
    if group_ids:
        groups = Group.objects.filter(id__in=group_ids)
        user.groups.set(groups)

    return JsonResponse(
        {
            "success": True,
            "message": "Utilizador criado com sucesso.",
        }
    )
#===================================================================================================
#===================================================================================================


#===================================================================================================
#===================================================================================================


#===================================================================================================
#===================================================================================================


#===================================================================================================
#===================================================================================================


#===================================================================================================
#===================================================================================================


#===================================================================================================
#===================================================================================================