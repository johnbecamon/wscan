[app]
title = WSCAN
package.name = wscan
package.domain = com.wscan

icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 14.0

requirements = python3,kivy==2.2.1,requests,urllib3,openssl,pyjnius,android,charset-normalizer,idna,certifi

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 31
android.minapi = 21
android.ndk = 25b
android.sdk = 24
android.accept_sdk_license = True

android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1