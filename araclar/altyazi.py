"""Bir YouTube videosunun altyazısını düz metin olarak indirir.

Sabah görevi bir videoyu özetlemeden önce bunu çalıştırır; böylece özet
videonun başlığından değil, gerçekten söylenenlerden çıkar.

Kullanım:  python3 -I araclar/altyazi.py <video-kimliği>
Çıktı:     .altyazi/<video-kimliği>.txt  (depoya girmez, .gitignore'da)
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
CIKTI = KOK / ".altyazi"
# YouTube video kimliği her zaman 11 karakter: harf, rakam, - ve _.
# Başka bir şey gelirse çalıştırmıyoruz (komuta zararlı metin sızmasın diye).
KIMLIK = re.compile(r"[A-Za-z0-9_-]{11}")
DILLER = ["en", "tr"]  # sırayla denenir; ilk bulunan yeterli


def json3_metne(yol: Path) -> str:
    """YouTube'un json3 altyazı biçimini [dakika:saniye] işaretli paragraflara çevirir."""
    veri = json.loads(yol.read_text(encoding="utf-8"))
    satirlar, son_isaret = [], -60
    for olay in veri.get("events", []):
        parca = "".join(s.get("utf8", "") for s in olay.get("segs", []) or [])
        parca = parca.replace("\n", " ").strip()
        if not parca:
            continue
        saniye = olay.get("tStartMs", 0) // 1000
        if saniye - son_isaret >= 60:  # dakikada bir zaman işareti
            satirlar.append(f"\n[{saniye // 60:02d}:{saniye % 60:02d}] ")
            son_isaret = saniye
        satirlar.append(parca + " ")
    return re.sub(r"[ \t]+", " ", "".join(satirlar)).strip()


def main() -> None:
    if len(sys.argv) != 2 or not KIMLIK.fullmatch(sys.argv[1]):
        sys.exit("Kullanım: python3 -I araclar/altyazi.py <11 karakterlik video kimliği>")
    kimlik = sys.argv[1]
    CIKTI.mkdir(exist_ok=True)
    metin = ""
    for dil in DILLER:  # tek tek iste: hepsini birden istemek YouTube'da "çok istek" hatası veriyor
        with tempfile.TemporaryDirectory() as gecici:
            subprocess.run(
                ["yt-dlp", "--quiet", "--no-warnings", "--skip-download",
                 "--write-subs", "--write-auto-subs", "--sub-langs", dil,
                 "--sub-format", "json3", "-o", f"{gecici}/%(id)s",
                 f"https://www.youtube.com/watch?v={kimlik}"],
                check=False, timeout=180, stderr=subprocess.DEVNULL)
            dosyalar = sorted(Path(gecici).glob(f"{kimlik}*.json3"))
            if dosyalar:
                metin = json3_metne(dosyalar[0])
                break
    if not metin:
        sys.exit(f"{kimlik}: altyazı bulunamadı (videoda altyazı yok ya da YouTube engelledi).")
    hedef = CIKTI / f"{kimlik}.txt"
    hedef.write_text(metin, encoding="utf-8")
    print(f"{len(metin.split())} kelime yazıldı → {hedef.relative_to(KOK)}")


if __name__ == "__main__":
    main()
