#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dosya_temizleyici.py
====================

Belirtilen bir dizinde, belirli bir günden ESKİ dosya ve klasörleri;
istediğiniz dosya/klasörleri hariç tutarak güvenli biçimde temizler.

Linux, Windows ve macOS uyumludur.

Öne çıkan özellikler
--------------------
* Komut satırından tam yapılandırma (kod düzenlemeye gerek yok)
* --dry-run (deneme modu): hiçbir şey silmeden ne olacağını gösterir
* Silmeden önce onay sorar (--yes ile atlanabilir)
* Glob desenli hariç tutma listesi (örn. "*.log", "yedek_*")
* İsteğe bağlı log dosyası
* Sonunda özet: kaç öğe silindi ve ne kadar yer açıldı
* Kök dizin (/ veya C:\\) gibi tehlikeli yollara karşı koruma

Örnek kullanım
--------------
    # Önce mutlaka deneme modunda çalıştırın:
    python dosya_temizleyici.py /var/www/html/test/data --days 7 --dry-run

    # Gerçek silme (onay sorar):
    python dosya_temizleyici.py /var/www/html/test/data --days 7 \\
        --exclude deneme1.txt Test1 "*.log"

    # Yapılandırma dosyasıyla:
    python dosya_temizleyici.py --config ornek_config.json --dry-run

Lisans: GPL-3.0
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path

__version__ = "2.0.0"

logger = logging.getLogger("dosya_temizleyici")


# --------------------------------------------------------------------------- #
# Yardımcı fonksiyonlar
# --------------------------------------------------------------------------- #
def insan_okur_boyut(bayt: int) -> str:
    """Bayt değerini okunabilir bir metne çevirir (örn. 12.4 MB)."""
    deger = float(bayt)
    for birim in ("B", "KB", "MB", "GB", "TB", "PB"):
        if deger < 1024.0:
            return f"{deger:.1f} {birim}"
        deger /= 1024.0
    return f"{deger:.1f} EB"


def yol_boyutu(yol: Path) -> int:
    """Bir dosyanın ya da klasörün (içeriği dahil) toplam boyutunu döndürür."""
    if yol.is_file() or yol.is_symlink():
        try:
            return yol.stat(follow_symlinks=False).st_size
        except OSError:
            return 0
    toplam = 0
    for kok, _klasorler, dosyalar in os.walk(yol, onerror=lambda e: None):
        for ad in dosyalar:
            try:
                toplam += os.path.getsize(os.path.join(kok, ad))
            except OSError:
                pass
    return toplam


def haric_mi(ad: str, haric_desenleri: list[str]) -> bool:
    """Verilen ad, hariç tutma desenlerinden herhangi biriyle eşleşiyor mu?"""
    return any(fnmatch.fnmatch(ad, desen) for desen in haric_desenleri)


def tehlikeli_yol_mu(yol: Path) -> bool:
    """Kök dizin gibi felakete yol açabilecek hedefleri yakalar."""
    cozulmus = yol.resolve()
    # Kök dizin: Linux/mac "/", Windows "C:\\"
    if cozulmus == cozulmus.anchor and cozulmus.parent == cozulmus:
        return True
    if str(cozulmus) in ("/", cozulmus.anchor):
        return True
    # Kullanıcının ev dizini ve birkaç kritik sistem klasörü
    hassas = {Path.home().resolve()}
    for ortak in ("/", "/etc", "/usr", "/var", "/bin", "/boot", "/lib", "/root"):
        hassas.add(Path(ortak))
    return cozulmus in hassas


# --------------------------------------------------------------------------- #
# Çekirdek mantık
# --------------------------------------------------------------------------- #
def silinecekleri_topla(
    klasor_yolu: Path,
    esik_saniye: float,
    su_an: float,
    haric: list[str],
    zaman_alani: str,
) -> list[Path]:
    """Silinmeye aday öğelerin listesini döndürür (henüz silmez)."""
    adaylar: list[Path] = []
    try:
        ogeler = sorted(os.listdir(klasor_yolu))
    except OSError as hata:
        logger.error("Dizin okunamadı: %s (%s)", klasor_yolu, hata)
        return adaylar

    for oge in ogeler:
        if haric_mi(oge, haric):
            logger.debug("Hariç tutuldu: %s", oge)
            continue

        oge_yolu = klasor_yolu / oge
        if not oge_yolu.exists() and not oge_yolu.is_symlink():
            continue

        try:
            durum = oge_yolu.stat(follow_symlinks=False)
            zaman = durum.st_ctime if zaman_alani == "ctime" else durum.st_mtime
        except OSError as hata:
            logger.warning("Bilgi alınamadı: %s (%s)", oge_yolu, hata)
            continue

        if (su_an - zaman) >= esik_saniye:
            adaylar.append(oge_yolu)

    return adaylar


