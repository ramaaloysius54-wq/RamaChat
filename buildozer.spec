[app]
title = RamaChat
package.name = ramachat
package.domain = com.rama
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,ttf,sql
source.include_patterns = assets/*,screens/*.py,services/*.py,utils/*.py,database/*.py
version = 1.0.0

# requirements asli lu, gue tambahin dependensi supabase biar gak crash pas login
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,httpx,websocket-client,plyer,supabase,python-dotenv,postgrest,gotrue,storage3,realtime

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/splash.png
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,CAMERA,POST_NOTIFICATIONS,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO,ACCESS_NETWORK_STATE,READ_CONTACTS,RECORD_AUDIO,VIBRATE

# --- FIX ERROR LICENSE TADI ---
android.api = 33
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

android.logcat_filters = *:S python:D

[buildozer]
log_level = 1
warn_on_root = 1