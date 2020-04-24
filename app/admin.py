from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import Request, User, Message, Conversation, Review
# Register your models here.
admin.site.register(Request)
admin.site.register(User)
admin.site.register(Message)
admin.site.register(Conversation)
admin.site.register(Review)

'''
* REFERENCES
* Title: How to use email as username for Django authentication
* Author: Federico Jaramillo
* Date: May 10, 2017
* URL: https://www.fomfus.com/articles/how-to-use-email-as-username-for-django-authentication-removing-the-username
'''
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (('Personal info'), {'fields': ('first_name', 'last_name')}),
        (('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)