from django.contrib import admin
from .models import Player, Level, Prize, PlayerLevel, LevelPrize

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['player_id']
    search_fields = ['player_id']

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['title', 'order']
    list_filter = ['order']
    ordering = ['order']

@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ['title']
    search_fields = ['title']

@admin.register(PlayerLevel)
class PlayerLevelAdmin(admin.ModelAdmin):
    list_display = ['player', 'level', 'is_completed', 'completed', 'score']
    list_filter = ['is_completed', 'completed']
    search_fields = ['player__player_id', 'level__title']
    readonly_fields = ['completed']

@admin.register(LevelPrize)
class LevelPrizeAdmin(admin.ModelAdmin):
    list_display = ['level', 'prize', 'received']
    list_filter = ['received']
    search_fields = ['level__title', 'prize__title']
    readonly_fields = ['received']