from django.db import models
import csv
from django.http import HttpResponse
from django.db.models import Case, When, BooleanField
from django.utils import timezone

class Player(models.Model):
    player_id = models.CharField(max_length=100, unique=True, verbose_name='ID игрока')
    
    class Meta:
        verbose_name = 'Игрок'
        verbose_name_plural = 'Игроки'
    
    def __str__(self):
        return self.player_id


class Level(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название уровня')
    order = models.IntegerField(default=0, verbose_name='Порядок уровня')
    
    class Meta:
        verbose_name = 'Уровень'
        verbose_name_plural = 'Уровни'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.order}. {self.title}"


class Prize(models.Model):
    title = models.CharField(max_length=100, verbose_name='Название приза')
    
    class Meta:
        verbose_name = 'Приз'
        verbose_name_plural = 'Призы'
    
    def __str__(self):
        return self.title


class PlayerLevel(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, verbose_name='Игрок')
    level = models.ForeignKey(Level, on_delete=models.CASCADE, verbose_name='Уровень')
    completed = models.DateField(null=True, blank=True, verbose_name='Дата завершения')
    is_completed = models.BooleanField(default=False, verbose_name='Завершен')
    score = models.PositiveIntegerField(default=0, verbose_name='Счет')
    
    class Meta:
        verbose_name = 'Прохождение уровня'
        verbose_name_plural = 'Прохождения уровней'
        unique_together = ['player', 'level']
    
    def __str__(self):
        status = "Завершен" if self.is_completed else "Не завершен"
        return f"{self.player} - {self.level} ({status})"
    
    def complete_level(self, score=0):
        """Отметить уровень как завершенный"""
        self.is_completed = True
        self.completed = timezone.now().date()
        self.score = score
        self.save()
        
        # Автоматически присваиваем приз за уровень
        self._assign_prize()
    
    def _assign_prize(self):
        """Присвоить приз за прохождение уровня"""
        level_prizes = LevelPrize.objects.filter(level=self.level)
        for level_prize in level_prizes:
            level_prize.received = self.completed
            level_prize.save()


class LevelPrize(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, verbose_name='Уровень')
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE, verbose_name='Приз')
    received = models.DateField(null=True, blank=True, verbose_name='Дата получения')
    
    class Meta:
        verbose_name = 'Приз за уровень'
        verbose_name_plural = 'Призы за уровни'
        unique_together = ['level', 'prize']
    
    def __str__(self):
        status = "Получен" if self.received else "Не получен"
        return f"{self.level} - {self.prize} ({status})"


# Функции для выгрузки в CSV
def export_player_levels_csv():
    """Выгрузка данных в CSV с правильной кодировкой UTF-8 с BOM"""
    
    # Оптимизированный запрос
    player_levels = PlayerLevel.objects.select_related(
        'player', 'level'
    ).prefetch_related(
        'level__levelprize_set'
    ).annotate(
        prize_received=Case(
            When(level__levelprize__received__isnull=False, then=True),
            default=False,
            output_field=BooleanField()
        )
    ).order_by('player__player_id', 'level__order')
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')  # UTF-8 с BOM
    response['Content-Disposition'] = 'attachment; filename="player_levels_report.csv"'
    
    # Создаем CSV writer с правильными настройками
    response.write('\ufeff')  # Добавляем BOM для Excel
    writer = csv.writer(response)
    
    # Заголовки с русскими названиями
    writer.writerow([
        'player_id', 
        'level_name', 
        'level_complete', 
        'prize_reserved'
    ])
    
    for player_level in player_levels.iterator(chunk_size=1000):
        writer.writerow([
            player_level.player.player_id,
            player_level.level.title,
            'true' if player_level.is_completed else 'false',
            'true' if player_level.prize_received else 'false'
        ])
    
    return response
