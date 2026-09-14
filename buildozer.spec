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
android.api = 30
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a
android.graphics_api = gl
android.accept_sdk_license = True
android.allow_backup = True
android.debug_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 0
