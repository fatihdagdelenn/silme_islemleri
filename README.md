# 🧹 silme_islemleri

> Belirtilen bir dizinde **belirli bir günden eski** dosya ve klasörleri,
> istediğiniz öğeleri hariç tutarak **güvenli biçimde** temizleyen Python aracı.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)]()
[![License](https://img.shields.io/badge/License-GPL--3.0-green.svg)](LICENSE)

---

## İçindekiler

- [Ne işe yarar?](#ne-işe-yarar)
- [Neler değişti? (sürüm 2.0)](#neler-değişti-sürüm-20)
- [Kurulum](#kurulum)
- [Hızlı başlangıç](#hızlı-başlangıç)
- [Tüm seçenekler](#tüm-seçenekler)
- [Yapılandırma dosyası](#yapılandırma-dosyası)
- [Zamanlanmış çalıştırma](#zamanlanmış-çalıştırma-cron--görev-zamanlayıcı)
- [Güvenlik notları](#güvenlik-notları)
- [Eski sürümler](#eski-sürümler)
- [Lisans](#lisans)

---

## Ne işe yarar?

Sunucularda biriken geçici dosyalar, eski yedekler, log birikintileri ya da
"test/data" gibi klasörler zamanla disk doldurur. `dosya_temizleyici.py` bir
dizine bakar, belirlediğiniz **yaş eşiğinden eski** öğeleri bulur ve hariç
tuttuklarınız dışındakileri siler.

En önemli farkı: **silmeden önce ne yapacağını gösterir.** Önce `--dry-run`
ile çalıştırır, sonucu görür, ardından gerçek silmeyi yaparsınız.

---

## Neler değişti? (sürüm 2.0)

Proje, biri Linux biri Windows için iki ayrı scriptten oluşuyordu. Artık
hepsi **tek, platform bağımsız bir araçta** birleşti:

| Önce | Sonra |
|------|-------|
| `linux_silme.py` + `windows_silme.py` (iki kopya) | Tek `dosya_temizleyici.py` (Linux/Windows/macOS) |
| Yol, gün, hariç listesi **koda gömülü** | Komut satırı argümanları + JSON config |
| Önizleme yok | **`--dry-run` deneme modu** |
| Onay yok, geri dönüş yok | Silmeden önce **onay sorusu** |
| Çıktı yalınamıyor | Konsol + isteğe bağlı **log dosyası** |
| Özet yok | Sonunda **kaç öğe / ne kadar alan** özeti |
| `windows_silme.py`'de `saniye_yedi_gun = 7 * saniye_yedi_gun` **hatası** | Düzeltildi |
| Kök dizin koruması yok | `/`, `C:\`, ev dizini gibi yollara **koruma** |

Eski scriptler silinmedi; düzeltilmiş halleriyle [`legacy/`](legacy/) klasöründe duruyor.

---

## Kurulum

Ek bir bağımlılık yok — yalnızca Python 3.8+ standart kütüphanesini kullanır.

```bash
git clone https://github.com/fatihdagdelenn/silme_islemleri.git
cd silme_islemleri
python3 dosya_temizleyici.py --help
```

---

## Hızlı başlangıç

> **Altın kural:** Yeni bir dizinde her zaman önce `--dry-run` ile deneyin.

```bash
# 1) Önce deneme modu — hiçbir şey silinmez, sadece liste gösterilir
python3 dosya_temizleyici.py /var/www/html/test/data --days 7 --dry-run

# 2) İyi görünüyorsa gerçek silme (program onay soracaktır)
python3 dosya_temizleyici.py /var/www/html/test/data --days 7 \
    --exclude deneme1.txt Test1 "*.log"

# 3) Otomasyon için onayı atla
python3 dosya_temizleyici.py /var/www/html/test/data --days 30 --yes
```

Windows'ta da aynı araç çalışır:

```powershell
python dosya_temizleyici.py "C:\Users\User\Desktop\Test" --days 7 --dry-run
```

---

## Tüm seçenekler

| Seçenek | Açıklama |
|---------|----------|
| `path` | Temizlenecek dizin yolu (zorunlu, ya da `--config` ile verilir). |
| `--days N` | Bu günden eski öğeler silinir. Varsayılan: **7**. |
| `-e, --exclude ...` | Hariç tutulacak ad/desen listesi. Glob destekler: `*.log`, `yedek_*`. |
| `--dry-run` | **Deneme modu:** hiçbir şey silmez, ne olacağını gösterir. |
| `--yes` | Onay sorusunu atlar (zamanlanmış görevler için). |
| `--time-field {mtime,ctime}` | Yaş ölçütü: değiştirilme zamanı (varsayılan) veya durum değişimi. |
| `--force` | Kritik dizin korumasını devre dışı bırakır (dikkatli kullanın). |
| `--log DOSYA` | İşlemleri ayrıca bu dosyaya yazar. |
| `--config DOSYA` | JSON yapılandırma dosyasından ayarları okur. |
| `-q, --quiet` | Yalnızca uyarı ve hataları gösterir. |
| `-v, --verbose` | Ayrıntılı (debug) çıktı. |
| `--version` | Sürümü gösterir. |

---

## Yapılandırma dosyası

Aynı ayarları tekrar tekrar yazmak yerine bir JSON dosyasında tutabilirsiniz.
Örnek: [`ornek_config.json`](ornek_config.json)

```json
{
  "path": "/var/www/html/test/data",
  "days": 7,
  "time_field": "mtime",
  "exclude": ["deneme1.txt", "Test1", "*.log", "yedek_*"]
}
```

Kullanımı:

```bash
python3 dosya_temizleyici.py --config ornek_config.json --dry-run
```

Komut satırında verilen değerler, config dosyasındaki değerleri ezer.

---

## Zamanlanmış çalıştırma (cron / Görev Zamanlayıcı)

**Linux — her gece 03:00'te:**

```cron
0 3 * * * /usr/bin/python3 /opt/silme_islemleri/dosya_temizleyici.py \
    /var/www/html/test/data --days 7 --yes \
    --log /var/log/temizleyici.log
```

**Windows — Görev Zamanlayıcı (Task Scheduler):**

```
Program : python
Argüman : C:\araclar\dosya_temizleyici.py "C:\inetpub\temp" --days 7 --yes --log C:\loglar\temizleyici.log
```

---

## Güvenlik notları

- **Geri alınamaz.** Silinen dosyalar çöp kutusuna gitmez; doğrudan kaldırılır.
  Bu yüzden ilk çalıştırmayı her zaman `--dry-run` ile yapın.
- Araç; `/`, sürücü kökü (`C:\`), ev dizini ve `/etc`, `/usr`, `/var` gibi
  kritik klasörlerde çalışmayı **reddeder**. Bilinçli olarak gerekliyse
  `--force` ile geçersiz kılabilirsiniz.
- Sembolik bağlantılar (symlink) takip edilmez; bağlantının kendisi silinir,
  işaret ettiği hedef korunur.
- Önemli verilerinizi her zaman `--exclude` ile koruma altına alın.

---

## Eski sürümler

Projenin ilk hali olan ayrı scriptler [`legacy/`](legacy/) klasöründedir:

- [`legacy/linux_silme.py`](legacy/linux_silme.py)
- [`legacy/windows_silme.py`](legacy/windows_silme.py) — bilinen `NameError`
  hatası düzeltilmiş haliyle.

Bunlar referans amaçlıdır; yeni kullanımda `dosya_temizleyici.py` önerilir.

---

## Lisans

Bu proje [GPL-3.0](LICENSE) lisansı altında dağıtılmaktadır.
