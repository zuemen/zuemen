#!/usr/bin/env bash
# 把 projects.py 的每個場景算成兩種用途的檔案（輸出到 repo 的 assets/manim/）
#
#   <slug>.gif          GitHub README 用：640px、15fps、調色盤最佳化
#   <slug>.mp4          zuemen.net /projects 用：1080p H.264、faststart
#   <slug>.webp         網站封面（取動畫結尾、內容最完整的那一格）
#   <slug>-preview.mp4  網站首頁循環預覽：720p、無聲、檔案更小
#
# 用法：bash manim/render.sh            → 全部
#       bash manim/render.sh chainlens  → 只算一個
set -euo pipefail
cd "$(dirname "$0")"
OUT=../assets/manim
mkdir -p "$OUT"

# slug → Scene 類別名稱（與 projects.py 的 SCENES 一致）
declare -A SCENES=(
  [chainlens]=ChainLens [evidence-at-source]=EvidenceAtSource [medssi]=MedSSI
  [chaintrust]=ChainTrust [pepefi]=PepeFi [rwa-tokenization]=RWATokenization
  [qml-simulation]=QMLSimulation
)
targets=("${@:-${!SCENES[@]}}")

for slug in "${targets[@]}"; do
  cls=${SCENES[$slug]}
  echo "▶ $slug ($cls)"
  # 1) 只算一次：1080p30
  manim --progress_bar none -r 1920,1080 --frame_rate 30 --disable_caching -o "$slug" projects.py "$cls" >/dev/null
  src=media/videos/projects/1080p30/$slug.mp4
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$src")

  # 2) 網站完整版：H.264 + faststart（瀏覽器邊下載邊播）
  ffmpeg -v error -y -i "$src" -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p -movflags +faststart -an "$OUT/$slug.mp4"
  # 3) 網站首頁循環預覽：720p、壓得更小
  ffmpeg -v error -y -i "$src" -vf scale=1280:-2 -c:v libx264 -preset veryfast -crf 28 -pix_fmt yuv420p -movflags +faststart -an "$OUT/$slug-preview.mp4"
  # 4) 封面：結尾淡出前 1.2 秒那一格
  ffmpeg -v error -y -ss "$(python3 -c "print(max($dur-1.2,0))")" -i "$src" -frames:v 1 -vf scale=1280:-2 -c:v libwebp -quality 82 "$OUT/$slug.webp"
  # 5) README 用 GIF：先產生全片共用調色盤，再套用（避免 Manim 直出 GIF 的色帶與巨大檔案）
  ffmpeg -v error -y -i "$src" -vf "fps=15,scale=640:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" "$OUT/$slug.gif"
done
ls -la "$OUT"
