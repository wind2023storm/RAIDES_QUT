from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# from .forms import UserCreationForm, UserChangeForm
from .models import User


class UserAdmin(UserAdmin):
    # add_form = UserCreationForm
    # form = UserChangeForm
    model = User
    list_display = ('email', 'first_name', 'last_name','company','is_staff', 'is_active', 'is_superuser')
    list_filter = ('email', 'first_name', 'last_name', 'company', 'is_staff', 'is_active', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'first_name', 'last_name','company', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name','company', 'password1', 'password2', 'is_staff', 'is_active', 'is_superuser')}
        ),
    )
    search_fields = ('email', 'first_name', 'last_name','company',)
    ordering = ('email',)


admin.site.register(User, UserAdmin)
