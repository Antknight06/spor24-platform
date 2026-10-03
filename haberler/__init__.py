import django.utils.html
import django.utils.safestring

_orig_format_html = django.utils.html.format_html

def _safe_format_html(format_string, *args, **kwargs):
    if not args and not kwargs:
        return django.utils.safestring.mark_safe(format_string)
    return _orig_format_html(format_string, *args, **kwargs)

django.utils.html.format_html = _safe_format_html
