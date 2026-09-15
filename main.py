# main.py - Приложение "Факты о ВОВ"

import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle

from data import FACTS_DATABASE, get_facts_count, get_fact_by_id, get_all_tags, get_facts_by_tag
from user_data import UserPreferences

try:
    from version import __version__
except Exception:
    __version__ = "1.0.0"

try:
    from updater import check_for_updates, UPDATER_AVAILABLE
except Exception as e:
    print(f"[MAIN] Updater недоступен: {e}")
    UPDATER_AVAILABLE = False
    def check_for_updates(manual=False):
        pass


def _fact_label(fact, length=60):
    title = fact.get("title")
    if title:
        return title
    text = fact.get("text", "")
    return text[:length] + "..." if len(text) > length else text


def make_header(title_text, back_callback, height=0.10):
    """Хедер с центрированным заголовком и кнопкой назад слева."""
    header = FloatLayout(size_hint=(1, height))

    title = Label(
        text=title_text,
        font_size='20sp',
        color=get_color_from_hex('#c9a84c'),
        bold=True,
        size_hint=(1, 1),
        pos_hint={'x': 0, 'y': 0},
        halign='center',
        valign='middle',
        text_size=(Window.width - 30, None)
    )
    header.add_widget(title)

    back_btn = Button(
        text="<--",
        size_hint=(0.15, 1),
        pos_hint={'x': 0, 'y': 0},
        background_color=(0.2, 0.2, 0.2, 0.8),
        color=(1, 1, 1, 1),
        font_size='16sp'
    )
    back_btn.bind(on_release=back_callback)
    header.add_widget(back_btn)

    return header


