"""kasa_notlari.py için testler.  Çalıştır:  python3 -m unittest test_kasa_notlari -v"""
import json
import tempfile
import unittest
from pathlib import Path

import kasa_notlari as kn


def icerik(kimlik, baslik, url="https://ornek.com/a", **ek):
    veri = {"id": kimlik, "title": baslik, "url": url, "summary": "Özet: kısa.",
            "why": "Çünkü güzel.", "tryIt": "Şunu dene.", "topic": "claude",
            "author": "Ayşe", "day": "2026-11-14", "source": "Blog"}
    veri.update(ek)
    return veri


class KasaNotlariTesti(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        kok = Path(self._tmp.name)
        self.girdi, self.hedef = kok / "disa", kok / "kasa"
        (self.girdi / "items").mkdir(parents=True)
        (self.girdi / "feedback").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def ekle(self, veri, oy):
        kimlik = veri["id"]
        (self.girdi / "items" / f"{kimlik}.json").write_text(json.dumps(veri), encoding="utf-8")
        (self.girdi / "feedback" / f"{kimlik}.json").write_text(json.dumps({"data": oy}), encoding="utf-8")

    def notlar(self):
        return sorted(self.hedef.glob("*.md")) if self.hedef.exists() else []

    def test_sadece_kaydedilenler_yazilir(self):
        self.ekle(icerik("a", "Kaydedilen"), {"saved": True, "vote": 0, "note": "Derste dene"})
        self.ekle(icerik("b", "Sadece beğenilen"), {"saved": False, "vote": 1})
        self.assertEqual(kn.yaz(self.girdi, self.hedef), 1)
        [dosya] = self.notlar()
        self.assertEqual(dosya.name, "Kaydedilen.md")
        metin = dosya.read_text(encoding="utf-8")
        for parca in ["Özet: kısa.", "**Neden ilginç:** Çünkü güzel.", "**Sen de dene:** Şunu dene.",
                      "**Benim notum:** Derste dene", kn.NOT_BAS, kn.NOT_SON, "İlgili: [[YZ Akış]]", 'akis_id: "a"']:
            self.assertIn(parca, metin)

    def test_https_olmayan_yazilmaz(self):
        self.ekle(icerik("a", "Güvensiz", url="javascript:alert(1)"), {"saved": True})
        self.assertEqual(kn.yaz(self.girdi, self.hedef), 0)

    def test_ikinci_calistirma_yeni_dosya_yazmaz_ve_dokunmaz(self):
        self.ekle(icerik("a", "Bir haber"), {"saved": True})
        kn.yaz(self.girdi, self.hedef)
        [dosya] = self.notlar()
        dosya.write_text("Barış düzenledi", encoding="utf-8")
        self.assertEqual(kn.yaz(self.girdi, self.hedef), 0)
        self.assertEqual(dosya.read_text(encoding="utf-8"), "Barış düzenledi")

    def test_tasinan_not_yeniden_yazilmaz(self):
        self.ekle(icerik("a", "Fikre dönüştü"), {"saved": True})
        kn.yaz(self.girdi, self.hedef)
        [dosya] = self.notlar()
        dosya.rename(dosya.parent.parent / "baska-klasore-tasindi.md")
        self.assertEqual(kn.yaz(self.girdi, self.hedef), 0)
        self.assertEqual(self.notlar(), [])

    def test_dosya_adina_uymayan_karakterler(self):
        self.ekle(icerik("a", 'Soru: A/B "test" #1 [yeni]?'), {"saved": True})
        kn.yaz(self.girdi, self.hedef)
        [dosya] = self.notlar()
        for kotu in '/\\:*?"<>|#^[]':
            self.assertNotIn(kotu, dosya.stem)

    def test_ayni_baslikli_iki_haber(self):
        self.ekle(icerik("a", "Aynı"), {"saved": True})
        self.ekle(icerik("b", "Aynı"), {"saved": True})
        self.assertEqual(kn.yaz(self.girdi, self.hedef), 2)
        self.assertEqual([d.name for d in self.notlar()], ["Aynı (2).md", "Aynı.md"])

    def test_frontmatter_iki_nokta_ve_tirnakla_bozulmaz(self):
        self.ekle(icerik("a", "Başlık", author='Ali: "usta"'), {"saved": True})
        kn.yaz(self.girdi, self.hedef)
        metin = self.notlar()[0].read_text(encoding="utf-8")
        self.assertIn('yazar: "Ali: \\"usta\\""', metin)

    def test_sonradan_eklenen_not_kasaya_eklenir(self):
        self.ekle(icerik("a", "Bir haber"), {"saved": True})
        kn.yaz(self.girdi, self.hedef)
        [dosya] = self.notlar()
        dosya.write_text(dosya.read_text(encoding="utf-8") + "Obsidian'da yazdığım satır\n", encoding="utf-8")
        self.ekle(icerik("a", "Bir haber"), {"saved": True, "note": "Projeme bağla"})
        self.assertEqual(kn.notlari_guncelle(self.girdi, self.hedef), 1)
        metin = dosya.read_text(encoding="utf-8")
        self.assertIn("Obsidian'da yazdığım satır", metin)
        self.assertIn("**Benim notum:** Projeme bağla", metin)
        self.assertEqual(kn.notlari_guncelle(self.girdi, self.hedef), 0)  # aynıysa dokunmaz

    def test_degisen_not_sadece_kendi_bolumunu_degistirir(self):
        self.ekle(icerik("a", "Bir haber"), {"saved": True, "note": "İlk not"})
        kn.yaz(self.girdi, self.hedef)
        [dosya] = self.notlar()
        dosya.write_text("Üstte kendi yazım\n" + dosya.read_text(encoding="utf-8"), encoding="utf-8")
        self.ekle(icerik("a", "Bir haber"), {"saved": True, "note": "İkinci not\nikinci satır"})
        self.assertEqual(kn.notlari_guncelle(self.girdi, self.hedef), 1)
        metin = dosya.read_text(encoding="utf-8")
        self.assertTrue(metin.startswith("Üstte kendi yazım"))
        self.assertNotIn("İlk not", metin)
        self.assertIn("**Benim notum:** İkinci not\nikinci satır", metin)
        self.assertEqual(metin.count(kn.NOT_BAS), 1)

    def test_sayfada_not_silinirse_kasadaki_silinmez(self):
        self.ekle(icerik("a", "Bir haber"), {"saved": True, "note": "Kalsın"})
        kn.yaz(self.girdi, self.hedef)
        self.ekle(icerik("a", "Bir haber"), {"saved": True, "note": ""})
        self.assertEqual(kn.notlari_guncelle(self.girdi, self.hedef), 0)
        self.assertIn("Kalsın", self.notlar()[0].read_text(encoding="utf-8"))

    def test_disa_aktarim_yoksa_sifir(self):
        self.assertEqual(kn.yaz(self.girdi / "yok", self.hedef), 0)


if __name__ == "__main__":
    unittest.main()
