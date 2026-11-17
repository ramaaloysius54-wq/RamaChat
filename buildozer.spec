[app]
title = RamaChat
package.name = ramachat
package.domain = com.rama
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json,ttf,sql
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,httpx,websocket-client,plyer,supabase,python-dotenv
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/splash.png
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,CAMERA,POST_NOTIFICATIONS,READ_MEDIA_IMAGES,READ_MEDIA_VIDEO
android.api = 34
android.minapi = 24
android.archs = arm64-v8a
