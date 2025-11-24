from django.urls import path
from core.views.dashboard_view import dashboard_view
from core.views.member.member_view import add_member, member_list, update_member, deactivate_member
from core.views.account.account_view import account_type_list, create_account_type
from core.views.account.account_view import client_account_list, create_client_account
from core.views.account.account_view import company_account_list, create_company_account

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
    
        # Contas do Cliente
    path("accounts/client/", client_account_list, name="client_account_list"),
    path("accounts/client/create/", create_client_account, name="create_client_account"),

    # Contas da Empresa
    path("accounts/company/", company_account_list, name="company_account_list"),
    path("accounts/company/create/", create_company_account, name="create_company_account"),
]