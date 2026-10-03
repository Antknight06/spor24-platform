from django.core.management.base import BaseCommand
from django.utils.text import slugify
from haberler.models import Haber

class Command(BaseCommand):
    help = 'Fixes news items that have empty slugs by generating proper slugs from their titles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without actually making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find all news items with empty slugs
        empty_slug_news = Haber.objects.filter(slug='')
        
        if not empty_slug_news.exists():
            self.stdout.write(
                self.style.SUCCESS('✅ No news items with empty slugs found.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'⚠️  Found {empty_slug_news.count()} news items with empty slugs')
        )
        
        fixed_count = 0
        
        for news_item in empty_slug_news:
            # Generate a slug from the title
            new_slug = slugify(news_item.baslik)
            
            # Ensure uniqueness
            base_slug = new_slug
            counter = 1
            while Haber.objects.filter(slug=new_slug).exclude(id=news_item.id).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            
            if dry_run:
                self.stdout.write(
                    f'   Would fix: ID {news_item.id} "{news_item.baslik}" -> "{new_slug}"'
                )
            else:
                # Update the slug
                news_item.slug = new_slug
                news_item.save()
                self.stdout.write(
                    f'   Fixed: ID {news_item.id} "{news_item.baslik}" -> "{new_slug}"'
                )
                fixed_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'ℹ️  Would fix {empty_slug_news.count()} news items (dry run)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully fixed {fixed_count} news items')
            )