# ============================================================
#  ГЛАВНОЕ МЕНЮ
# ============================================================

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets()
            self.user_prefs = UserPreferences()
            self.build_ui()
        else:
            self._built_once = True

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=15, spacing=8)

        header = BoxLayout(orientation='vertical', size_hint=(1, 0.13))
        title = Label(
            text="ФАКТЫ О ВОВ",
            font_size='28sp',
            color=get_color_from_hex('#c9a84c'),
            bold=True,
            size_hint=(1, 0.5)
        )
        header.add_widget(title)
        subtitle = Label(
            text="Великая Отечественная война 1941-1945",
            font_size='14sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint=(1, 0.3)
        )
        header.add_widget(subtitle)
        layout.add_widget(header)

        total_facts = get_facts_count()
        viewed = len(self.user_prefs.data["viewed_facts"])
        progress = self.user_prefs.get_total_progress(total_facts)
        streak = self.user_prefs.get_streak_days()

        progress_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.08), spacing=3)

        progress_header = BoxLayout(size_hint=(1, 0.4))
        progress_header.add_widget(Label(
            text=f"Прогресс: {viewed}/{total_facts} фактов",
            font_size='14sp',
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(0.7, 1),
            halign='left'
        ))
        progress_header.add_widget(Label(
            text=f"Серия: {streak} дн.",
            font_size='14sp',
            color=(0.9, 0.7, 0.2, 1),
            size_hint=(0.3, 1),
            halign='right'
        ))
        progress_layout.add_widget(progress_header)

        progress_bar = Button(
            text=f"{progress}%",
            background_color=(0.2, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            size_hint=(1, 0.6),
            font_size='12sp',
            disabled=True
        )
        progress_bar.canvas.before.clear()
        with progress_bar.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=progress_bar.pos, size=progress_bar.size)
            if progress > 0:
                Color(0.78, 0.66, 0.30, 1)
                Rectangle(
                    pos=progress_bar.pos,
                    size=(progress_bar.width * progress / 100, progress_bar.height)
                )

        progress_bar.bind(pos=self.update_progress_bar, size=self.update_progress_bar)
        self.progress_bar = progress_bar
        self.progress_value = progress

        progress_layout.add_widget(progress_bar)
        layout.add_widget(progress_layout)

        stats = self.user_prefs.get_user_stats()
        top_tags = stats['top_tags'][:3]

        fact_btn_text = "ФАКТ ДНЯ\n"

        viewed_facts = set(self.user_prefs.data["viewed_facts"])
        unviewed_facts = [f for f in FACTS_DATABASE if f["id"] not in viewed_facts]

        if not unviewed_facts:
            fact_btn_text = "ВСЕ ФАКТЫ ИЗУЧЕНЫ!\nПоздравляем!"
            fact_btn_text += "\n\nНажмите для просмотра понравившихся"
        elif top_tags and any(score > 0 for _, score in top_tags):
            tags_str = "  ".join([f"{tag} +{score}" for tag, score in top_tags if score > 0])
            fact_btn_text += f"Ваши темы: {tags_str}"
        else:
            fact_btn_text += "Оценивайте факты [+] или [-]"

        fact_btn = Button(
            text=fact_btn_text,
            font_size='16sp',
            background_color=get_color_from_hex('#7a3b1e'),
            color=(1, 1, 1, 1),
            bold=True,
            size_hint=(1, 0.20),
            halign='center',
            valign='middle'
        )
        fact_btn.bind(on_release=self.go_to_fact_of_day)
        layout.add_widget(fact_btn)

        grid = GridLayout(cols=2, spacing=10, size_hint=(1, 0.42))

        history_btn = Button(
            text=f"ИСТОРИЯ\n\n{stats['unique_facts_viewed']}\nизучено",
            background_color=get_color_from_hex('#2c3e50'),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        history_btn.bind(on_release=self.go_to_history)
        grid.add_widget(history_btn)

        notes_count = len(self.user_prefs.get_all_notes())
        notes_btn = Button(
            text=f"ЗАМЕТКИ\n\n{notes_count}\nсохранено",
            background_color=get_color_from_hex('#2c3e50'),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        notes_btn.bind(on_release=self.go_to_notes)
        grid.add_widget(notes_btn)

        stats_btn = Button(
            text=f"СТАТИСТИКА\n\n{progress}%\nпрогресс",
            background_color=get_color_from_hex('#2c3e50'),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        stats_btn.bind(on_release=self.go_to_stats)
        grid.add_widget(stats_btn)

        settings_btn = Button(
            text=f"НАСТРОЙКИ\n\nv{__version__}\n",
            background_color=get_color_from_hex('#2c3e50'),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        settings_btn.bind(on_release=self.go_to_settings)
        grid.add_widget(settings_btn)

        layout.add_widget(grid)

        footer = BoxLayout(orientation='vertical', size_hint=(1, 0.05))
        footer.add_widget(Label(
            text=f"Фактов: {total_facts}  |  Изучено: {viewed}  |  Понравилось: {stats['liked_count']}",
            font_size='11sp',
            color=(0.5, 0.5, 0.5, 1)
        ))
        layout.add_widget(footer)

        self.add_widget(layout)

    def update_progress_bar(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=instance.pos, size=instance.size)
            if self.progress_value > 0:
                Color(0.78, 0.66, 0.30, 1)
                width = (self.progress_value / 100) * instance.width
                Rectangle(
                    pos=instance.pos,
                    size=(width, instance.height)
                )

    def go_to_fact_of_day(self, instance):
        viewed_facts = set(self.user_prefs.data["viewed_facts"])
        unviewed_facts = [f for f in FACTS_DATABASE if f["id"] not in viewed_facts]

        if unviewed_facts:
            scored_facts = []
            for fact in unviewed_facts:
                score = self.user_prefs.get_recommendation_score(fact)
                scored_facts.append((fact, score))
            scored_facts.sort(key=lambda x: x[1], reverse=True)

            if scored_facts:
                best_fact = scored_facts[0][0]
                self.manager.current = 'fact_screen'
                self.manager.get_screen('fact_screen').show_fact(best_fact)
            else:
                fact = random.choice(unviewed_facts)
                self.manager.current = 'fact_screen'
                self.manager.get_screen('fact_screen').show_fact(fact)
        else:
            liked = self.user_prefs.data["liked_facts"]
            if liked:
                fact_id = random.choice(liked)
                fact = get_fact_by_id(fact_id)
                if fact:
                    self.manager.current = 'fact_screen'
                    self.manager.get_screen('fact_screen').show_fact(fact)
                else:
                    self.show_all_studied_popup()
            else:
                self.show_all_studied_popup()

    def show_all_studied_popup(self):
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        content.add_widget(Label(
            text="ПОЗДРАВЛЯЕМ!",
            font_size='22sp',
            color=get_color_from_hex('#c9a84c'),
            size_hint=(1, None),
            height=50,
            bold=True
        ))
        content.add_widget(Label(
            text="Вы изучили все факты!\n\n"
                 "Оцените факты [+] или [-],\n"
                 "чтобы улучшить рекомендации\n"
                 "и получить новые достижения.",
            font_size='16sp',
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(1, None),
            height=130,
            halign='center'
        ))

        btn_row = BoxLayout(size_hint=(1, None), height=45, spacing=10)
        ok_btn = Button(
            text="ОК",
            background_color=get_color_from_hex('#7a3b1e'),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        btn_row.add_widget(ok_btn)
        content.add_widget(btn_row)

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.85, 0.45),
            background_color=(0.1, 0.1, 0.1, 0.95)
        )
        ok_btn.bind(on_release=popup.dismiss)
        popup.open()

    def go_to_history(self, instance):
        self.manager.current = 'history_screen'

    def go_to_notes(self, instance):
        self.manager.current = 'notes_screen'

    def go_to_stats(self, instance):
        self.manager.current = 'stats_screen'

    def go_to_settings(self, instance):
        self.manager.current = 'settings_screen'


# ============================================================
#  ЭКРАН ФАКТА
# ============================================================

class FactScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_fact = None
        self.showing_extended = False
        self.user_prefs = UserPreferences()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=15, spacing=8)

        top_panel = BoxLayout(size_hint=(1, 0.07), spacing=8)

        back_btn = Button(
            text="<--",
            size_hint=(0.15, 1),
            background_color=(0.2, 0.2, 0.2, 0.8),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        back_btn.bind(on_release=self.go_back)
        top_panel.add_widget(back_btn)

        self.ext_btn = Button(
            text="[i] Подробнее",
            size_hint=(0.85, 1),
            background_color=get_color_from_hex('#2c3e50'),
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        self.ext_btn.bind(on_release=self.toggle_extended)
        top_panel.add_widget(self.ext_btn)

        layout.add_widget(top_panel)

        self.text_scroll = ScrollView(size_hint=(1, 0.4))
        self.fact_text = Label(
            text="",
            font_size='20sp',
            color=(1, 1, 1, 1),
            halign='left',
            valign='top',
            size_hint=(1, None),
            text_size=(Window.width - 30, None)
        )
        self.fact_text.bind(texture_size=self.fact_text.setter('size'))
        self.text_scroll.add_widget(self.fact_text)
        layout.add_widget(self.text_scroll)

        self.ext_scroll = ScrollView(size_hint=(1, 0.35))
        self.ext_text = Label(
            text="",
            font_size='16sp',
            color=(0.8, 0.8, 0.8, 1),
            halign='left',
            valign='top',
            size_hint=(1, None),
            text_size=(Window.width - 30, None)
        )
        self.ext_text.bind(texture_size=self.ext_text.setter('size'))
        self.ext_scroll.add_widget(self.ext_text)
        self.ext_scroll.opacity = 0
        self.ext_scroll.disabled = True
        layout.add_widget(self.ext_scroll)

        self.tags_label = Label(
            text="",
            font_size='13sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint=(1, 0.06),
            halign='center'
        )
        layout.add_widget(self.tags_label)

        action_row = BoxLayout(size_hint=(1, 0.08), spacing=8)

        self.like_btn = Button(
            text="[+]",
            font_size='22sp',
            background_color=(0.3, 0.3, 0.3, 0.5),
            color=(0.5, 0.5, 0.5, 1),
            size_hint=(0.25, 1)
        )
        self.like_btn.bind(on_release=self.toggle_like)
        action_row.add_widget(self.like_btn)

        self.dislike_btn = Button(
            text="[-]",
            font_size='22sp',
            background_color=(0.3, 0.3, 0.3, 0.5),
            color=(0.5, 0.5, 0.5, 1),
            size_hint=(0.25, 1)
        )
        self.dislike_btn.bind(on_release=self.toggle_dislike)
        action_row.add_widget(self.dislike_btn)

        self.note_btn = Button(
            text="[N]",
            font_size='22sp',
            background_color=(0.3, 0.3, 0.3, 0.5),
            color=(0.7, 0.7, 0.7, 1),
            size_hint=(0.25, 1)
        )
        self.note_btn.bind(on_release=self.open_note_popup)
        action_row.add_widget(self.note_btn)

        next_btn = Button(
            text="[>]",
            font_size='22sp',
            background_color=get_color_from_hex('#7a3b1e'),
            color=(1, 1, 1, 1),
            size_hint=(0.25, 1)
        )
        next_btn.bind(on_release=self.next_fact)
        action_row.add_widget(next_btn)

        layout.add_widget(action_row)

        self.status_label = Label(
            text="Оцените или сохраните в заметки",
            font_size='11sp',
            color=(0.5, 0.5, 0.5, 1),
            size_hint=(1, 0.04)
        )
        layout.add_widget(self.status_label)

        self.add_widget(layout)

    def on_size(self, *args):
        if hasattr(self, 'fact_text'):
            self.fact_text.text_size = (self.width - 30, None)
        if hasattr(self, 'ext_text'):
            self.ext_text.text_size = (self.width - 30, None)

    def show_fact(self, fact):
        self.current_fact = fact
        self.showing_extended = False
        self.ext_scroll.opacity = 0
        self.ext_scroll.disabled = True
        self.ext_btn.text = "[i] Подробнее"

        self.fact_text.text = fact["text"]
        self.fact_text.text_size = (self.width - 30, None)

        if "extended" in fact and fact["extended"]:
            self.ext_text.text = fact["extended"]
            self.ext_text.text_size = (self.width - 30, None)
            self.has_extended = True
        else:
            self.ext_text.text = "Нет дополнительной информации"
            self.has_extended = False

        tags_info = []
        for tag in fact["tags"]:
            score = self.user_prefs.get_tag_score(tag)
            if score > 0:
                tags_info.append(f"#{tag.capitalize()} +{score}")
            elif score < 0:
                tags_info.append(f"#{tag.capitalize()} {score}")
            else:
                tags_info.append(f"#{tag.capitalize()}")
        self.tags_label.text = "  ".join(tags_info)

        status = self.user_prefs.get_fact_status(fact["id"])
        self.update_buttons(status)

        if self.user_prefs.has_note(fact["id"]):
            self.note_btn.text = "[N*]"
            self.note_btn.color = (0.2, 0.8, 0.2, 1)
        else:
            self.note_btn.text = "[N]"
            self.note_btn.color = (0.7, 0.7, 0.7, 1)

        if fact["id"] not in self.user_prefs.data["viewed_facts"]:
            self.user_prefs.add_view(fact["id"], fact["tags"])

        stats = self.user_prefs.get_user_stats()
        self.status_label.text = f"Просмотрено: {stats['unique_facts_viewed']} | [+]: {stats['liked_count']} | Заметок: {len(self.user_prefs.get_all_notes())}"

    def toggle_extended(self, instance):
        if not self.has_extended:
            self.status_label.text = "Для этого факта нет доп. информации"
            return

        self.showing_extended = not self.showing_extended

        if self.showing_extended:
            self.ext_scroll.opacity = 1
            self.ext_scroll.disabled = False
            self.ext_btn.text = "[i] Скрыть"
            anim = Animation(opacity=1, duration=0.3)
            anim.start(self.ext_scroll)
        else:
            anim = Animation(opacity=0, duration=0.3)
            anim.bind(on_complete=lambda *args: setattr(self.ext_scroll, 'disabled', True))
            anim.start(self.ext_scroll)
            self.ext_btn.text = "[i] Подробнее"

    def open_note_popup(self, instance):
        if not self.current_fact:
            return

        fact_id = self.current_fact["id"]
        fact_text = self.current_fact["text"][:50] + "..."
        existing_note = self.user_prefs.get_note(fact_id)

        content = BoxLayout(orientation='vertical', padding=10, spacing=8)

        content.add_widget(Label(
            text="ЗАМЕТКА К ФАКТУ",
            font_size='18sp',
            color=get_color_from_hex('#c9a84c'),
            size_hint=(1, 0.1)
        ))

        content.add_widget(Label(
            text=fact_text,
            font_size='14sp',
            color=(0.8, 0.8, 0.8, 1),
            size_hint=(1, 0.1),
            halign='center'
        ))

        text_input = TextInput(
            text=existing_note,
            hint_text="Введите вашу заметку...",
            multiline=True,
            font_size='16sp',
            size_hint=(1, 0.5),
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1)
        )
        content.add_widget(text_input)

        btn_row = BoxLayout(size_hint=(1, 0.15), spacing=8)

        cancel_btn = Button(
            text="Отмена",
            background_color=(0.3, 0.3, 0.3, 0.8),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        btn_row.add_widget(cancel_btn)

        save_btn = Button(
            text="Сохранить",
            background_color=get_color_from_hex('#7a3b1e'),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        btn_row.add_widget(save_btn)

        if existing_note:
            delete_btn = Button(
                text="Удалить",
                background_color=(0.5, 0.2, 0.2, 0.8),
                color=(1, 1, 1, 1),
                font_size='16sp'
            )
            btn_row.add_widget(delete_btn)

        content.add_widget(btn_row)

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.9, 0.7),
            background_color=(0.1, 0.1, 0.1, 0.95)
        )

        def save_note(instance):
            note = text_input.text
            self.user_prefs.add_note(fact_id, note)
            popup.dismiss()
            if note.strip():
                self.note_btn.text = "[N*]"
                self.note_btn.color = (0.2, 0.8, 0.2, 1)
                self.status_label.text = "Заметка сохранена!"
            else:
                self.note_btn.text = "[N]"
                self.note_btn.color = (0.7, 0.7, 0.7, 1)
                self.status_label.text = "Заметка удалена"

        def delete_note(instance):
            self.user_prefs.delete_note(fact_id)
            popup.dismiss()
            self.note_btn.text = "[N]"
            self.note_btn.color = (0.7, 0.7, 0.7, 1)
            self.status_label.text = "Заметка удалена"

        save_btn.bind(on_release=save_note)
        cancel_btn.bind(on_release=popup.dismiss)
        if existing_note:
            delete_btn.bind(on_release=delete_note)

        popup.open()

    def update_buttons(self, status):
        if status == "liked":
            self.like_btn.background_color = (0.8, 0.2, 0.2, 0.8)
            self.like_btn.color = get_color_from_hex('#c9a84c')
            self.like_btn.text = "[★]"
            self.dislike_btn.background_color = (0.3, 0.3, 0.3, 0.5)
            self.dislike_btn.color = (0.5, 0.5, 0.5, 1)
            self.dislike_btn.text = "[-]"
        elif status == "disliked":
            self.like_btn.background_color = (0.3, 0.3, 0.3, 0.5)
            self.like_btn.color = (0.5, 0.5, 0.5, 1)
            self.like_btn.text = "[+]"
            self.dislike_btn.background_color = (0.3, 0.3, 0.3, 0.8)
            self.dislike_btn.color = (1, 1, 1, 1)
            self.dislike_btn.text = "[-]"
        else:
            self.like_btn.background_color = (0.3, 0.3, 0.3, 0.5)
            self.like_btn.color = (0.5, 0.5, 0.5, 1)
            self.like_btn.text = "[+]"
            self.dislike_btn.background_color = (0.3, 0.3, 0.3, 0.5)
            self.dislike_btn.color = (0.5, 0.5, 0.5, 1)
            self.dislike_btn.text = "[-]"

    def toggle_like(self, instance):
        if not self.current_fact:
            return

        fact_id = self.current_fact["id"]
        tags = self.current_fact["tags"]
        status = self.user_prefs.get_fact_status(fact_id)

        if status == "liked":
            self.user_prefs.remove_like(fact_id, tags)
            self.update_buttons("neutral")
        else:
            if status == "disliked":
                self.user_prefs.remove_dislike(fact_id, tags)
            self.user_prefs.add_like(fact_id, tags)
            self.update_buttons("liked")

        if self.user_prefs.has_note(fact_id):
            self.note_btn.text = "[N*]"
            self.note_btn.color = (0.2, 0.8, 0.2, 1)
        else:
            self.note_btn.text = "[N]"
            self.note_btn.color = (0.7, 0.7, 0.7, 1)

        stats = self.user_prefs.get_user_stats()
        self.status_label.text = f"Просмотрено: {stats['unique_facts_viewed']} | [+]: {stats['liked_count']} | Заметок: {len(self.user_prefs.get_all_notes())}"

    def toggle_dislike(self, instance):
        if not self.current_fact:
            return

        fact_id = self.current_fact["id"]
        tags = self.current_fact["tags"]
        status = self.user_prefs.get_fact_status(fact_id)

        if status == "disliked":
            self.user_prefs.remove_dislike(fact_id, tags)
            self.update_buttons("neutral")
        else:
            if status == "liked":
                self.user_prefs.remove_like(fact_id, tags)
            self.user_prefs.add_dislike(fact_id, tags)
            self.update_buttons("disliked")

        stats = self.user_prefs.get_user_stats()
        self.status_label.text = f"Просмотрено: {stats['unique_facts_viewed']} | [+]: {stats['liked_count']} | Заметок: {len(self.user_prefs.get_all_notes())}"

    def next_fact(self, instance):
        viewed_facts = set(self.user_prefs.data["viewed_facts"])
        unviewed_facts = [f for f in FACTS_DATABASE if f["id"] not in viewed_facts]

        if unviewed_facts:
            scored_facts = []
            for fact in unviewed_facts:
                score = self.user_prefs.get_recommendation_score(fact)
                scored_facts.append((fact, score))
            scored_facts.sort(key=lambda x: x[1], reverse=True)

            if scored_facts:
                next_fact = scored_facts[0][0]
                self.show_fact(next_fact)
            else:
                next_fact = random.choice(unviewed_facts)
                self.show_fact(next_fact)
        else:
            self.show_all_studied_popup()

    def show_all_studied_popup(self):
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        content.add_widget(Label(
            text="ПОЗДРАВЛЯЕМ!",
            font_size='22sp',
            color=get_color_from_hex('#c9a84c'),
            size_hint=(1, None),
            height=50,
            bold=True
        ))
        content.add_widget(Label(
            text="Вы изучили все факты!\n\n"
                 "Оценивайте факты [+] или [-],\n"
                 "чтобы улучшить рекомендации.",
            font_size='16sp',
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(1, None),
            height=110,
            halign='center'
        ))

        btn_row = BoxLayout(size_hint=(1, None), height=45, spacing=10)
        ok_btn = Button(
            text="ОК",
            background_color=get_color_from_hex('#7a3b1e'),
            color=(1, 1, 1, 1),
            font_size='18sp',
            bold=True
        )
        btn_row.add_widget(ok_btn)
        content.add_widget(btn_row)

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.85, 0.4),
            background_color=(0.1, 0.1, 0.1, 0.95)
        )
        ok_btn.bind(on_release=popup.dismiss)
        popup.open()

    def go_back(self, instance):
        self.manager.current = 'main_menu'


# ============================================================
#  ИСТОРИЯ
# ============================================================

class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets()
            self.user_prefs = UserPreferences()
            self.build_ui()
        else:
            self._built_once = True

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=6)

        layout.add_widget(make_header("История", self.go_back, 0.10))

        scroll = ScrollView(size_hint=(1, 0.90), bar_width=4)
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content_box.bind(minimum_height=content_box.setter('height'))

        liked = self.user_prefs.data["liked_facts"]
        viewed = self.user_prefs.data["viewed_facts"]

        # СЕКЦИЯ: ПОНРАВИВШИЕСЯ
        content_box.add_widget(Label(
            text=f"★ ПОНРАВИВШИЕСЯ ({len(liked)})",
            font_size='16sp',
            color=get_color_from_hex('#c9a84c'),
            bold=True,
            size_hint=(1, None),
            height=45,
            halign='center',
            valign='middle',
            text_size=(Window.width - 30, None)
        ))

        if liked:
            for fact_id in reversed(liked):
                fact = get_fact_by_id(fact_id)
                if fact:
                    has_note = self.user_prefs.has_note(fact_id)
                    note_icon = " [N]" if has_note else ""

                    fact_btn = Button(
                        text=f"[★]{note_icon} {_fact_label(fact, 40)}",
                        size_hint=(1, None),
                        height=55,
                        background_color=get_color_from_hex('#4a2a1a'),
                        color=get_color_from_hex('#c9a84c'),
                        font_size='15sp',
                        halign='center',
                        valign='middle'
                    )
                    fact_btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                    content_box.add_widget(fact_btn)
        else:
            content_box.add_widget(Label(
                text="Нет понравившихся фактов. Оценивайте [+]",
                font_size='14sp',
                color=(0.5, 0.5, 0.5, 1),
                size_hint=(1, None),
                height=45,
                halign='center',
                valign='middle',
                text_size=(Window.width - 20, None)
            ))

        # ПУСТОЙ РАЗДЕЛИТЕЛЬ
        content_box.add_widget(Label(
            text="",
            size_hint=(1, None),
            height=20
        ))

        # СЕКЦИЯ: ИЗУЧЕННЫЕ (без лайкнутых)
        not_liked = [fid for fid in viewed if fid not in liked]

        content_box.add_widget(Label(
            text=f"▸ ИЗУЧЕННЫЕ ({len(not_liked)})",
            font_size='16sp',
            color=(0.8, 0.8, 0.8, 1),
            bold=True,
            size_hint=(1, None),
            height=45,
            halign='center',
            valign='middle',
            text_size=(Window.width - 30, None)
        ))

        if not_liked:
            for fact_id in reversed(not_liked):
                fact = get_fact_by_id(fact_id)
                if fact:
                    has_note = self.user_prefs.has_note(fact_id)
                    note_icon = " [N]" if has_note else ""

                    fact_btn = Button(
                        text=f"[i]{note_icon} {_fact_label(fact, 40)}",
                        size_hint=(1, None),
                        height=55,
                        background_color=get_color_from_hex('#2c3e50'),
                        color=(1, 1, 1, 1),
                        font_size='15sp',
                        halign='center',
                        valign='middle'
                    )
                    fact_btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                    content_box.add_widget(fact_btn)
        else:
            msg = "Все изученные уже в понравившихся" if viewed else "Вы ещё не читали факты.\nНачните с 'Факта дня'!"
            content_box.add_widget(Label(
                text=msg,
                font_size='14sp',
                color=(0.5, 0.5, 0.5, 1),
                size_hint=(1, None),
                height=45,
                halign='center',
                valign='middle',
                text_size=(Window.width - 20, None)
            ))

        scroll.add_widget(content_box)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def view_fact(self, fact):
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(fact)

    def go_back(self, instance):
        self.manager.current = 'main_menu'


