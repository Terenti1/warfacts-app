# updater.py - Проверка обновлений через GitHub Releases

import threading
import webbrowser
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.utils import get_color_from_hex

from version import __version__

# --- Настройки ---
GITHUB_USER = "Terenti1"
GITHUB_REPO = "warfacts-app"
API_URL = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases/latest"


def _version_tuple(v):
    """'1.2.3' -> (1, 2, 3)"""
    try:
        return tuple(int(x) for x in str(v).strip().lstrip('v').split('.'))
    except Exception:
        return (0, 0, 0)


def _fetch_latest_release():
    """Возвращает (version, download_url, notes) или None при ошибке."""
    try:
        import requests
        r = requests.get(API_URL, timeout=10)
        if r.status_code != 200:
            print(f"[UPDATER] HTTP {r.status_code}")
            return None

        data = r.json()
        tag = data.get("tag_name", "").strip().lstrip('v')
        if not tag:
            return None

        notes = data.get("body", "")[:300]

        # Ищем APK в assets
        download_url = None
        for asset in data.get("assets", []):
            if asset.get("name", "").endswith(".apk"):
                download_url = asset.get("browser_download_url")
                break

        if not download_url:
            download_url = RELEASES_URL

        return {"version": tag, "download_url": download_url, "notes": notes}
    except Exception as e:
        print(f"[UPDATER] Ошибка проверки: {e}")
        return None


def check_for_updates(manual=False, parent_widget=None):
    """Проверяет обновления в фоне. Если найдёт — покажет popup."""
    def worker():
        info = _fetch_latest_release()
        if not info:
            if manual:
                Clock.schedule_once(lambda dt: _show_info_popup(
                    "Не удалось проверить обновления",
                    "Проверьте подключение к интернету."
                ), 0)
            return

        current = _version_tuple(__version__)
        latest = _version_tuple(info["version"])

        if latest > current:
            Clock.schedule_once(lambda dt: _show_update_popup(info), 0)
        elif manual:
            Clock.schedule_once(lambda dt: _show_info_popup(
                "Обновлений нет",
                f"У вас последняя версия: {__version__}"
            ), 0)

    threading.Thread(target=worker, daemon=True).start()


def _show_update_popup(info):
    """Показывает popup с предложением обновиться."""
    content = BoxLayout(orientation='vertical', padding=15, spacing=10)

    content.add_widget(Label(
        text=f"Доступно обновление {info['version']}",
        font_size='18sp',
        color=get_color_from_hex('#c9a84c'),
        bold=True,
        size_hint=(1, None),
        height=40
    ))

    content.add_widget(Label(
        text=f"Текущая версия: {__version__}",
        font_size='14sp',
        color=(0.8, 0.8, 0.8, 1),
        size_hint=(1, None),
        height=25
    ))

    if info.get("notes"):
        content.add_widget(Label(
            text=info["notes"],
            font_size='13sp',
            color=(0.7, 0.7, 0.7, 1),
            size_hint=(1, None),
            height=100
        ))

    btn_row = BoxLayout(size_hint=(1, None), height=50, spacing=10)

    later_btn = Button(
        text="Позже",
        background_color=(0.3, 0.3, 0.3, 0.8),
        color=(1, 1, 1, 1),
        font_size='16sp'
    )
    btn_row.add_widget(later_btn)

    download_btn = Button(
        text="Скачать",
        background_color=get_color_from_hex('#7a3b1e'),
        color=(1, 1, 1, 1),
        font_size='16sp',
        bold=True
    )
    btn_row.add_widget(download_btn)

    content.add_widget(btn_row)

    popup = Popup(
        title="",
        content=content,
        size_hint=(0.9, 0.5),
        background_color=(0.1, 0.1, 0.1, 0.95),
        auto_dismiss=False
    )

    def do_download(instance):
        try:
            webbrowser.open(info["download_url"])
        except Exception as e:
            print(f"[UPDATER] Не удалось открыть браузер: {e}")
        popup.dismiss()

    download_btn.bind(on_press=do_download)
    later_btn.bind(on_press=popup.dismiss)

    popup.open()


def _show_info_popup(title, message):
    """Информационный popup (для ручной проверки)."""
    content = BoxLayout(orientation='vertical', padding=15, spacing=10)

    content.add_widget(Label(
        text=title,
        font_size='18sp',
        color=get_color_from_hex('#c9a84c'),
        bold=True,
        size_hint=(1, None),
        height=40
    ))

    content.add_widget(Label(
        text=message,
        font_size='14sp',
        color=(0.9, 0.9, 0.9, 1),
        size_hint=(1, None),
        height=80
    ))

    ok_btn = Button(
        text="ОК",
        background_color=get_color_from_hex('#7a3b1e'),
        color=(1, 1, 1, 1),
        font_size='16sp',
        size_hint=(1, None),
        height=45
    )
    content.add_widget(ok_btn)

    popup = Popup(
        title="",
        content=content,
        size_hint=(0.85, 0.35),
        background_color=(0.1, 0.1, 0.1, 0.95)
    )

    ok_btn.bind(on_press=popup.dismiss)
    popup.open()
