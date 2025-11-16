from django.contrib import admin
from .models import GoogleUser

# Register your models here.

@admin.register(GoogleUser)
class GoogleUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'google_email', 'google_id', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'google_email', 'google_id']
    readonly_fields = ['google_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('사용자 정보', {
            'fields': ('user',)
        }),
        ('구글 계정 정보', {
            'fields': ('google_id', 'google_email', 'picture')
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # 수정 모드
            return self.readonly_fields + ['user']
        return self.readonly_fields
