#! /usr/bin/python3
# -*- coding: utf-8 -*-

import os
import time
import shutil

# Klasor yolu
klasor_yolu = "/var/www/html/test/data"

# Haric tutmak istediginiz dosyalar ve klasorlerin listesi


haric = ["deneme1.txt", "Test1", "Test2","deneme2.txt"]


# Gecerli Zaman
su_an = time.time()


# Klasor gezin
for oge in os.listdir(klasor_yolu):
    oge_yolu = os.path.join(klasor_yolu, oge)

    # Dosya veya klasor var mı?
    if os.path.exists(oge_yolu):
        # Haric tutulan dosyaları veya klasorleri kontrol edin
        if oge not in haric:
            # son degistirilme tarihi alma
            try:
                son_degistirme = os.path.getmtime(oge_yolu)

                # 7 gunden eski mi?
                fark = su_an - son_degistirme
                saniye = 60
                saniye_bir_gun = 60 * 60 * 24
                saniye_yedi_gun = 7 * saniye_bir_gun

                if fark >= saniye_yedi_gun:
                    print(f"Siliniyor: {oge_yolu}")
                    if os.path.isfile(oge_yolu):
                        os.remove(oge_yolu)

                    elif os.path.isdir(oge_yolu):
                        
                        shutil.rmtree(oge_yolu)
                    else:
                        print(f"{oge_yolu} ne bir dosya ne de bir klasor yoktur")

            except Exception as e:
                print(f"Hata: {e}")
