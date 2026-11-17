#!/usr/bin/env bash
set -e
python3 scripts/check_project.py
buildozer android debug
ls -lh bin/*.apk
