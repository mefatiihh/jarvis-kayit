#!/bin/bash
# Sıpanur Nöbet Scripti - 15:50'ye kadar çalışır
# Her 20 saniyede bir WhatsApp'ı kontrol eder
# Yeni mesaj gelirse /tmp/sipanur_msg.txt'ye yazar

WATCH_DIR="/tmp/sipanur_watch"
mkdir -p "$WATCH_DIR"
echo "NÖBET_ACTIVE=true" > "$WATCH_DIR/status.txt"

END_TIME="15:50"
LAST_CHECK_FILE="$WATCH_DIR/last_check.txt"

while true; do
    CURRENT=$(date +%H:%M)
    
    # 15:50 geçtiyse bitir
    if [[ "$CURRENT" > "$END_TIME" ]] || [[ "$CURRENT" == "$END_TIME" ]]; then
        echo "NÖBET_BITTI=true" > "$WATCH_DIR/status.txt"
        exit 0
    fi
    
    # WhatsApp snapshot al
    SNAPSHOT=$(openclaw browser snapshot 2>&1)
    
    # Sıpanur'dan gelen son mesajı bul
    # Son mesaj saati
    LAST_TIME=$(echo "$SNAPSHOT" | grep -o 'Sıpanur[^<]*[0-2][0-9]:[0-5][0-9]' | tail -1 | grep -o '[0-2][0-9]:[0-5][0-9]')
    
    if [ -n "$LAST_TIME" ]; then
        echo "$LAST_TIME" > "$LAST_CHECK_FILE"
        
        # Daha önce kaydedilmiş son saat
        PREV_TIME=""
        [ -f "$WATCH_DIR/last_msg_time.txt" ] && PREV_TIME=$(cat "$WATCH_DIR/last_msg_time.txt")
        
        # Eğer son saat değiştiyse ve yeni bir mesaj varsa
        if [ "$LAST_TIME" != "$PREV_TIME" ]; then
            # Mesaj içeriğini al (gönderen Fatih değilse - JARVIS kontrolü)
            MY_MSG_TIME=$(echo "$SNAPSHOT" | grep "JARVIS" | grep -o '[0-2][0-9]:[0-5][0-9]' | tail -1)
            
            if [ -z "$MY_MSG_TIME" ] || [ "$LAST_TIME" != "$MY_MSG_TIME" ]; then
                # Yeni mesaj geldi - içeriğini al
                MSG_CONTENT=$(echo "$SNAPSHOT" | grep -A2 "Sıpanur.*$LAST_TIME" | tail -2 | sed 's/.*text: //' | tr '\n' ' ')
                echo "$LAST_TIME|$MSG_CONTENT" > "$WATCH_DIR/new_message.txt"
                echo "YENI_MESAJ=true" > "$WATCH_DIR/status.txt"
                echo "Mesaj: $MSG_CONTENT"
                exit 0
            fi
        fi
        
        echo "$LAST_TIME" > "$WATCH_DIR/last_msg_time.txt"
    fi
    
    sleep 20
done
