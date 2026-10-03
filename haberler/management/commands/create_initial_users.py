from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from haberler.models import UserProfile

class Command(BaseCommand):
    help = 'Create initial users with different roles for the ANT News system'

    def handle(self, *args, **options):
        # Create admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@antnews.com',
                password='admin123',
                is_staff=True,
                is_superuser=True
            )
            # Create or update user profile
            try:
                admin_profile = admin_user.userprofile
                admin_profile.user_type = 'admin'
            except UserProfile.DoesNotExist:
                admin_profile = UserProfile.objects.create(
                    user=admin_user,
                    user_type='admin'
                )
            admin_profile.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully created admin user: admin / admin123')
            )
        else:
            self.stdout.write('Admin user already exists')

        # Create yetkili user
        if not User.objects.filter(username='yetkili').exists():
            yetkili_user = User.objects.create_user(
                username='yetkili',
                email='yetkili@antnews.com',
                password='yetkili123'
            )
            # Create or update user profile
            try:
                yetkili_profile = yetkili_user.userprofile
                yetkili_profile.user_type = 'yetkili'
            except UserProfile.DoesNotExist:
                yetkili_profile = UserProfile.objects.create(
                    user=yetkili_user,
                    user_type='yetkili'
                )
            yetkili_profile.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully created yetkili user: yetkili / yetkili123')
            )
        else:
            self.stdout.write('Yetkili user already exists')

        # Create abone user
        if not User.objects.filter(username='abone').exists():
            abone_user = User.objects.create_user(
                username='abone',
                email='abone@antnews.com',
                password='abone123'
            )
            # Create or update user profile
            try:
                abone_profile = abone_user.userprofile
                abone_profile.user_type = 'abone'
            except UserProfile.DoesNotExist:
                abone_profile = UserProfile.objects.create(
                    user=abone_user,
                    user_type='abone'
                )
            abone_profile.save()
            self.stdout.write(
                self.style.SUCCESS('Successfully created abone user: abone / abone123')
            )
        else:
            self.stdout.write('Abone user already exists')

        self.stdout.write(
            self.style.SUCCESS('Initial users creation completed!')
        )