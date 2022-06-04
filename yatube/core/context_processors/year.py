from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    this_year = timezone.now()
    return {'year': this_year.year}