def oge_sil(oge_yolu: Path, deneme: bool) -> bool:
    """Tek bir dosya/klasörü siler. Deneme modunda yalnızca raporlar."""
    if deneme:
        return True
    try:
        if oge_yolu.is_symlink() or oge_yolu.is_file():
            oge_yolu.unlink()
        elif oge_yolu.is_dir():
            shutil.rmtree(oge_yolu)
        else:
            logger.warning("%s ne dosya ne de klasör; atlandı.", oge_yolu)
            return False
        return True
    except Exception as hata:  # noqa: BLE001 - kullanıcıya tüm hatayı göster
        logger.error("Silinemedi: %s (%s)", oge_yolu, hata)
        return False


def calistir(ayarlar: argparse.Namespace) -> int:
    """Ana akış. Çıkış kodunu döndürür (0 = başarılı)."""
    klasor_yolu = Path(ayarlar.path).expanduser()

    if not klasor_yolu.exists():
        logger.error("Belirtilen yol bulunamadı: %s", klasor_yolu)
        return 2
    if not klasor_yolu.is_dir():
        logger.error("Belirtilen yol bir klasör değil: %s", klasor_yolu)
        return 2
    if tehlikeli_yol_mu(klasor_yolu) and not ayarlar.force:
        logger.error(
            "GÜVENLİK: '%s' kritik bir dizin gibi görünüyor. "
            "Gerçekten istiyorsanız --force ekleyin.",
            klasor_yolu,
        )
        return 3

    esik_saniye = ayarlar.days * 24 * 60 * 60
    su_an = time.time()

    logger.info("Hedef dizin : %s", klasor_yolu)
    logger.info("Eşik        : %s günden eski", ayarlar.days)
    logger.info("Zaman ölçütü: %s", ayarlar.time_field)
    if ayarlar.exclude:
        logger.info("Hariç       : %s", ", ".join(ayarlar.exclude))
    if ayarlar.dry_run:
        logger.info(">>> DENEME MODU: hiçbir şey silinmeyecek <<<")

    adaylar = silinecekleri_topla(
        klasor_yolu, esik_saniye, su_an, ayarlar.exclude, ayarlar.time_field
    )

    if not adaylar:
        logger.info("Silinecek öğe bulunamadı. ✔")
        return 0

    toplam_boyut = 0
    logger.info("%d öğe silinmeye aday:", len(adaylar))
    for oge in adaylar:
        boyut = yol_boyutu(oge)
        toplam_boyut += boyut
        tur = "DİZİN " if oge.is_dir() else "DOSYA "
        logger.info("  [%s] %s (%s)", tur, oge.name, insan_okur_boyut(boyut))

    logger.info("Tahmini boşalacak alan: %s", insan_okur_boyut(toplam_boyut))

    if ayarlar.dry_run:
        logger.info("Deneme modu tamamlandı. Gerçek silme için --dry-run'ı kaldırın.")
        return 0

    if not ayarlar.yes:
        try:
            cevap = input(f"\n{len(adaylar)} öğe silinecek. Onaylıyor musunuz? [e/H] ")
        except EOFError:
            cevap = ""
        if cevap.strip().lower() not in ("e", "evet", "y", "yes"):
            logger.info("İşlem iptal edildi.")
            return 0

    silinen, basarisiz, silinen_boyut = 0, 0, 0
    for oge in adaylar:
        boyut = yol_boyutu(oge)
        if oge_sil(oge, deneme=False):
            silinen += 1
            silinen_boyut += boyut
            logger.info("Silindi: %s", oge)
        else:
            basarisiz += 1

    logger.info("-" * 48)
    logger.info("Tamamlandı. Silinen: %d | Başarısız: %d | Açılan alan: %s",
                silinen, basarisiz, insan_okur_boyut(silinen_boyut))
    return 0 if basarisiz == 0 else 1


