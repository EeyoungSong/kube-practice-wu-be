from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class GoogleUser(models.Model):
    """
    구글 OAuth2로 인증된 사용자 정보를 저장하는 모델
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_user')
    google_id = models.CharField(max_length=100, unique=True, help_text="구글 계정 고유 ID")
    google_email = models.EmailField(help_text="구글 계정 이메일")
    picture = models.URLField(blank=True, null=True, help_text="구글 프로필 사진 URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "구글 사용자"
        verbose_name_plural = "구글 사용자들"

    def __str__(self):
        return f"{self.user.username} ({self.google_email})"
