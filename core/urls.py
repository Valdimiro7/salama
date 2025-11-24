from django.urls import path
from core.views.dashboard_view import dashboard_view
from core.views.member.member_view import add_member, member_list, update_member, deactivate_member
from core.views.account.account_view import account_type_list, create_account_type

app_name = "core"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("members/add/", add_member, name="add_member"),
    path("members/list/", member_list, name="member_list"),
    path("members/<int:member_id>/update/", update_member, name="update_member"),
    path("members/<int:member_id>/deactivate/", deactivate_member, name="deactivate_member"),
    
    
    
    # Tipos de Contas
    path("accounts/types/", account_type_list, name="account_type_list"),
    path("accounts/types/create/", create_account_type, name="create_account_type"),
]