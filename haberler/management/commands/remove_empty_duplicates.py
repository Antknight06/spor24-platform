from django.core.management.base import BaseCommand
from haberler.models import Haber
from django.db.models import Count

class Command(BaseCommand):
    help = 'Remove duplicate news articles that have empty content'

    def handle(self, *args, **options):
        self.stdout.write("Searching for duplicate news articles...")
        
        # Find duplicate titles
        duplicates = Haber.objects.values('baslik').annotate(count=Count('baslik')).filter(count__gt=1)
        
        self.stdout.write(f"Found {len(duplicates)} duplicate titles")
        
        removed_count = 0
        
        for duplicate in duplicates:
            title = duplicate['baslik']
            count = duplicate['count']
            
            # Get all articles with this title
            articles = Haber.objects.filter(baslik=title).order_by('olusturma_tarihi')
            
            # Find articles with empty content
            empty_content_articles = [article for article in articles if not article.icerik.strip()]
            
            self.stdout.write(f"Title: {title}")
            self.stdout.write(f"Total articles: {count}")
            self.stdout.write(f"Articles with empty content: {len(empty_content_articles)}")
            
            # Remove articles with empty content
            for article in empty_content_articles:
                self.stdout.write(f"Removing article ID {article.id} with empty content")
                article.delete()
                removed_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nRemoved {removed_count} duplicate articles with empty content"
            )
        )