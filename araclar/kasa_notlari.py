"""'Kaydet' dediğin haberleri İkinci Beyin kasasına not olarak yazar.

Girdi: Artifact veritabanından dışa aktarılmış klasör (vitrin_json.py ile aynı)
    <girdi>/items/*.json     (akıştaki tüm içerikler)
    <girdi>/feedback/*.json  (senin oyların: saved true/false, note)
Çıktı: <hedef>/<haber başlığı>.md — sadece "Kaydet" (saved: true) dediklerin.

Kasa özeldir; bu yüzden vitrine gitmeyen "Neden ilginç" ve "Sen de dene" de yazılır.
Kasada zaten olan nota (akis_id aynı) hiç dokunulmaz; hiçbir şey silinmez.

Kullanım:  python3 araclar/kasa_notlari.py <girdi-klasörü> <hedef-klasör>
"""
import json
import re
import sys
from pathlib import Path

KOTU_KARAKTERLER = re.compile(r'[/\\:*?"<>|#^\[\]]')
DEFTER_ADI = ".kasa-yazilanlar.txt"  # girdi klasörünün yanında durur, depoya girmez
KIMLIK_SATIRI =re.compile(r'^akis_id:\s*"?(.*?)"?\s*$', re.MULTILINE)


def oku(klasor: Path) -> dict:
    """Bir klasördeki her JSON dosyasını {belge_kimliği: içerik} sözlüğüne çevirir."""
    sonuc = {}
    for dosya in klasor.glob("*.json"):
        belge = json.loads(dosya.read_text(encoding="utf-8"))
        sonuc[dosya.stem] = belge.get("data", belge)
    return sonuc


def mevcut_kimlikler(hedef: Path) -> set:
    """Kasadaki notların başındaki akis_id değerlerini toplar (tekrar yazmamak için)."""
    kimlikler = set()
    for dosya in hedef.glob("*.md"):
        bulunan = KIMLIK_SATIRI.search(dosya.read_text(encoding="utf-8"))
        if bulunan:
            kimlikler.add(bulunan.group(1))
    return kimlikler


def dosya_adi(baslik: str, hedef: Path) -> Path:
    """Başlıktan dosya adına uygun, çakışmayan bir yol üretir."""
    temiz = KOTU_KARAKTERLER.sub("-", baslik)
    temiz = re.sub(r"\s+", " ", temiz).strip(" .-")[:100] or "Adsız haber"
    yol, sayac = hedef / f"{temiz}.md", 2
    while yol.exists():
        yol, sayac = hedef / f"{temiz} ({sayac}).md", sayac + 1
    return yol


def not_metni(icerik: dict, oy: dict) -> str:
    # json.dumps tırnaklı değer üretir; iki nokta ya da tırnak frontmatter'ı bozamaz.
    def deger(x):
        return json.dumps(str(x or ""), ensure_ascii=False)

    satirlar = [
        "---",
        "tur: kaynak",
        "kaynak: YZ Akış",
        f"akis_id: {deger(icerik.get('id'))}",
        f"gun: {icerik.get('day', '')}",
        f"konu: {deger(icerik.get('topic'))}",
        f"yazar: {deger(icerik.get('author'))}",
        f"url: {deger(icerik.get('url'))}",
        "---",
        f"# {icerik.get('title', '')}",
        "",
        str(icerik.get("summary", "")),
        "",
    ]
    for etiket, alan in [("Neden ilginç", icerik.get("why")),
                         ("Sen de dene", icerik.get("tryIt")),
                         ("Benim notum", oy.get("note"))]:
        if alan:
            satirlar += [f"**{etiket}:** {alan}", ""]
    kaynak = " · ".join(x for x in [icerik.get("source"), icerik.get("author")] if x)
    satirlar += [f"🔗 [{kaynak or 'Kaynağa git'}]({icerik.get('url')})", "",
                 "İlgili: [[YZ Akış]]", ""]
    return "\n".join(satirlar)


def yaz(girdi: Path, hedef: Path) -> int:
    """Kaydedilen ve kasada henüz olmayan haberleri yazar; yazılan not sayısını döndürür."""
    if not (girdi / "items").is_dir() or not (girdi / "feedback").is_dir():
        return 0
    icerikler = oku(girdi / "items")
    oylar = oku(girdi / "feedback")
    hedef.mkdir(parents=True, exist_ok=True)
    # Defter: daha önce yazılan kimlikler. Not taşınsa (ör. 40 Fikirler'e) ya da
    # yeniden adlandırılsa bile aynı haber bir daha yazılmaz.
    defter = girdi.parent / DEFTER_ADI
    yazilmislar = set(defter.read_text(encoding="utf-8").split()) if defter.exists() else set()
    var_olanlar = yazilmislar | mevcut_kimlikler(hedef)

    yazilan = 0
    for kimlik in sorted(oylar):
        oy, icerik = oylar[kimlik], icerikler.get(kimlik)
        if oy.get("saved") is not True or not icerik:
            continue
        icerik = {"id": kimlik, **icerik}
        if str(icerik["id"]) in var_olanlar:
            continue
        if not str(icerik.get("url", "")).startswith("https://"):
            continue
        yol = dosya_adi(str(icerik.get("title", "")), hedef)
        yol.write_text(not_metni(icerik, oy), encoding="utf-8")
        var_olanlar.add(str(icerik["id"]))
        yazilan += 1
    defter.write_text("\n".join(sorted(var_olanlar)) + "\n", encoding="utf-8")
    return yazilan


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Kullanım: python3 araclar/kasa_notlari.py <girdi-klasörü> <hedef-klasör>")
    sayi = yaz(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"Kasa: {sayi} yeni not yazıldı.")


if __name__ == "__main__":
    main()
