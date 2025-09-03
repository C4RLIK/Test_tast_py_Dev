from django.shortcuts import render
from django.http import HttpResponse
from .models import export_player_levels_csv

def index(request):
    """Главная страница"""
    return HttpResponse("Добро пожаловать в систему бонусов!")

def download_report(request):
    """Страница для скачивания отчета"""
    return export_player_levels_csv()

def admin_dashboard(request):
    """Простая админ-панель"""
    from .models import Player, Level, PlayerLevel
    stats = {
        'total_players': Player.objects.count(),
        'total_levels': Level.objects.count(),
        'completed_levels': PlayerLevel.objects.filter(is_completed=True).count(),
    }
    return render(request, 'admin_dashboard.html', {'stats': stats})