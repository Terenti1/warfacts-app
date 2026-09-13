# user_data.py - Система рейтинга тегов, заметок и прогрессии

import json
import os
from datetime import datetime


class UserPreferences:
    """Управляет предпочтениями пользователя, заметками и прогрессией"""

    def __init__(self, storage_file="user_data.json"):
        self.storage_file = storage_file
        self.data = self.load_data()

    def load_data(self):
        """Загружает данные пользователя из файла"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                default = self.get_default_data()
                for key in default:
                    if key not in data:
                        data[key] = default[key]
                return data
            except:
                return self.get_default_data()
        return self.get_default_data()

    def get_default_data(self):
        """Возвращает структуру данных по умолчанию"""
        return {
            "viewed_facts": [],  # ID просмотренных фактов
            "liked_facts": [],  # ID фактов, которые понравились
            "disliked_facts": [],  # ID фактов, которые не понравились
            "tag_scores": {},  # {tag: score} - очки тегов
            "tag_history": [],  # История изменений тегов
            "notes": {},  # {fact_id: "текст заметки"}
            "tag_progress": {},  # {tag: [изученные ID фактов]}
            "achievements": [],  # список полученных достижений
            "streak_days": 0,  # серия дней
            "last_activity": None,  # дата последней активности
            "total_views": 0  # общее количество просмотров
        }

    def save_data(self):
        """Сохраняет данные пользователя"""
        self.data["last_visit"] = datetime.now().isoformat()
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_view(self, fact_id, tags):
        """Добавляет просмотр факта и обновляет прогрессию"""
        if fact_id not in self.data["viewed_facts"]:
            self.data["viewed_facts"].append(fact_id)

            # Обновляем прогресс по тегам
            for tag in tags:
                if tag not in self.data["tag_progress"]:
                    self.data["tag_progress"][tag] = []
                if fact_id not in self.data["tag_progress"][tag]:
                    self.data["tag_progress"][tag].append(fact_id)

        self.data["total_views"] += 1

        # Обновляем серию (streak)
        self.update_streak()

        self.save_data()

    def update_streak(self):
        """Обновляет серию дней активности"""
        today = datetime.now().date()
        last = self.data.get("last_activity")

        if last:
            last_date = datetime.fromisoformat(last).date()
            diff = (today - last_date).days

            if diff == 0:
                # Уже сегодня активен
                pass
            elif diff == 1:
                # Вчера был активен - увеличиваем серию
                self.data["streak_days"] = self.data.get("streak_days", 0) + 1
            else:
                # Пропустил день - сбрасываем серию
                self.data["streak_days"] = 0
        else:
            # Первая активность
            self.data["streak_days"] = 1

        self.data["last_activity"] = datetime.now().isoformat()

    # ===== МЕТОДЫ ДЛЯ ПРОГРЕССИИ =====

    def get_total_progress(self, total_facts):
        """Возвращает общий прогресс в процентах"""
        if total_facts == 0:
            return 0
        return round((len(self.data["viewed_facts"]) / total_facts) * 100)

    def get_tag_progress(self, tag, total_facts_for_tag):
        """Возвращает прогресс по тегу в процентах"""
        if total_facts_for_tag == 0:
            return 0
        viewed = len(self.data["tag_progress"].get(tag, []))
        return round((viewed / total_facts_for_tag) * 100)

    def get_tag_progress_details(self, all_tags_data):
        """Возвращает детальную информацию о прогрессе по тегам"""
        result = {}
        for tag, facts in all_tags_data.items():
            total = len(facts)
            viewed = len(self.data["tag_progress"].get(tag, []))
            result[tag] = {
                "total": total,
                "viewed": viewed,
                "progress": self.get_tag_progress(tag, total),
                "completed": viewed >= total
            }
        return result

    def get_achievement_progress(self):
        """Возвращает прогресс по достижениям"""
        achievements = []
        viewed_count = len(self.data["viewed_facts"])

        # Достижения по количеству фактов
        if viewed_count >= 1:
            achievements.append(
                {"id": "first_fact", "name": "Первый шаг", "desc": "Прочитан первый факт", "unlocked": True})
        if viewed_count >= 10:
            achievements.append(
                {"id": "ten_facts", "name": "Любознательный", "desc": "Прочитано 10 фактов", "unlocked": True})
        if viewed_count >= 25:
            achievements.append(
                {"id": "twenty_five", "name": "Исследователь", "desc": "Прочитано 25 фактов", "unlocked": True})
        if viewed_count >= 50:
            achievements.append(
                {"id": "fifty_facts", "name": "Знаток истории", "desc": "Прочитано 50 фактов", "unlocked": True})

        # Достижение за серию
        streak = self.data.get("streak_days", 0)
        if streak >= 3:
            achievements.append(
                {"id": "streak_3", "name": "Постоянный", "desc": "Активен 3 дня подряд", "unlocked": True})
        if streak >= 7:
            achievements.append(
                {"id": "streak_7", "name": "Неутомимый", "desc": "Активен 7 дней подряд", "unlocked": True})

        return achievements

    def add_achievement(self, achievement_id):
        """Добавляет достижение, если его ещё нет"""
        if achievement_id not in self.data["achievements"]:
            self.data["achievements"].append(achievement_id)
            self.save_data()
            return True
        return False

    def get_streak_days(self):
        """Возвращает текущую серию дней"""
        # Проверяем, не пропущен ли сегодняшний день
        today = datetime.now().date()
        last = self.data.get("last_activity")
        if last:
            last_date = datetime.fromisoformat(last).date()
            diff = (today - last_date).days
            if diff > 1:
                self.data["streak_days"] = 0
                self.save_data()
        return self.data.get("streak_days", 0)

    # ===== МЕТОДЫ ДЛЯ ЗАМЕТОК =====

    def add_note(self, fact_id, note_text):
        """Добавляет или обновляет заметку для факта"""
        if note_text and note_text.strip():
            self.data["notes"][str(fact_id)] = note_text.strip()
        else:
            if str(fact_id) in self.data["notes"]:
                del self.data["notes"][str(fact_id)]
        self.save_data()
        return True

    def get_note(self, fact_id):
        """Возвращает заметку для факта, если есть"""
        return self.data["notes"].get(str(fact_id), "")

    def has_note(self, fact_id):
        """Проверяет, есть ли заметка для факта"""
        return str(fact_id) in self.data["notes"]

    def delete_note(self, fact_id):
        """Удаляет заметку для факта"""
        if str(fact_id) in self.data["notes"]:
            del self.data["notes"][str(fact_id)]
            self.save_data()
            return True
        return False

    def get_all_notes(self):
        """Возвращает все заметки в виде {fact_id: note_text}"""
        return self.data.get("notes", {}).copy()

    # ===== МЕТОДЫ ДЛЯ ОЦЕНОК (ЛАЙК/ДИЗЛАЙК) =====

    def add_like(self, fact_id, tags):
        """Добавляет лайк факту (+1 к каждому тегу)"""
        if fact_id in self.data["disliked_facts"]:
            self.data["disliked_facts"].remove(fact_id)
        if fact_id not in self.data["liked_facts"]:
            self.data["liked_facts"].append(fact_id)
            for tag in tags:
                self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) + 1
                self.data["tag_history"].append({
                    "tag": tag,
                    "change": +1,
                    "fact_id": fact_id,
                    "timestamp": datetime.now().isoformat()
                })
            self.save_data()
            return True
        return False

    def add_dislike(self, fact_id, tags):
        """Добавляет дизлайк факту (-1 к каждому тегу)"""
        if fact_id in self.data["liked_facts"]:
            self.data["liked_facts"].remove(fact_id)
        if fact_id not in self.data["disliked_facts"]:
            self.data["disliked_facts"].append(fact_id)
            for tag in tags:
                self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) - 1
                self.data["tag_history"].append({
                    "tag": tag,
                    "change": -1,
                    "fact_id": fact_id,
                    "timestamp": datetime.now().isoformat()
                })
            self.save_data()
            return True
        return False

    def remove_like(self, fact_id, tags):
        """Удаляет лайк (отмена)"""
        if fact_id in self.data["liked_facts"]:
            self.data["liked_facts"].remove(fact_id)
            for tag in tags:
                self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) - 1
            self.save_data()
            return True
        return False

    def remove_dislike(self, fact_id, tags):
        """Удаляет дизлайк (отмена)"""
        if fact_id in self.data["disliked_facts"]:
            self.data["disliked_facts"].remove(fact_id)
            for tag in tags:
                self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) + 1
            self.save_data()
            return True
        return False

    # ===== МЕТОДЫ ДЛЯ РЕЙТИНГА =====

    def get_tag_score(self, tag):
        """Возвращает текущий рейтинг тега"""
        return self.data["tag_scores"].get(tag, 0)

    def get_top_tags(self, limit=5):
        """Возвращает топ N тегов по очкам"""
        sorted_tags = sorted(
            self.data["tag_scores"].items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_tags[:limit]

    def get_bottom_tags(self, limit=5):
        """Возвращает худшие N тегов по очкам"""
        sorted_tags = sorted(
            self.data["tag_scores"].items(),
            key=lambda x: x[1]
        )
        return sorted_tags[:limit]

    # ===== СИСТЕМА РЕКОМЕНДАЦИЙ =====

    def get_recommendation_score(self, fact):
        """Вычисляет рейтинг рекомендации для факта на основе очков тегов"""
        if "tags" not in fact:
            return 0

        # Суммируем очки всех тегов факта
        total_score = sum(self.get_tag_score(tag) for tag in fact["tags"])

        # Штраф за повторный просмотр
        if fact["id"] in self.data["viewed_facts"]:
            total_score -= 5

        # Бонус за новизну (если факт не просмотрен)
        if fact["id"] not in self.data["viewed_facts"]:
            total_score += 2

        # Если факт уже в избранном, показываем его чаще
        if fact["id"] in self.data["liked_facts"]:
            total_score += 3

        return total_score

    # ===== СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ =====

    def get_user_stats(self):
        """Возвращает статистику пользователя"""
        return {
            "total_views": self.data["total_views"],
            "liked_count": len(self.data["liked_facts"]),
            "disliked_count": len(self.data["disliked_facts"]),
            "unique_facts_viewed": len(set(self.data["viewed_facts"])),
            "top_tags": self.get_top_tags(5),
            "bottom_tags": self.get_bottom_tags(3),
            "total_tags_tracked": len(self.data["tag_scores"]),
            "streak_days": self.get_streak_days()
        }

    def get_fact_status(self, fact_id):
        """Возвращает статус факта (лайк, дизлайк или нейтральный)"""
        if fact_id in self.data["liked_facts"]:
            return "liked"
        elif fact_id in self.data["disliked_facts"]:
            return "disliked"
        return "neutral"

    # ===== УПРАВЛЕНИЕ ДАННЫМИ =====

    def clear_history(self):
        """Очищает историю просмотров и прогресс, сохраняя избранное, заметки и рейтинг"""
        self.data["viewed_facts"] = []
        self.data["tag_progress"] = {}
        self.data["total_views"] = 0
        self.data["streak_days"] = 0
        self.data["last_activity"] = None
        # Не удаляем: liked_facts, disliked_facts, tag_scores, tag_history, notes, achievements
        self.save_data()

    def reset_data(self):
        """Сбрасывает все данные пользователя"""
        self.data = self.get_default_data()
        self.save_data()