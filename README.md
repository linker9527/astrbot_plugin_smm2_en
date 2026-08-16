# astrbot_plugin_smm2

An AstrBot plugin for **Super Mario Maker 2** (SMM2).

Supports level/player queries, random level draws, bcd file downloads, and high-definition level rendering.

## Features

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/smm2 <ID>` | Query level or player info | `/smm2 0c7-1bx-j2g` |
| `/rest <0-4>` | Random level + download bcd | `/rest 2` |
| `/bcd <ID>` | Download bcd for a specific level | `/bcd 3FG-2K1-7HG` |
| `/render <ID>` | Render HD level images (overworld + underworld) | `/render WYQ-CPL-90H` |

ID format: 9 characters or `XXX-XXX-XXX`, case-insensitive. Queries levels first, falls back to player if not found.

### /rest Difficulty Levels

| Param | Difficulty |
|-------|------------|
| 0 | Fully random |
| 1 | Easy |
| 2 | Normal |
| 3 | Hard |
| 4 | Extreme |

### /render Notes

Uses [toost](https://github.com/TheGreatRambler/toost) v2.0.2 to render HD full images of level overworld and underworld (2x scale, no grid). Two PNG images are sent directly to chat, along with the bcd file.

**Auto-install on first use:** The first time you run `/render`, the plugin automatically downloads toost from a netdisk link and extracts it to the plugin directory. No manual setup needed. If the netdisk link fails, it falls back to GitHub.

**Manual install (fallback):** If auto-download fails, download `toost_windows.zip` from [toost Releases](https://github.com/TheGreatRambler/toost/releases), then place the `toost` folder in the plugin directory (same level as `main.py`).

**Note:** toost does not support Chinese paths. Make sure your AstrBot installation path contains no Chinese characters.

## Data Sources

- Level and player data: [tgrcode.com](https://tgrcode.com/) public API
- Level rendering: [toost](https://github.com/TheGreatRambler/toost) v2.0.2

## Contact

Questions or suggestions welcome:

- QQ: 584017206
- Email: qfqfg_w@qq.com

## Changelog

### v1.1.1

- `/render` auto-downloads toost on first use, with download progress bar
- toost files no longer bundled with the plugin, significantly reducing plugin size

### v1.1.0

- Added `/render <ID>` command: render HD level images (overworld + underworld) + send bcd file
- `/smm2` query results now include a `/render` command hint
- Code optimization and portable path handling

### v1.0.1

- Initial release: `/smm2` `/rest` `/bcd` commands