# ============================================================
#  ЗАМЕТКИ
# ============================================================

class NotesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets()
            self.user_prefs = UserPreferences()
            self.build_ui()
        else:
            self._built_once = True

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=6)

        layout.add_widget(make_header("Мои заметки", 
            lambda x: setattr(self.manager, 'current', 'main_menu'), 0.10))

        scroll = ScrollView(size_hint=(1, 0.90), bar_width=4)
        notes_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        notes_box.bind(minimum_height=notes_box.setter('height'))

        all_notes = self.user_prefs.get_all_notes()

        if all_notes:
            for fact_id_str, note_text in all_notes.items():
                fact_id = int(fact_id_str)
                fact = get_fact_by_id(fact_id)
                if fact:
                    note_btn = Button(
                        text=f"[N] {_fact_label(fact, 40)}\n\n{note_text[:100]}{'...' if len(note_text) > 100 else ''}",
                        size_hint=(1, None),
                        height=100,
                        background_color=get_color_from_hex('#2c3e50'),
                        color=(1, 1, 1, 1),
                        font_size='13sp',
                        halign='center',
                        valign='middle'
                    )
                    note_btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                    notes_box.add_widget(note_btn)
        else:
            notes_box.add_widget(Label(
                text="У вас нет заметок\nОткройте факт и нажмите [N]",
                font_size='18sp',
                color=(0.5, 0.5, 0.5, 1),
                size_hint=(1, None),
                height=200
            ))

        scroll.add_widget(notes_box)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def view_fact(self, fact):
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(fact)


