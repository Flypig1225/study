#!/usr/bin/env bash
# 下载思源黑体（Noto Sans SC）可变字体，拆成 400/500/700 三个静态字重，供 reportlab 使用。
# 用法： bash tools/guide/fetch_fonts.sh [目标目录，默认 /tmp/fonts]
set -euo pipefail
DIR="${1:-/tmp/fonts}"
PY="${PYTHON:-python3}"
# 依赖： fontTools（pip install fonttools）用于拆分可变字体字重
"$PY" -c "import fontTools" 2>/dev/null || { echo "需要 fontTools： pip install fonttools"; exit 1; }
mkdir -p "$DIR"
API="https://api.github.com/repos/google/fonts"

SHA=$(curl -s "$API/contents/ofl/notosanssc" \
  | python3 -c "import sys,json;print([f['sha'] for f in json.load(sys.stdin) if f['name'].endswith('.ttf')][0])")

if [ ! -f "$DIR/NotoSansSC.ttf" ]; then
  curl -sL -H "Accept: application/vnd.github.raw" "$API/git/blobs/$SHA" -o "$DIR/NotoSansSC.ttf"
fi

"$PY" - "$DIR" <<'PY'
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
d = sys.argv[1]
for w, name in ((400, "Regular"), (500, "Medium"), (700, "Bold")):
    f = TTFont(f"{d}/NotoSansSC.ttf")
    instantiateVariableFont(f, {"wght": w}, updateFontNames=True).save(f"{d}/NotoSansSC-{name}.ttf")
    print("ok", name)
PY
