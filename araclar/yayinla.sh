#!/bin/bash
# Vitrini günceller: akis.json'u yeniden üretir; değiştiyse GitHub'a gönderir.
# Sabah görevi bunu çalıştırır. Önce artifact verisi .disa-aktarim/ klasörüne
# dışa aktarılmış olmalı (items/ ve feedback/ alt klasörleri).
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -I araclar/vitrin_json.py .disa-aktarim

if git diff --quiet -- docs/akis.json; then
  echo "Vitrinde değişiklik yok, gönderilmedi."
  exit 0
fi

# Yalnızca akis.json kaydedilir ve gönderilir; başka hiçbir dosyaya dokunulmaz.
git commit -q -m "Vitrin: $(date +%F) güncellemesi" -- docs/akis.json
git push -q origin main
echo "Vitrin güncellendi ve GitHub'a gönderildi."
