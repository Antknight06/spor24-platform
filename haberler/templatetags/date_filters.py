from django import template
from django.utils import timezone
from datetime import datetime, timedelta
import locale

register = template.Library()

@register.filter
def smart_date(value):
    """
    Smart date filter that handles both past and future dates appropriately
    """
    if not value:
        return ""
    
    # Make sure we're working with a timezone-aware datetime
    if timezone.is_aware(value):
        now = timezone.now()
    else:
        now = timezone.make_aware(datetime.now())
        if timezone.is_naive(value):
            value = timezone.make_aware(value)
    
    # Calculate time difference
    diff = now - value
    
    # If the article is from the future (future date), show the actual date
    if diff.total_seconds() < 0:
        # Format: "27 Ekim 2025"
        try:
            # Try to set Turkish locale for month names
            try:
                locale.setlocale(locale.LC_TIME, 'tr_TR.UTF-8')
            except:
                pass
            
            # Turkish month names
            turkish_months = {
                1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
                5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
                9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
            }
            
            day = value.day
            month = turkish_months.get(value.month, value.strftime('%B'))
            year = value.year
            
            return f"{day} {month} {year}"
            
        except:
            # Fallback to standard date format
            return value.strftime('%d.%m.%Y')
    
    # For past dates, use relative time
    total_seconds = diff.total_seconds()
    
    if total_seconds < 60:  # Less than 1 minute
        return "Az önce"
    elif total_seconds < 3600:  # Less than 1 hour
        minutes = int(total_seconds // 60)
        return f"{minutes} dk önce"
    elif total_seconds < 86400:  # Less than 1 day
        hours = int(total_seconds // 3600)
        return f"{hours} saat önce"
    elif total_seconds < 604800:  # Less than 1 week
        days = int(total_seconds // 86400)
        return f"{days} gün önce"
    else:
        # For older dates, show the actual date
        try:
            turkish_months = {
                1: 'Ocak', 2: 'Şubat', 3: 'Mart', 4: 'Nisan',
                5: 'Mayıs', 6: 'Haziran', 7: 'Temmuz', 8: 'Ağustos',
                9: 'Eylül', 10: 'Ekim', 11: 'Kasım', 12: 'Aralık'
            }
            
            day = value.day
            month = turkish_months.get(value.month, value.strftime('%B'))
            year = value.year
            
            return f"{day} {month} {year}"
            
        except:
            return value.strftime('%d.%m.%Y')