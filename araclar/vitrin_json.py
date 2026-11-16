"""Vitrin için akis.json dosyasını üretir.

Girdi: Artifact veritabanından dışa aktarılmış klasör
    <girdi>/items/*.json     (akıştaki tüm içerikler)
    <girdi>/feedback/*.json  (senin oyların: vote 1/-1/0, saved true/false)
Çıktı: docs/akis.json — sadece "İlgimi çekti" (vote 1) ya da "Kaydet" dediklerin.

Kullanım:  python3 araclar/vitrin_json.py <girdi-klasörü>
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Herkese açık sayfaya gidecek alanlar. "why" ve "tryIt" bilerek yok:
# ikisi de sana özel yazılıyor (projelerin, derslerin geçebiliyor).
# Herkese uygun öneri ayrı bir alanda: "tryPublic" → sayfada "tryIt" adıyla çıkar.
ACIK_ALANLAR = ["id", "title", "summary", "url", "source",
                "author", "lang", "topic", "day", "order"]

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / "docs" / "akis.json"


def oku(klasor: Path) -> dict:
    """Bir klasördeki her JSON dosyasını {belge_kimliği: içerik} sözlüğüne çevirir."""
    sonuc = {}
    for dosya in klasor.glob("*.json"):
        belge = json.loads(dosya.read_text(encoding="utf-8"))
        sonuc[dosya.stem] = belge.get("data", belge)
    return sonuc


def secilmis_mi(oy: dict) -> bool:
    return oy.get("vote") == 1 or oy.get("saved") is True


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Kullanım: python3 araclar/vitrin_json.py <girdi-klasörü>")
    girdi = Path(sys.argv[1])
    icerikler = oku(girdi / "items")
    oylar = oku(girdi / "feedback")

    secilenler = []
    for kimlik, oy in oylar.items():
        icerik = icerikler.get(kimlik)
        if not icerik or not secilmis_mi(oy):
            continue
        url = str(icerik.get("url", ""))
        if not url.startswith("https://"):  # güvenli olmayan bağlantıyı yayınlama
            continue
        acik = {k: icerik[k] for k in ACIK_ALANLAR if k in icerik}
        if icerik.get("tryPublic"):
            acik["tryIt"] = icerik["tryPublic"]
        secilenler.append(acik)

    # En yeni gün en üstte; aynı gün içinde akıştaki sırayla.
    secilenler.sort(key=lambda x: (x.get("order", 99), x.get("id", "")))
    secilenler.sort(key=lambda x: x.get("day", ""), reverse=True)

    # Güvenlik kemeri: dışa aktarım boş ya da bozuksa siteyi boşaltma.
    if not secilenler:
        sys.exit("Hiç seçili içerik bulunamadı; dışa aktarım eksik olabilir. akis.json değiştirilmedi.")

    # İçerik aynıysa dosyaya hiç dokunma; böylece boş yere "güncelleme" gönderilmez.
    if CIKTI.exists():
        eski = json.loads(CIKTI.read_text(encoding="utf-8")).get("icerikler")
        if eski == secilenler:
            print(f"Değişiklik yok ({len(secilenler)} içerik).")
            return

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps({
        "guncellendi": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "icerikler": secilenler,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(secilenler)} içerik yazıldı → {CIKTI.relative_to(KOK)}")


if __name__ == "__main__":
    main()
