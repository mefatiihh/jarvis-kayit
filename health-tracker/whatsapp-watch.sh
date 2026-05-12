#!/bin/bash
# WhatsApp Nöbet Scripti - Sıpanur'dan gelen mesajları kontrol eder
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# WhatsApp Web chat snapshot'ında "Sıpanur" mesajlarını bul
RESULT=$(openclaw browser snapshot 2>&1)

# Son mesaj saatini bul (benim gönderdiğim mesaj 15:36 idi)
# Son gelen mesajın saatini kontrol et
LAST_MSG_TIME=$(echo "$RESULT" | grep -o 'Sıpanur.*[0-2][0-9]:[0-5][0-9]' | tail -1 | grep -o '[0-2][0-9]:[0-5][0-9]')

# Eğer son mesaj saati 15:36'dan büyükse (yani daha sonra mesaj gelmişse)
# Sadece sayısal karşılaştırma yap
if [ -n "$LAST_MSG_TIME" ]; then
    echo "Son mesaj saati: $LAST_MSG_TIME"
    
    # Son mesaj içeriğini al (benimkinden farklı mı?)
    LATEST_MSG=$(echo "$RESULT" | grep -A3 "Sıpanur.*[0-2][0-9]:[0-5][0-9]" | tail -6 | head -3)
    
    # "ben JARVIS" içeren mesaj bizim attığımız, onu atla
    HAS_NEW=$(echo "$RESULT" | grep -c "Sıpanur.*[0-2][0-9]:[0-5][0-9]" 2>/dev/null || true)
    MY_MSG=$(echo "$RESULT" | grep -c "JARVIS" 2>/dev/null || true)
    
    # Eğer toplam mesaj sayısı 1'den fazlaysa ve benimkinden sonra mesaj var
    # Basitçe: mesaj listesinde 15:37 veya sonrası var mı?
    if echo "$RESULT" | grep -q "15:3[789]\|15:4[0-9]\|15:5[0-9]\|1[6-9]:[0-5][0-9]"; then
        echo "YENI_MESAJ_VAR=true"
        echo "MESAJ:$LATEST_MSG"
    else
        echo "YENI_MESAJ_VAR=false"
    fi
else
    echo "Mesaj saati bulunamadı"
    echo "YENI_MESAJ_VAR=false"
fi
