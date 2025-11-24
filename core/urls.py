from django.urls import path
from core.views.dashboard_view import dashboard_view
from core.views.member.member_view import add_member, member_list, update_member, deactivate_member

app_name = "core"

urlpatterns = [
    path("", dashboard_view, name="dashboard"),
    path("members/add/", add_member, name="add_member"),
    path("members/list/", member_list, name="member_list"),
    path("members/<int:member_id>/update/", update_member, name="update_member"),
    path("members/<int:member_id>/deactivate/", deactivate_member, name="deactivate_member"),
]