from datetime import datetime


def year(request):
    date_year = datetime.now().year
    """Добавляет переменную с текущим годом."""
    return {
        'year': date_year
    }
