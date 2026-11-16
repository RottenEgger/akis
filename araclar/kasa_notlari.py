"""'Kaydet' dediğin haberleri İkinci Beyin kasasına not olarak yazar.

Girdi: Artifact veritabanından dışa aktarılmış klasör (vitrin_json.py ile aynı)
    <girdi>/items/*.json     (akıştaki tüm içerikler)
    <girdi>/feedback/*.json  (senin oyların: saved true/false, note)
Çıktı: <hedef>/<haber başlığı>.md — sadece "Kaydet" (saved: true) dediklerin.

Kasa özeldir; bu yüzden vitrine gitmeyen "Neden ilginç" ve "Sen de dene" de yazılır.
Kasada zaten olan notta (akis_id aynı) yalnızca "Benim notum" bölümü
(işaretli iki yorum satırının arası) sayfadaki notla güncellenir; notun geri
kalanına, Obsidian'da yazdıklarına dokunulmaz. Hiçbir şey silinmez.

Kullanım:  python3 araclar/kasa_notlari.py <girdi-klasörü> <hedef-klasör>
"""
import json
import re
import sys
from pathlib import Path

KOTU_KARAKTERLER = re.compile(r'[/\\:*?"<>|#^\[\]]')
DEFTER_ADI = ".kasa-yazilanlar.txt"  # girdi klasörünün yanında durur, depoya girmez
KIMLIK_SATIRI = re.compile(r'^akis_id:\s*"?(.*?)"?\s*$', re.MULTILINE)
# Sayfadaki not kutusundan gelen bölüm bu iki satırın arasında durur.
NOT_BAS = "<!-- yz-akis-notum: bu bölüm sayfadaki not kutusundan gelir -->"
NOT_SON = "<!-- /yz-akis-notum -->"
NOT_BOLUMU = re.compile(re.escape(NOT_BAS) + r".*?" + re.escape(NOT_SON), re.DOTALL)


def oku(klasor: Path) -> dict:
    """Bir klasördeki her JSON dosyasını {belge_kimliği: içerik} sözlüğüne çevirir."""
    sonuc = {}
    for dosya in klasor.glob("*.json"):
        belge = json.loads(dosya.read_text(encoding="utf-8"))
        sonuc[dosya.stem] = belge.get("data", belge)
    return sonuc


def kasadaki_notlar(hedef: Path) -> dict:
    """Kasadaki notları {akis_id: dosya yolu} olarak bulur."""
    bulunanlar = {}
    for dosya in hedef.glob("*.md"):
        bulunan = KIMLIK_SATIRI.search(dosya.read_text(encoding="utf-8"))
        if bulunan:
            bulunanlar[bulunan.group(1)] = dosya
    return bulunanlar


def mevcut_kimlikler(hedef: Path) -> set:
    """Kasadaki notların başındaki akis_id değerlerini toplar (tekrar yazmamak için)."""
    return set(kasadaki_notlar(hedef))


def not_bolumu(metin: str) -> str:
    """Sayfadaki notu, işaretli bölüm olarak hazırlar (birden çok satır olabilir)."""
    return f"{NOT_BAS}\n**Benim notum:** {metin.strip()}\n{NOT_SON}"


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
                         ("Sen de dene", icerik.get("tryIt"))]:
        if alan:
            satirlar += [f"**{etiket}:** {alan}", ""]
    if str(oy.get("note") or "").strip():
        satirlar += [not_bolumu(str(oy["note"])), ""]
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


def notlari_guncelle(girdi: Path, hedef: Path) -> int:
    """Kasada duran notların "Benim notum" bölümünü sayfadaki notla eşitler.

    Sayfada not yoksa hiçbir şey yapılmaz (kasadaki metin silinmez). Bölüm yoksa
    notun sonuna eklenir. Güncellenen not sayısını döndürür.
    """
    if not (girdi / "feedback").is_dir() or not hedef.is_dir():
        return 0
    oylar = oku(girdi / "feedback")
    guncellenen = 0
    for kimlik, dosya in kasadaki_notlar(hedef).items():
        yeni = str((oylar.get(kimlik) or {}).get("note") or "").strip()
        if not yeni:
            continue
        eski_metin = dosya.read_text(encoding="utf-8")
        bolum = not_bolumu(yeni)
        if NOT_BOLUMU.search(eski_metin):
            yeni_metin = NOT_BOLUMU.sub(lambda _: bolum, eski_metin, count=1)
        else:
            yeni_metin = eski_metin.rstrip("\n") + "\n\n" + bolum + "\n"
        if yeni_metin != eski_metin:
            dosya.write_text(yeni_metin, encoding="utf-8")
            guncellenen += 1
    return guncellenen


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit("Kullanım: python3 araclar/kasa_notlari.py <girdi-klasörü> <hedef-klasör>")
    girdi, hedef = Path(sys.argv[1]), Path(sys.argv[2])
    sayi = yaz(girdi, hedef)
    guncellenen = notlari_guncelle(girdi, hedef)
    print(f"Kasa: {sayi} yeni not yazıldı, {guncellenen} notun 'Benim notum' bölümü güncellendi.")


if __name__ == "__main__":
    main()
