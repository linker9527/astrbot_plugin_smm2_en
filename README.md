# astrbot_plugin_smm2

Super Mario Maker 2 AstrBot Plugin.

Supports level/player query, random draw, bcd file download, and HD level rendering.

## Features

### Commands

| Command | Description | Example |
|------|------|------|
| `/smm2 <ID>` | Query level or player info | `/smm2 0c7-1bx-j2g` |
| `/rest <0-4>` | Random level draw + bcd download | `/rest 2` |
| `/bcd <ID>` | Download bcd file for a specific level | `/bcd 3FG-2K1-7HG` |
| `/render <ID>` | Render HD level images (overworld + underworld) | `/render WYQ-CPL-90H` |

ID format: 9 chars or `XXX-XXX-XXX`, case-insensitive. Queries levels first, falls back to player if not found.

### /rest Difficulty Parameters

| Parameter | Difficulty |
|------|------|
| 0 | Any |
| 1 | Easy |
| 2 | Normal |
| 3 | Hard |
| 4 | Expert |

### /render Notes

Renders HD full images of the level overworld and underworld using [toost](https://github.com/TheGreatRambler/toost) v2.0.2 (2x scale, grid removed). Two PNG images are sent directly to the chat, along with the bcd file.

**Auto-install on first use:** The first time `/render` is executed, the plugin will automatically download the toost renderer and extract it to the plugin directory. Download takes some time (~17MB), check the AstrBot logs for progress. If the direct link fails, it will fall back to GitHub.

**Manual install (backup):** If auto-download fails, go to [toost Releases](https://github.com/TheGreatRambler/toost/releases) and download `toost_windows.zip`, extract it, and place the `toost` folder in the plugin directory (same level as `main.py`).

**Note:** toost does not support Chinese paths. Ensure the AstrBot installation path contains no Chinese characters.

## Data Sources

- Level and player data: [tgrcode.com](https://tgrcode.com/) public API
- Level rendering: [toost](https://github.com/TheGreatRambler/toost) v2.0.2

## Contact

Questions or feedback are welcome:

- QQ: 584017206
- Email: qfqfg_w@qq.com

## Changelog

### v1.1.1

- `/render` auto-downloads toost renderer on first use, with download progress bar
- No longer bundles toost files with the plugin, significantly reducing plugin size

### v1.1.0

- Added `/render <ID>` command: render HD level images (overworld + underworld) + send bcd file
- `/smm2` query results now include a `/render` command hint
- Code optimization and path portability improvements

### v1.0.1

- Initial version: `/smm2`, `/rest`, `/bcd` commands