# --------------------------------------------------------------------------- #
# Yapılandırma & argümanlar
# --------------------------------------------------------------------------- #
def config_yukle(yol: str) -> dict:
    """JSON yapılandırma dosyasını okur."""
    try:
        with open(yol, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as hata:
        print(f"Yapılandırma dosyası okunamadı: {hata}", file=sys.stderr)
        sys.exit(2)


def argumanlari_ayrıştir(argv: list[str] | None = None) -> argparse.Namespace:
    ayrıştırıcı = argparse.ArgumentParser(
        prog="dosya_temizleyici.py",
        description="Belirli bir günden eski dosya/klasörleri güvenle temizler.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Örnek:\n"
        "  python dosya_temizleyici.py /yol/dizin --days 7 --dry-run\n"
        '  python dosya_temizleyici.py /yol/dizin -e "*.log" yedek_ --yes',
    )
    ayrıştırıcı.add_argument("path", nargs="?", help="Temizlenecek dizin yolu.")
    ayrıştırıcı.add_argument("--days", type=int, default=7,
                             help="Bu günden eski öğeler silinir (varsayılan: 7).")
    ayrıştırıcı.add_argument("-e", "--exclude", nargs="*", default=[],
                             help="Hariç tutulacak ad/desen listesi (glob destekler).")
    ayrıştırıcı.add_argument("--dry-run", action="store_true",
                             help="Deneme modu: hiçbir şey silmez, sadece gösterir.")
    ayrıştırıcı.add_argument("--yes", action="store_true",
                             help="Onay sorusunu atla (dikkatli kullanın).")
    ayrıştırıcı.add_argument("--time-field", choices=("mtime", "ctime"),
                             default="mtime",
                             help="Yaş ölçütü: değiştirilme (mtime) ya da durum "
                                  "değişimi (ctime). Varsayılan: mtime.")
    ayrıştırıcı.add_argument("--force", action="store_true",
                             help="Kritik dizin koruması dahil zorla çalıştır.")
    ayrıştırıcı.add_argument("--log", metavar="DOSYA",
                             help="İşlemleri bu dosyaya da yaz.")
    ayrıştırıcı.add_argument("--config", metavar="DOSYA",
                             help="JSON yapılandırma dosyası.")
    ayrıştırıcı.add_argument("-q", "--quiet", action="store_true",
                             help="Yalnızca uyarı ve hataları göster.")
    ayrıştırıcı.add_argument("-v", "--verbose", action="store_true",
                             help="Ayrıntılı (debug) çıktı.")
    ayrıştırıcı.add_argument("--version", action="version",
                             version=f"%(prog)s {__version__}")

    ayarlar = ayrıştırıcı.parse_args(argv)

    # Config dosyası komut satırı için varsayılan değer sağlar.
    if ayarlar.config:
        cfg = config_yukle(ayarlar.config)
        if ayarlar.path is None:
            ayarlar.path = cfg.get("path")
        if "days" in cfg and "--days" not in (argv or sys.argv):
            ayarlar.days = cfg.get("days", ayarlar.days)
        if not ayarlar.exclude:
            ayarlar.exclude = cfg.get("exclude", [])
        ayarlar.time_field = cfg.get("time_field", ayarlar.time_field)

    if not ayarlar.path:
        ayrıştırıcı.error("Bir dizin yolu vermelisiniz (ya path argümanı ya da --config).")

    return ayarlar


def loglama_kur(ayarlar: argparse.Namespace) -> None:
    seviye = logging.INFO
    if ayarlar.quiet:
        seviye = logging.WARNING
    if ayarlar.verbose:
        seviye = logging.DEBUG

    logger.setLevel(logging.DEBUG)
    bicim = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s",
                              datefmt="%Y-%m-%d %H:%M:%S")

    konsol = logging.StreamHandler(sys.stdout)
    konsol.setLevel(seviye)
    konsol.setFormatter(bicim)
    logger.addHandler(konsol)

    if ayarlar.log:
        dosya = logging.FileHandler(ayarlar.log, encoding="utf-8")
        dosya.setLevel(logging.DEBUG)
        dosya.setFormatter(bicim)
        logger.addHandler(dosya)


def main(argv: list[str] | None = None) -> int:
    ayarlar = argumanlari_ayrıştir(argv)
    loglama_kur(ayarlar)
    try:
        return calistir(ayarlar)
    except KeyboardInterrupt:
        logger.warning("Kullanıcı tarafından durduruldu.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
