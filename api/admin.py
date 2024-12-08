from django.contrib import admin
from api.models import User, Place, Review, Favourite
from django.contrib.auth.admin import UserAdmin

class UserModelAdmin(UserAdmin):
    list_display = ('id', 'email', 'username','is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        ('User Credentials', {'fields': ('email', 'password',)}),
        ('Personal info', {'fields': ('username',)}),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username','password'),
        }),
    )
    search_fields = ('email', 'username',)
    ordering = ('email', 'id',)
    filter_horizontal = ()

admin.site.register(User, UserModelAdmin)
admin.site.register([Place, Review, Favourite])


