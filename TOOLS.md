# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

### Brew Tools (Prodüksiyon)

| Araç | Versiyon | Ne işe yarar |
|------|---------|-------------|
| ffmpeg | brew | Video/ses dönüşüm, kırpma, birleştirme |
| exiftool | 13.55 | RAW/video metadata okuma |
| imagemagick | 7.1.2 | Batch thumbnail, resize (magick ile) |
| mediainfo | 26.01 | Video codec, bitrate, çözünürlük analizi |
| HandBrakeCLI | 1.11.1 | Profesyonel video encoding |
| yt-dlp | 2026.03.17 | Video indirme (YouTube, vb.) |
| rclone | 1.74.0 | Bulut/NAS dosya yönetimi |

### macOS İzinleri

| İzin | Durum |
|------|-------|
| Screen Recording | ✅ Ayarlandı |
| Accessibility | ✅ Çalışıyor |
| Calendar | ✅ Erişim var |
| Full Disk Access | Henüz gerekmedi |

### GitHub

- **Hesap:** mefatiihh
- **Repo:** jarvis-kayit (private)
- **Token:** Keychain'de kayıtlı

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

### Browser Tercihleri

- **Safari:** Basit URL açmaları (GitHub, sendgb, google drive vs.)
- **Chrome (openclaw browser):** YouTube, arama, sayfa kontrolü gereken işler
- **YouTube Premium:** Chrome profilinde oturum açık → reklamsız
