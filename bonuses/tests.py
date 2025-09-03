from django.test import TestCase
from django.http import HttpResponse
from bonuses.models import Player, Level, Prize, PlayerLevel, LevelPrize
from bonuses.models import export_player_levels_csv
import csv
from io import StringIO

class PlayerLevelSystemTests(TestCase):
    
    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем игроков
        self.player1 = Player.objects.create(player_id="user_001")
        self.player2 = Player.objects.create(player_id="user_002")
        
        # Создаем уровни
        self.level1 = Level.objects.create(title="Уровень 1", order=1)
        self.level2 = Level.objects.create(title="Уровень 2", order=2)
        self.level3 = Level.objects.create(title="Уровень 3", order=3)
        
        # Создаем призы
        self.prize1 = Prize.objects.create(title="Золотая монета")
        self.prize2 = Prize.objects.create(title="Серебряная монета")
        self.prize3 = Prize.objects.create(title="Бронзовая монета")
        
        # Связываем призы с уровнями
        self.level_prize1 = LevelPrize.objects.create(level=self.level1, prize=self.prize1)
        self.level_prize2 = LevelPrize.objects.create(level=self.level2, prize=self.prize2)
        # У уровня 3 нет приза
    
    def test_player_creation(self):
        """Тест создания игрока"""
        self.assertEqual(self.player1.player_id, "user_001")
        self.assertEqual(Player.objects.count(), 2)
    
    def test_level_creation(self):
        """Тест создания уровней"""
        self.assertEqual(self.level1.title, "Уровень 1")
        self.assertEqual(self.level1.order, 1)
        self.assertEqual(Level.objects.count(), 3)
    
    def test_prize_creation(self):
        """Тест создания призов"""
        self.assertEqual(self.prize1.title, "Золотая монета")
        self.assertEqual(Prize.objects.count(), 3)
    
    def test_level_prize_association(self):
        """Тест связи уровня и приза"""
        self.assertEqual(self.level_prize1.level, self.level1)
        self.assertEqual(self.level_prize1.prize, self.prize1)
        self.assertIsNone(self.level_prize1.received)
    
    def test_complete_level_with_prize(self):
        """Тест завершения уровня с призом"""
        # Игрок проходит уровень с призом
        player_level = PlayerLevel.objects.create(
            player=self.player1, 
            level=self.level1
        )
        player_level.complete_level(score=100)
        
        # Обновляем объекты из базы
        player_level.refresh_from_db()
        self.level_prize1.refresh_from_db()
        
        # Проверяем что уровень завершен
        self.assertTrue(player_level.is_completed)
        self.assertIsNotNone(player_level.completed)
        self.assertEqual(player_level.score, 100)
        
        # Проверяем что приз получен
        self.assertIsNotNone(self.level_prize1.received)
        self.assertEqual(self.level_prize1.received, player_level.completed)
    
    def test_complete_level_without_prize(self):
        """Тест завершения уровня без приза"""
        # Игрок проходит уровень без приза
        player_level = PlayerLevel.objects.create(
            player=self.player1, 
            level=self.level3  # У уровня 3 нет приза
        )
        player_level.complete_level(score=80)
        
        player_level.refresh_from_db()
        
        # Уровень должен быть завершен, но приза нет
        self.assertTrue(player_level.is_completed)
        self.assertIsNotNone(player_level.completed)
    
    def test_multiple_players_completing_levels(self):
        """Тест нескольких игроков, завершающих уровни"""
        # Игрок 1 проходит уровень 1
        pl1 = PlayerLevel.objects.create(player=self.player1, level=self.level1)
        pl1.complete_level(score=100)
        
        # Игрок 2 проходит уровень 1
        pl2 = PlayerLevel.objects.create(player=self.player2, level=self.level1)
        pl2.complete_level(score=90)
        
        # Игрок 1 проходит уровень 2
        pl3 = PlayerLevel.objects.create(player=self.player1, level=self.level2)
        pl3.complete_level(score=85)
        
        # Проверяем количество записей
        self.assertEqual(PlayerLevel.objects.count(), 3)
        self.assertEqual(PlayerLevel.objects.filter(is_completed=True).count(), 3)
    
    def test_csv_export_basic(self):
        """Тест базовой выгрузки CSV"""
        # Создаем тестовые данные
        pl1 = PlayerLevel.objects.create(player=self.player1, level=self.level1)
        pl1.complete_level(score=100)
        
        # Выгружаем CSV
        response = export_player_levels_csv()
        
        # Проверяем что это HTTP response с CSV
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        
        # Читаем CSV данные
        content = response.content.decode('utf-8')
        csv_data = list(csv.reader(StringIO(content)))
        
        # Проверяем заголовки
        self.assertEqual(csv_data[0], ['player_id', 'level_title', 'is_completed', 'prize_received'])
        
        # Проверяем данные
        self.assertEqual(len(csv_data), 2)  # Заголовок + 1 строка данных
        self.assertEqual(csv_data[1][0], 'user_001')
        self.assertEqual(csv_data[1][1], 'Уровень 1')
        self.assertEqual(csv_data[1][2], 'Да')
        self.assertEqual(csv_data[1][3], 'Да')
    
    def test_csv_export_with_incomplete_levels(self):
        """Тест выгрузки CSV с незавершенными уровнями"""
        # Игрок начинает уровень но не завершает
        PlayerLevel.objects.create(player=self.player1, level=self.level1)
        
        # Выгружаем CSV
        response = export_player_levels_csv()
        content = response.content.decode('utf-8')
        csv_data = list(csv.reader(StringIO(content)))
        
        # Ищем запись игрока
        player_row = None
        for row in csv_data[1:]:  # Пропускаем заголовок
            if row[0] == 'user_001':
                player_row = row
                break
        
        self.assertIsNotNone(player_row)
        self.assertEqual(player_row[2], 'Нет')  # is_completed = Нет
        self.assertEqual(player_row[3], 'Нет')  # prize_received = Нет
    
    def test_unique_constraints(self):
        """Тест уникальности связей"""
        # Нельзя создать два одинаковых прохождения уровня
        PlayerLevel.objects.create(player=self.player1, level=self.level1)
        
        with self.assertRaises(Exception):
            PlayerLevel.objects.create(player=self.player1, level=self.level1)
        
        # Нельзя создать два одинаковых приза для уровня
        with self.assertRaises(Exception):
            LevelPrize.objects.create(level=self.level1, prize=self.prize1)

class EdgeCaseTests(TestCase):
    """Тесты крайних случаев"""
    
    def test_empty_database_export(self):
        """Тест выгрузки из пустой базы"""
        response = export_player_levels_csv()
        content = response.content.decode('utf-8')
        csv_data = list(csv.reader(StringIO(content)))
        
        # Должен быть только заголовок
        self.assertEqual(len(csv_data), 1)
        self.assertEqual(csv_data[0], ['player_id', 'level_title', 'is_completed', 'prize_received'])