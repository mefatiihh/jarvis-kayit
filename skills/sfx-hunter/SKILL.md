---
name: sfx-hunter
description: Find, download, organize, and manage free sound effects for video/film production. Use when the user needs cinematic SFX (whoosh, impact, riser, sub boom, ambient drone, transition sounds, foley) for their edits. Supports searching free SFX libraries, downloading packs, and organizing by category. Ideal for editors, cinematographers, and content creators who need royalty-free sound effects without paid subscriptions.
---

# SFX Hunter

Find, download, organize, and prepare free sound effects for video editing.

## Core Sources (Free, Royalty-Free)

### Tier 1 — Best Quality, No Attribution Needed

| Source | URL | Notes |
|--------|-----|-------|
| **Pixabay** | `pixabay.com/sound-effects/` | 5,000+ cinematic SFX, no attribution, bulk download |
| **Mixkit** | `mixkit.co/free-sound-effects/` | Categorized, no attribution, high quality |
| **Uppbeat** | `uppbeat.io/sfx` | Free plan: monthly download limit, very high quality |
| **Videvo** | `videvo.net/royalty-free-sound-effects/` | Free account needed, good cinematic selection |

### Tier 2 — Good Quality, Attribution May Be Required

| Source | URL | Notes |
|--------|-----|-------|
| **Freesound** | `freesound.org` | Huge community library — check license per sound, account needed to download |
| **Zapsplat** | `zapsplat.com` | Free plan: attribution required, 10 downloads/day |
| **SoundBible** | `soundbible.com` | Mixed quality, check license per sound |

### Tier 3 — YouTube Free Packs

Search YouTube for: `"free cinematic sfx pack"`, `"free sound effects pack"`, `"free whoosh pack"`.
Many editors share free packs via Google Drive links in descriptions.

**Recommended channels:**
- Proc Audio (frequent free pack releases)
- Maxwell T. (cinematic SFX)
- Sounds of the World

## SFX Categories for Cinematic Edits

| Category | Description | Search Terms |
|----------|-------------|--------------|
| **Whoosh / Swoosh** | Transition sounds, fast movement | `whoosh`, `swoosh`, `transition`, `swipe` |
| **Impact / Hit** | Heavy strikes, punches, dramatic beats | `impact`, `hit`, `strike`, `punch`, `cinematic hit` |
| **Riser** | Building tension, anticipation | `riser`, `build up`, `tension`, `rise` |
| **Sub Boom / 808** | Deep bass drops, low-end power | `sub boom`, `bass drop`, `808`, `low end` |
| **Stinger** | Short dramatic accent | `stinger`, `stab`, `accent`, `cinematic sting` |
| **Ambient Drone** | Background atmosphere, tension | `drone`, `ambient`, `atmosphere`, `texture` |
| **Reverse Cymbal** | Swell effect, transition marker | `reverse cymbal`, `swell`, `reverse` |
| **Foley** | Everyday sounds (footsteps, doors, etc.) | `foley`, `footsteps`, `door`, `rustle` |
| **Glitch / Digital** | Electronic artifacts, data corruption | `glitch`, `digital`, `error`, `robotic` |
| **Cinematic Boom** | Epic movie trailer boom | `cinematic boom`, `trailer hit`, `epic impact` |

## Workflow

### 1. Find SFX

Use `web_search` or `web_fetch` to search the sources above for the specific category.
Example search: `"pixabay sound effects whoosh"` or `"freesound cinematic impact pack"`.

For YouTube packs, use `web_search` with queries like:
- `"free cinematic sfx pack 2025"`
- `"free whoosh sound pack download"`

### 2. Download SFX

**From Pixabay / Mixkit / Uppbeat / Videvo:**
Use the browser tool (Chrome) to:
1. Navigate to the site
2. Search for the SFX category
3. Click download button
4. File saves to Downloads folder

**From YouTube:**
Use the browser tool to open the YouTube video description and find the download link.

**From direct URLs:**
Use `exec wget` or `curl` to download .mp3/.wav files.

### 3. Organize SFX

Create a folder structure:

```
~/SFX_Library/
├── Whooshes/
├── Impacts/
├── Risers/
├── Sub_Booms/
├── Stingers/
├── Ambients/
├── Foley/
├── Transitions/
└── Glitches/
```

After downloading, move files to appropriate folders.

### 4. Process with ffmpeg (Optional)

**Trim to specific length:**
```bash
ffmpeg -i input.mp3 -ss 0 -t 2 output_trimmed.mp3
```

**Normalize volume:**
```bash
ffmpeg -i input.mp3 -af "loudnorm=I=-16:LRA=11:TP=-1.5" output_normalized.mp3
```

**Convert format:**
```bash
ffmpeg -i input.wav -codec:a libmp3lame -qscale:a 2 output.mp3
```

**Fade in/out:**
```bash
ffmpeg -i input.mp3 -af "afade=t=in:ss=0:d=0.3,afade=t=out:st=2:d=0.5" output_faded.mp3
```

### 5. Preview for User

When delivering SFX to the user:
1. Download to a temp directory
2. List what you found with descriptions
3. Organize into categories
4. Offer to trim/process as needed
5. Ask where they want the final files

## Scripts

### `scripts/download_sfx.sh`
Download a sound effect from a direct URL and save to organized folder structure.

Usage:
```bash
bash scripts/download_sfx.sh <url> <category> [filename]
```

Example:
```bash
bash scripts/download_sfx.sh "https://example.com/whoosh.mp3" "Whooshes" "cinematic-whoosh-01"
```

## Response Templates

When user asks for SFX, respond with:

> **"Bakayım sana şu tarz sesleri bulayım:"**
> 1. Araştır / kategorize et
> 2. Ücretsiz kaynaklardan indir
> 3. Düzenle / trimle
> 4. Klasörle
> 5. Teslim et

Always ask the user:
- Hangi kategoride ses lazım? (whoosh, impact, riser, etc.)
- Kaç tane?
- Herhangi bir mood / vibe var mı? (epic, soft, horror, etc.)
- Nereye kaydedeyim?
