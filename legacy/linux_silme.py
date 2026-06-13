#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# [ESKİ SÜRÜM] Bu, projenin ilk Linux scriptidir ve geriye dönük
# uyumluluk için saklanmıştır. Yeni projelerde kök dizindeki
# "dosya_temizleyici.py" aracını kullanmanız önerilir (deneme modu,
# onay, log ve platform bağımsızlık içerir).
#
# Belirlenen dizinde 7 günden eski dosya/klasörleri, hariç listesi
# dışındakileri siler.

import os
import time
import shutil

# Klasör yolu
klasor_yolu = "/var/www/html/test/data"

# Hariç tutmak istediğiniz dosya ve klasörlerin listesi
haric = ["deneme1.txt", "Test1", "Test2", "deneme2.txt"]

# Geçerli zaman
su_an = time.time()

saniye_bir_gun = 60 * 60 * 24
saniye_yedi_gun = 7 * saniye_bir_gun

# Klasörü gez
for oge in os.listdir(klasor_yolu):
    oge_yolu = os.path.join(klasor_yolu, oge)

    # Dosya veya klasör var mı?
    if os.path.exists(oge_yolu):
        # Hariç tutulanları atla
        if oge not in haric:
            try:
                son_degistirme = os.path.getmtime(oge_yolu)
                fark = su_an - son_degistirme

                # 7 günden eski mi?
                if fark >= saniye_yedi_gun:
                    print(f"Siliniyor: {oge_yolu}")
                    if os.path.isfile(oge_yolu):
                        os.remove(oge_yolu)
                    elif os.path.isdir(oge_yolu):
                        shutil.rmtree(oge_yolu)
                    else:
                        print(f"{oge_yolu} ne dosya ne de klasör.")
            except Exception as e:
                print(f"Hata: {e}")

print("Silme işlemi tamamlandı.")
