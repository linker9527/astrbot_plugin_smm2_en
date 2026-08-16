# astrbot_plugin_smm2

AstrBot plugin for Super Mario Maker 2.

Supports level/player query, random draw, bcd download, HD level rendering, LLM natural language calls, and image OCR recognition.

## Features

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/smm2 <ID>` | Query level or player info | `/smm2 0c7-1bx-j2g` |
| `/rest <0-4>` | Random level draw + download bcd | `/rest 2` |
| `/bcd <ID>` | Download bcd file for a level | `/bcd 3FG-2K1-7HG` |
| `/render <ID>` | Render HD level images (overworld + underworld) | `/render WYQ-CPL-90H` |
| `/help` | Show help | `/help` |

ID format: 9 characters or `XXX-XXX-XXX`, case-insensitive. Queries levels first, falls back to player if not found.

### LLM Natural Language

After enabling **LLM Tool Master Switch** in plugin config, users can trigger queries in natural language without commands:

| Scenario | Example | Behavior |
|----------|---------|----------|
| Image OCR | Send Switch screenshot | Auto-extract level ID, render HD image + return info |
| Fuzzy query | "Query WYQ-CPL-90H" | Query level first, fall back to player |
| Level only | "Query WYQ-CPL-90H this level" | Query level only |
| Player only | "Query WYQ-CPL-90H this player" | Query player only |
| Random draw | "Draw a level", "Give me a hard one" | Random draw by difficulty |

**OCR Correction:** SMM2 IDs do not contain I/O/Z. Auto-correct O->0, I->1/L/7, up to 3 attempts.

### Configuration

| Config | Description | Default |
|--------|-------------|---------|
| smm2_quality | Image quality for /smm2 and text queries (low/high) | low |
| image_quality | Image quality for image recognition (low/high) | low |
| enable_llm_tools | **LLM Tool Master Switch**, disable for command-only mode | false |
| enable_ocr | Image OCR (requires master switch) | false |
| enable_llm_auto | Fuzzy query (requires master switch) | true |
| enable_llm_course | Level query only (requires master switch) | true |
| enable_llm_player | Player query only (requires master switch) | true |
| enable_llm_random | Random draw (requires master switch) | true |
| llm_hint | Extra LLM hint (requires master switch) | - |

### /rest Difficulty

| Param | Difficulty |
|-------|------------|
| 0 | Random |
| 1 | Easy |
| 2 | Normal |
| 3 | Hard |
| 4 | Extreme |

### toost Installation

v1.1.1: toost auto-downloads on first `/render` use from GitHub official source (SHA256 verified), no manual setup needed.

Manual install (offline):

1. Download `toost_windows.zip` from [toost Releases](https://github.com/TheGreatRambler/toost/releases)
2. Extract and place `toost` folder in plugin directory (same level as `main.py`)
3. Structure:
   ```
   astrbot_plugin_smm2/
   ├── main.py
   ├── toost/
   │   ├── bin/toost.exe
   │   ├── fonts/
   │   └── img/
   └── ...
   ```

**Note:** toost does not support Chinese paths.

## Data Sources

- Level & player data: [tgrcode.com](https://tgrcode.com/) public API
- Level rendering: [toost](https://github.com/TheGreatRambler/toost) v2.0.2

## Contact

- QQ: 584017206
- Email: qfqfg_w@qq.com

## Changelog

### v1.1.1

- Market release (151KB, stripped of toost binaries)
- toost auto-download on first `/render` use
- Dual download source: GitHub Releases (official) first, `now61.com` fallback
- SHA256 hash verification to prevent supply chain tampering
- TLS certificate verification enabled
- Download progress bar
- Per-session download flag to avoid re-downloads