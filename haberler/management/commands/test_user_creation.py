from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from haberler.models import UserProfile

class Command(BaseCommand):
    help = 'Test user creation'

    def handle(self, *args, **options):
        self.stdout.write('Testing user creation...')
        
        try:
            # Create a test user
            user = User.objects.create_user(
                username='test_yetkili', 
                email='test_yetkili@example.com', 
                password='testpass123'
            )
            user.first_name = 'Test'
            user.last_name = 'Yetkili'
            user.save()
            
            # Update the user profile
            profile = user.userprofile
            profile.user_type = 'yetkili'
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Success! User created: {user.username} with type: {profile.user_type}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            import traceback
            traceback.print_exc()