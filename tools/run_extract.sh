#!/usr/bin/env bash
set -u
cd "$(dirname "$0")/.."
python3 -u tools/extract_text.py "materials/法硕非法学-基础课" "materials/text" ocr
