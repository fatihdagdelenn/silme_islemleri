import os
import time
import shutil

# Örnek Klasör yolu
klasor_yolu = "C:\\Users\\User\\Desktop\\Test"

# Hariç tutmak istediğiniz dosyaların ve klasörlerin listesi
haric = ["deneme1.txt", "Test1", "Test2","deneme2.txt"]

# Geçerli zamanı alın
su_an = time.time()


#print(su_an)



# Klasörü gezin
for oge in os.listdir(klasor_yolu):
    oge_yolu = os.path.join(klasor_yolu, oge)
    
    # Dosya veya klasör mü?
    if os.path.exists(oge_yolu):
        
        # Hariç tutulan dosyaları veya klasörleri kontrol edin
        if oge not in haric:
            
            
            # oge=ogenin son değiştirilme tarihini alın
            try:
                son_degistirme = os.path.getmtime(oge_yolu)
                #print(son_degistirme)
                
                
                # 7 günden eski mi?
                fark = su_an - son_degistirme
                saniye = 60
                saniye_bir_gun = 60 * 60 * 24
                saniye_yedi_gun = 7 * saniye_yedi_gun
                
                
                if fark >= saniye_yedi_gun:
                    print(f"Siliniyor: {oge_yolu}")
                    
                    
                    if os.path.isfile(oge_yolu):
                        os.remove(oge_yolu)
                    elif os.path.isdir(oge_yolu):
                        #os.rmdir(oge_yolu)
                        shutil.rmtree(oge_yolu)              
                    else:                        
                        print(f"{oge_yolu} ne bir dosya ne de bir klasördür.")
                    
                    
                    
            except Exception as e:
                print(f"Hata: {e}")




print("Silme işlemi tamamlandı.")
