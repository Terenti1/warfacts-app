[app]
title = Факты о ВОВ
package.name = warfacts
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json
version = 1.0.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.archs = arm64-v8a
android.graphics_api = gl
android.accept_sdk_license = True
android.allow_backup = True
android.debug_artifact = apk

# ФОРСИРУЕМ версию p4a, где Python 3.10
p4a.branch = v2023.05.25

[buildozer]
log_level = 2
warn_on_root = 0
