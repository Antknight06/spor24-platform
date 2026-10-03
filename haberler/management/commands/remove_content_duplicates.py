from django.core.management.base import BaseCommand
from haberler.models import Haber
from django.db.models import Count

class Command(BaseCommand):
    help = 'Remove duplicate news articles based on title or image, keeping the ones with more content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        action_text = "Would delete" if dry_run else "Deleting"
        
        self.stdout.write(f"Searching for duplicate news articles based on title or image...")
        
        # Remove duplicates based on title
        removed_by_title = self.remove_duplicates_by_title(dry_run, action_text)
        
        # Remove duplicates based on image
        removed_by_image = self.remove_duplicates_by_image(dry_run, action_text)
        
        total_removed = removed_by_title + removed_by_image
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nWould remove {total_removed} duplicate articles "
                    f"({removed_by_title} by title, {removed_by_image} by image)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nRemoved {total_removed} duplicate articles "
                    f"({removed_by_title} by title, {removed_by_image} by image)"
                )
            )

    def remove_duplicates_by_title(self, dry_run, action_text):
        """Remove duplicate articles based on title, keeping the one with more content"""
        # Find duplicate titles
        duplicates = Haber.objects.values('baslik').annotate(count=Count('baslik')).filter(count__gt=1)
        
        self.stdout.write(f"Found {len(duplicates)} duplicate titles")
        
        removed_count = 0
        
        for duplicate in duplicates:
            title = duplicate['baslik']
            
            # Get all articles with this title, ordered by content length (descending)
            articles = Haber.objects.filter(baslik=title).order_by('-olusturma_tarihi')
            
            # Sort by content length (descending) to keep the one with most content
            articles_sorted = sorted(articles, key=lambda x: len(x.icerik), reverse=True)
            
            # Keep the first one (most content) and remove the rest
            articles_to_remove = articles_sorted[1:]
            
            self.stdout.write(f"Title: {title}")
            self.stdout.write(f"Total articles: {len(articles_sorted)}")
            self.stdout.write(f"Articles to remove: {len(articles_to_remove)}")
            
            for article in articles_to_remove:
                self.stdout.write(f"{action_text} article ID {article.id} with {len(article.icerik)} characters")
                if not dry_run:
                    article.delete()
                removed_count += 1
        
        return removed_count

    def remove_duplicates_by_image(self, dry_run, action_text):
        """Remove duplicate articles based on image, keeping the one with more content"""
        # Find articles with images
        articles_with_images = Haber.objects.exclude(resim='').exclude(resim__isnull=True)
        
        # Group by image path
        image_groups = {}
        for article in articles_with_images:
            image_path = article.resim.name
            if image_path not in image_groups:
                image_groups[image_path] = []
            image_groups[image_path].append(article)
        
        # Filter to only groups with duplicates
        duplicate_image_groups = {k: v for k, v in image_groups.items() if len(v) > 1}
        
        self.stdout.write(f"Found {len(duplicate_image_groups)} duplicate images")
        
        removed_count = 0
        
        for image_path, articles in duplicate_image_groups.items():
            # Sort by content length (descending) to keep the one with most content
            articles_sorted = sorted(articles, key=lambda x: len(x.icerik), reverse=True)
            
            # Keep the first one (most content) and remove the rest
            articles_to_remove = articles_sorted[1:]
            
            self.stdout.write(f"Image: {image_path}")
            self.stdout.write(f"Total articles: {len(articles_sorted)}")
            self.stdout.write(f"Articles to remove: {len(articles_to_remove)}")
            
            for article in articles_to_remove:
                self.stdout.write(f"{action_text} article ID {article.id} with {len(article.icerik)} characters")
                if not dry_run:
                    article.delete()
                removed_count += 1
        
        return removed_count