from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from daily_expenses_app import models


class UserAdmin(BaseUserAdmin):
    """Define the admin pages for users"""
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = (
        (
            None,
            {
                'fields': (
                    'email', 'name', 'region',
                    'password', 'last_email_sent_date'
                )
            }
        ),
        (
            _('Permissions'),
            {'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
            )
            }
        ),
        (_('Important dates'), {'fields': ('last_login',)})
    )
    readonly_fields = ['last_login']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2',
                'name',
                'region',
                'is_active',
                'is_staff',
                'is_superuser',

            )
        }),
    )


admin.site.register(models.UserProfile, UserAdmin)
admin.site.register(models.UserDailyExpenses)
admin.site.register(models.Category)
