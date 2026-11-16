# YZAkis — Yapay Zekâ Seçkisi (vitrin)

Günlük yapay zekâ akışının **herkese açık, salt okunur** sayfası.

- **Mutfak (özel):** claude.ai artifact'i — oy verme, kaydetme, bağlantı ekleme orada.
- **Vitrin (bu klasör):** sadece "İlgimi çekti" ya da "Kaydet" dediğin içerikler.

## Klasörler

| Yer | Ne işe yarar |
|---|---|
| `docs/index.html` | Vitrin sayfası (düğme/form yok, sadece okur) |
| `docs/akis.json` | Sayfanın gösterdiği içerikler |
| `araclar/vitrin_json.py` | Artifact'ten dışa aktarılan veriden `akis.json` üretir |

## Gizlilik kuralı

Herkese açık dosyaya yalnızca başlık, özet, kaynak, yazar, konu, dil, gün ve
`tryPublic` (herkese uygun "Sen de dene") gider. Sana özel yazılan "Neden ilginç"
ve "Sen de dene" metinleri **gitmez**.

## Bilgisayarında açmak

```bash
python3 -m http.server 8765 --directory docs
```

Sonra tarayıcıda http://127.0.0.1:8765 adresini aç.

## Sıradaki adımlar

1. Alan adı almak.
2. GitHub deposu açıp `docs/` klasörünü GitHub Pages ya da Cloudflare Pages ile yayınlamak.
3. Sabah görevine "akis.json'u güncelle ve gönder" adımını eklemek.
