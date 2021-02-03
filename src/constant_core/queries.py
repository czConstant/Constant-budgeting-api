from constant_core.models import AdminPermissions


class BackendQuery:
    @staticmethod
    def check_admin_permission(user_id, page_name):
        qs = AdminPermissions.objects.raw('''
select p.page_id as id, p.page_id, 
    max(p.can_view) as can_view, 
    max(p.can_add) as can_add, 
    max(p.can_update) as can_update, 
    max(p.can_delete) as can_delete
from admin_permissions p
join admin_user_groups ug on p.group_id = p.group_id
join admin_pages pg on pg.id = p.page_id
where ug.user_id = %(user_id)s and pg.name = %(page_name)s
group by p.page_id
''', {'user_id': user_id, 'page_name': page_name})

        return qs
