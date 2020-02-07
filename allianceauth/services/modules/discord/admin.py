from django.contrib import admin

from .models import DiscordUser
from ...admin import ServicesUserAdmin


class DiscordUserAdmin(ServicesUserAdmin):            
    list_display = ServicesUserAdmin.list_display + (        
        '_uid',        
    )    
   
    def _uid(self, obj):
        return obj.uid
    
    _uid.short_description = 'Discord ID (UID)'
    _uid.admin_order_field = 'uid'


admin.site.register(DiscordUser, DiscordUserAdmin)