# ============================================================
#  СТАТИСТИКА
# ============================================================

class StatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets()
            self.user_prefs = UserPreferences()
            self.build_ui()
        else:
            self._built_once = True

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=6)

        layout.add_widget(make_header("Статистика", 
            lambda x: setattr(self.manager, 'current', 'main_menu'), 0.09))

        scroll = ScrollView(size_hint=(1, 0.91), bar_width=4)
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=12)
        content.bind(minimum_height=content.setter('height'))

        stats = self.user_prefs.get_user_stats()
        total_facts = get_facts_count()
        viewed = stats['unique_facts_viewed']
        progress = self.user_prefs.get_total_progress(total_facts)

        # ЗАГОЛОВОК: ОБЩИЙ ПРОГРЕСС
        content.add_widget(Label(
            text="[ ОБЩИЙ ПРОГРЕСС ]",
            font_size='16sp',
            color=get_color_from_hex('#c9a84c'),
            size_hint=(1, None),
            height=40,
            bold=True,
            halign='center',
            valign='middle',
            text_size=(Window.width - 20, None)
        ))

        stats_grid = GridLayout(cols=2, spacing=6, size_hint=(1, None), height=100)

        stats_grid.add_widget(Label(
            text=f"Всего фактов: {total_facts}",
            font_size='15sp',
            color=(0.9, 0.9, 0.9, 1)
        ))
        stats_grid.add_widget(Label(
            text=f"Изучено: {viewed}",
            font_size='15sp',
            color=(0.9, 0.9, 0.9, 1)
        ))
        stats_grid.add_widget(Label(
            text=f"Прогресс: {progress}%",
            font_size='15sp',
            color=(0.9, 0.9, 0.9, 1)
        ))
        stats_grid.add_widget(Label(
            text=f"Серия: {stats['streak_days']} дней",
            font_size='15sp',
            color=(0.9, 0.7, 0.2, 1)
        ))

        content.add_widget(stats_grid)

        progress_bar = Button(
            text=f"{progress}%",
            background_color=(0.2, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=25,
            font_size='14sp',
            disabled=True
        )
        progress_bar.canvas.before.clear()
        with progress_bar.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=progress_bar.pos, size=progress_bar.size)
            if progress > 0:
                Color(0.78, 0.66, 0.30, 1)
                Rectangle(
                    pos=progress_bar.pos,
                    size=(progress_bar.width * progress / 100, progress_bar.height)
                )
        progress_bar.bind(pos=self.update_progress_bar, size=self.update_progress_bar)
        self.total_progress_bar = progress_bar
        self.total_progress_value = progress

        content.add_widget(progress_bar)

        # ЗАГОЛОВОК: ПРОГРЕСС ПО ТЕГАМ
        content.add_widget(Label(
            text="[ ПРОГРЕСС ПО ТЕГАМ ]",
            font_size='16sp',
            color=get_color_from_hex('#c9a84c'),
            size_hint=(1, None),
            height=40,
            bold=True,
            halign='center',
            valign='middle',
            text_size=(Window.width - 20, None)
        ))

        all_tags = get_all_tags()
        viewed_facts = set(self.user_prefs.data["viewed_facts"])
        tag_progress = {}

        for tag in all_tags:
            facts = get_facts_by_tag(tag)
            viewed_in_tag = [f for f in facts if f["id"] in viewed_facts]
            viewed_count = len(viewed_in_tag)

            tag_progress[tag] = {
                "total": len(facts),
                "viewed": viewed_count,
                "progress": round((viewed_count / len(facts)) * 100) if len(facts) > 0 else 0
            }

        sorted_tags = sorted(tag_progress.items(), key=lambda x: x[1]["progress"], reverse=True)

        for tag, data in sorted_tags:
            if data["viewed"] == 0:
                continue

            tag_container = BoxLayout(orientation='vertical', size_hint=(1, None), height=55, spacing=3)

            tag_header = BoxLayout(size_hint=(1, 0.45))

            score = self.user_prefs.get_tag_score(tag)
            score_str = f" [+{score}]" if score > 0 else f" [{score}]" if score < 0 else " [=]"
            completed = " [Готово!]" if data["progress"] == 100 else ""

            tag_header.add_widget(Label(
                text=f"#{tag.capitalize()}{score_str}{completed}",
                font_size='14sp',
                color=(1, 1, 1, 1),
                size_hint=(1, 1),
                halign='center',
                valign='middle',
                text_size=(Window.width - 30, None)
            ))

            tag_container.add_widget(tag_header)

            p_bar = Button(
                text=f"{data['viewed']}/{data['total']}  ({data['progress']}%)",
                background_color=(0.15, 0.15, 0.15, 1),
                color=(1, 1, 1, 1),
                size_hint=(1, 0.55),
                font_size='12sp',
                disabled=True
            )
            p_bar.tag_progress = data["progress"]
            p_bar.canvas.before.clear()
            with p_bar.canvas.before:
                Color(0.15, 0.15, 0.15, 1)
                Rectangle(pos=p_bar.pos, size=p_bar.size)
                if data["progress"] > 0:
                    if data["progress"] == 100:
                        Color(0.2, 0.8, 0.2, 1)
                    else:
                        Color(0.4, 0.6, 0.9, 1)
                    Rectangle(
                        pos=p_bar.pos,
                        size=(p_bar.width * data["progress"] / 100, p_bar.height)
                    )
            p_bar.bind(pos=self.update_tag_progress_bar, size=self.update_tag_progress_bar)

            tag_container.add_widget(p_bar)
            content.add_widget(tag_container)

        # ЗАГОЛОВОК: ДОСТИЖЕНИЯ
        content.add_widget(Label(
            text="[ ДОСТИЖЕНИЯ ]",
            font_size='16sp',
            color=get_color_from_hex('#c9a84c'),
            size_hint=(1, None),
            height=40,
            bold=True,
            halign='center',
            valign='middle',
            text_size=(Window.width - 20, None)
        ))

        achievements = self.user_prefs.get_achievement_progress()
        if achievements:
            for ach in achievements:
                ach_btn = Button(
                    text=f"[+] {ach['name']} — {ach['desc']}",
                    size_hint=(1, None),
                    height=45,
                    background_color=get_color_from_hex('#2c3e50'),
                    color=(0.8, 0.8, 0.2, 1),
                    font_size='13sp',
                    halign='center',
                    valign='middle'
                )
                content.add_widget(ach_btn)
        else:
            content.add_widget(Label(
                text="Читайте факты, чтобы получать достижения!",
                font_size='14sp',
                color=(0.5, 0.5, 0.5, 1),
                size_hint=(1, None),
                height=45,
                halign='center',
                valign='middle',
                text_size=(Window.width - 20, None)
            ))

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def update_progress_bar(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=instance.pos, size=instance.size)
            if self.total_progress_value > 0:
                Color(0.78, 0.66, 0.30, 1)
                width = (self.total_progress_value / 100) * instance.width
                Rectangle(
                    pos=instance.pos,
                    size=(width, instance.height)
                )

    def update_tag_progress_bar(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            Rectangle(pos=instance.pos, size=instance.size)
            if hasattr(instance, 'tag_progress') and instance.tag_progress > 0:
                if instance.tag_progress == 100:
                    Color(0.2, 0.8, 0.2, 1)
                else:
                    Color(0.4, 0.6, 0.9, 1)
                width = (instance.tag_progress / 100) * instance.width
                Rectangle(
                    pos=instance.pos,
                    size=(width, instance.height)
                )


# ============================================================
#  НАСТРОЙКИ (переработанный layout — контент сверху)
# ============================================================

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets()
            self.user_prefs = UserPreferences()
            self.build_ui()
        else:
            self._built_once = True

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=6)

        layout.add_widget(make_header("Настройки", 
            lambda x: setattr(self.manager, 'current', 'main_menu'), 0.09))

        # ВСЁ СОДЕРЖИМОЕ В SCROLLVIEW — контент прижат к верху
        scroll = ScrollView(size_hint=(1, 0.91), bar_width=4)
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content.bind(minimum_height=content.setter('height'))

        # Заголовок раздела
        content.add_widget(Label(
            text="[ УПРАВЛЕНИЕ ДАННЫМИ ]",
            font_size='15sp',
            color=get_color_from_hex('#c9a84c'),
            bold=True,
            size_hint=(1, None),
            height=35,
            halign='center',
            valign='middle',
            text_size=(Window.width - 20, None)
        ))

        # Информация
        stats = self.user_prefs.get_user_stats()
        info_grid = GridLayout(cols=2, spacing=6, size_hint=(1, None), height=80)
        info_grid.add_widget(Label(
            text=f"Просмотрено: {stats['unique_facts_viewed']}",
            font_size='14sp',
            color=(0.9, 0.9, 0.9, 1)
        ))
        info_grid.add_widget(Label(
            text=f"Понравилось: {stats['liked_count']}",
            font_size='14sp',
            color=(0.9, 0.9, 0.9, 1)
        ))
        info_grid.add_widget(Label(
            text=f"Заметок: {len(self.user_prefs.get_all_notes())}",
            font_size='14sp',
            color=(0.9, 0.9, 0.9, 1)
        ))
        info_grid.add_widget(Label(
            text=f"Серия: {stats['streak_days']} дн.",
            font_size='14sp',
            color=(0.9, 0.7, 0.2, 1)
        ))
        content.add_widget(info_grid)

        # Кнопки управления
        clear_btn = Button(
            text="ОЧИСТИТЬ ИСТОРИЮ",
            size_hint=(1, None),
            height=55,
            background_color=(0.6, 0.2, 0.2, 0.9),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        clear_btn.bind(on_release=self.confirm_clear_history)
        content.add_widget(clear_btn)

        clear_all_btn = Button(
            text="ОЧИСТИТЬ ВСЕ ДАННЫЕ",
            size_hint=(1, None),
            height=55,
            background_color=(0.4, 0.1, 0.1, 0.8),
            color=(0.9, 0.6, 0.6, 1),
            font_size='16sp',
            bold=True
        )
        clear_all_btn.bind(on_release=self.confirm_clear_all)
        content.add_widget(clear_all_btn)

        # Разделитель
        content.add_widget(Label(
            text="",
            size_hint=(1, None),
            height=15
        ))

        # Заголовок раздела "Обновления"
        content.add_widget(Label(
            text="[ ОБНОВЛЕНИЯ ]",
            font_size='15sp',
            color=get_color_from_hex('#c9a84c'),
            bold=True,
            size_hint=(1, None),
            height=35,
            halign='center',
            valign='middle',
            text_size=(Window.width - 20, None)
        ))

        content.add_widget(Label(
            text=f"Версия приложения: {__version__}",
            font_size='14sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint=(1, None),
            height=30,
            halign='center',
            valign='middle',
            text_size=(Window.width - 20, None)
        ))

        if UPDATER_AVAILABLE:
            update_btn = Button(
                text="ПРОВЕРИТЬ ОБНОВЛЕНИЯ",
                size_hint=(1, None),
                height=55,
                background_color=get_color_from_hex('#2c3e50'),
                color=(1, 1, 1, 1),
                font_size='16sp',
                bold=True
            )
            update_btn.bind(on_release=lambda x: check_for_updates(manual=True))
            content.add_widget(update_btn)

        content.add_widget(Label(
            text="",
            size_hint=(1, None),
            height=30
        ))

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def confirm_clear_history(self, instance):
        content = BoxLayout(orientation='vertical', padding=15, spacing=15)

        content.add_widget(Label(
            text="ПОДТВЕРЖДЕНИЕ",
            font_size='18sp',
            color=get_color_from_hex('#c9a84c'),
            size_hint=(1, None),
            height=40,
            bold=True
        ))

        content.add_widget(Label(
            text="Вы действительно хотите очистить\nисторию просмотров и прогресс?\n\nПонравившиеся, заметки и рейтинг тегов\nбудут сохранены.",
            font_size='16sp',
            color=(0.9, 0.9, 0.9, 1),
            size_hint=(1, None),
            height=120,
            halign='center'
        ))

        btn_row = BoxLayout(size_hint=(1, None), height=45, spacing=10)

        cancel_btn = Button(
            text="Отмена",
            background_color=(0.3, 0.3, 0.3, 0.8),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        btn_row.add_widget(cancel_btn)

        confirm_btn = Button(
            text="Очистить",
            background_color=(0.6, 0.2, 0.2, 0.9),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        btn_row.add_widget(confirm_btn)

        content.add_widget(btn_row)

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.85, 0.5),
            background_color=(0.1, 0.1, 0.1, 0.95)
        )

        def do_clear(instance):
            self.user_prefs.clear_history()
            popup.dismiss()
            self.clear_widgets()
            self.build_ui()
            success_popup = Popup(
                title="",
                content=Label(
                    text="История очищена!\nПонравившиеся и заметки сохранены.",
                    font_size='16sp',
                    color=(0.2, 0.8, 0.2, 1),
                    halign='center'
                ),
                size_hint=(0.7, 0.25),
                background_color=(0.1, 0.1, 0.1, 0.95)
            )
            success_popup.open()
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: success_popup.dismiss(), 1.5)

        confirm_btn.bind(on_release=do_clear)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()

    def confirm_clear_all(self, instance):
        content = BoxLayout(orientation='vertical', padding=15, spacing=15)

        content.add_widget(Label(
            text="ВНИМАНИЕ!",
            font_size='20sp',
            color=(0.9, 0.2, 0.2, 1),
            size_hint=(1, None),
            height=40,
            bold=True
        ))

        content.add_widget(Label(
            text="Это действие удалит ВСЕ данные:\n"
                 "- Историю просмотров\n"
                 "- Понравившиеся\n"
                 "- Заметки\n"
                 "- Рейтинг тегов\n"
                 "- Прогресс\n\n"
                 "Восстановление будет невозможно!",
            font_size='15sp',
            color=(0.9, 0.5, 0.5, 1),
            size_hint=(1, None),
            height=180,
            halign='center'
        ))

        btn_row = BoxLayout(size_hint=(1, None), height=45, spacing=10)

        cancel_btn = Button(
            text="Отмена",
            background_color=(0.3, 0.3, 0.3, 0.8),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        btn_row.add_widget(cancel_btn)

        confirm_btn = Button(
            text="Удалить всё",
            background_color=(0.8, 0.1, 0.1, 0.9),
            color=(1, 1, 1, 1),
            font_size='16sp',
            bold=True
        )
        btn_row.add_widget(confirm_btn)

        content.add_widget(btn_row)

        popup = Popup(
            title="",
            content=content,
            size_hint=(0.85, 0.6),
            background_color=(0.1, 0.1, 0.1, 0.95)
        )

        def do_clear_all(instance):
            self.user_prefs.reset_data()
            popup.dismiss()
            self.clear_widgets()
            self.build_ui()
            success_popup = Popup(
                title="",
                content=Label(
                    text="Все данные удалены!",
                    font_size='18sp',
                    color=(0.2, 0.8, 0.2, 1),
                    halign='center'
                ),
                size_hint=(0.6, 0.2),
                background_color=(0.1, 0.1, 0.1, 0.95)
            )
            success_popup.open()
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: success_popup.dismiss(), 1.5)

        confirm_btn.bind(on_release=do_clear_all)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()


