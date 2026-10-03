from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.functions import Concat
from django.db.models import Value

class EmailBackend(ModelBackend):
    """
    Universal authentication backend that allows ALL users (Admin, Yetkili, Kose Yazari, Abone)
    to log in using EITHER their Username, Full Name (Display Name), OR their Email address seamlessly.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        
        username = username.strip()
        
        # 1. Try matching by username (exact or case-insensitive)
        user = User.objects.filter(username__iexact=username).first()
        
        # 2. If not found, try matching by email
        if not user:
            user = User.objects.filter(email__iexact=username).first()
            
        # 3. If still not found, try matching full name (first_name + ' ' + last_name)
        if not user and ' ' in username:
            user = User.objects.annotate(
                full_name=Concat('first_name', Value(' '), 'last_name')
            ).filter(full_name__iexact=username).first()
            
        # 4. If still not found, try simple split
        if not user and ' ' in username:
            parts = username.split(None, 1)
            user = User.objects.filter(first_name__iexact=parts[0], last_name__iexact=parts[1]).first()
            
        # 5. Legacy alias support for merged accounts
        if not user and username.lower() == 'malatyaspo44@gmail.com':
            user = User.objects.filter(id=65).first()
            
        if user and user.check_password(password):
            return user
            
        return None

    def get_user(self, user_id):
        return super().get_user(user_id)