# ============================================================
#  ЭКРАН ПО ТЕГУ
# ============================================================

class TagScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_tag = None
        self.user_prefs = UserPreferences()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=6)

        header = FloatLayout(size_hint=(1, 0.10))

        self.tag_title = Label(
            text="По тегу",
            font_size='18sp',
            color=get_color_from_hex('#c9a84c'),
            bold=True,
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            halign='center',
            valign='middle',
            text_size=(Window.width - 30, None)
        )
        header.add_widget(self.tag_title)

        back_btn = Button(
            text="<--",
            size_hint=(0.15, 1),
            pos_hint={'x': 0, 'y': 0},
            background_color=(0.2, 0.2, 0.2, 0.8),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        back_btn.bind(on_release=lambda x: setattr(self.manager, 'current', 'main_menu'))
        header.add_widget(back_btn)

        layout.add_widget(header)

        scroll = ScrollView(size_hint=(1, 0.90), bar_width=4)
        self.facts_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        self.facts_box.bind(minimum_height=self.facts_box.setter('height'))

        scroll.add_widget(self.facts_box)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def set_tag(self, tag):
        self.current_tag = tag
        self.tag_title.text = f"#{tag.capitalize()}"
        self.facts_box.clear_widgets()

        all_facts = get_facts_by_tag(tag)
        viewed_facts = set(self.user_prefs.data["viewed_facts"])

        facts = [f for f in all_facts if f["id"] in viewed_facts]

        if facts:
            for fact in facts:
                status = self.user_prefs.get_fact_status(fact["id"])
                if status == "liked":
                    icon = "[★]"
                elif status == "disliked":
                    icon = "[-]"
                else:
                    icon = "[i]"

                has_note = self.user_prefs.has_note(fact["id"])
                note_icon = " [N]" if has_note else ""

                fact_btn = Button(
                    text=f"{icon}{note_icon} {_fact_label(fact, 40)}",
                    size_hint=(1, None),
                    height=55,
                    background_color=get_color_from_hex('#2c3e50'),
                    color=(1, 1, 1, 1),
                    font_size='15sp',
                    halign='center',
                    valign='middle'
                )
                fact_btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                self.facts_box.add_widget(fact_btn)
        else:
            self.facts_box.add_widget(Label(
                text=f"Нет изученных фактов по тегу '{tag}'",
                font_size='16sp',
                color=(0.5, 0.5, 0.5, 1),
                size_hint=(1, None),
                height=100,
                halign='center'
            ))

    def view_fact(self, fact):
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(fact)


# ============================================================
#  ПРИЛОЖЕНИЕ
# ============================================================

class WarFactApp(App):
    def build(self):
        sm = ScreenManager()

        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(FactScreen(name='fact_screen'))
        sm.add_widget(HistoryScreen(name='history_screen'))
        sm.add_widget(NotesScreen(name='notes_screen'))
        sm.add_widget(StatsScreen(name='stats_screen'))
        sm.add_widget(SettingsScreen(name='settings_screen'))
        sm.add_widget(TagScreen(name='tag_screen'))

        return sm


if __name__ == '__main__':
    WarFactApp().run()
