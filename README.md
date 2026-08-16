# astrbot_plugin_smm2

Super Mario Maker 2 AstrBot Plugin.

Supports level/player query, random draw, bcd file download, HD level rendering, and LLM natural language calls with image recognition.

## Features

### Commands

| Command | Description | Example |
|------|------|------|
| `/smm2 <ID>` | Query level or player info | `/smm2 0c7-1bx-j2g` |
| `/rest <0-4>` | Random level draw + bcd download | `/rest 2` |
| `/bcd <ID>` | Download bcd file for a specific level | `/bcd 3FG-2K1-7HG` |
| `/render <ID>` | Render HD level images (overworld + underworld) | `/render WYQ-CPL-90H` |
| `/help` | Show help | `/help` |

ID format: 9 chars or `XXX-XXX-XXX`, case-insensitive. Queries levels first, falls back to player if not found.

### LLM Natural Language Calls

After enabling the **LLM Tools Master Switch** in the plugin config, users can trigger queries by simply talking:

| Scenario | Example | Behavior |
|------|------|------|
| Image OCR Recognition | Send a Switch screenshot | Auto-extract level ID, render HD image + return level info |
| Auto Query | "look up WYQ-CPL-90H" | Query level first, fall back to player if not found |
| Query Level Only | "look up WYQ-CPL-90H this level" | Query level only |
| Query Player Only | "look up WYQ-CPL-90H this person" | Query player only |
| Random Level | "draw a level", "give me a hard one" | Randomly draw a level of specified difficulty and return image + info |

**OCR Correction:** SMM2 IDs do not contain I, O, Z. If recognized in an image, they are auto-corrected (O→0, I→1, I→L, I→7), trying up to 3 schemes.

### Config Options

| Option | Description | Default |
|--------|------|--------|
| smm2_quality | Image quality for /smm2 and text queries (low/high) | low |
| image_quality | Image quality for image recognition results (low/high) | low |
| enable_llm_tools | **LLM Tools Master Switch** - when off, pure command mode with zero token usage | false |
| enable_ocr | Image OCR recognition (requires master switch on) | false |
| enable_llm_auto | Auto query (requires master switch on) | true |
| enable_llm_course | Query level only (requires master switch on) | true |
| enable_llm_player | Query player only (requires master switch on) | true |
| enable_llm_random | Random level draw (requires master switch on) | true |
| llm_hint | Extra hint for LLM (requires master switch on) | - |

When the master switch is off, all sub-switches are automatically hidden.

### /rest Difficulty Parameters

| Parameter | Difficulty |
|------|------|
| 0 | Any |
| 1 | Easy |
| 2 | Normal |
| 3 | Hard |
| 4 | Expert |

### toost Installation

v1.2.0 and above: toost will auto-download on first use of `/render`, no manual setup needed.

v1.1.1 (Plugin Market version): Auto-downloads toost from cloud/GitHub on first use of `/render` and extracts to the plugin directory.

Manual installation (for offline environments):

1. Go to [toost Releases](https://github.com/TheGreatRambler/toost/releases) and download `toost_windows.zip`
2. Extract and place the `toost` folder in the plugin directory (same level as `main.py`)
3. Directory structure:
   ```
   astrbot_plugin_smm2/
   ├── main.py
   ├── toost/
   │   ├── bin/toost.exe
   │   ├── fonts/
   │   └── img/
   └── ...
   ```

**Note:** toost does not support Chinese paths. Ensure the AstrBot installation path contains no Chinese characters.

## Data Sources

- Level and player data: [tgrcode.com](https://tgrcode.com/) public API
- Level rendering: [toost](https://github.com/TheGreatRambler/toost) v2.0.2

## Contact

Questions or feedback are welcome:

- QQ: 584017206
- Email: qfqfg_w@qq.com

## Image Recognition Principle

v1.2.0 supports users directly sending Switch screenshots to recognize level IDs. The full pipeline:

1. **Interceptor Trigger:** A global interceptor is registered via `@filter.regex(r".*", priority=5)` with priority higher than the LLM handler. When a message contains an `Image` component, it enters the image processing flow. Requires `enable_ocr` to be enabled in config.

2. **Text-First Extraction:** First checks if the text portion of the message already contains an ID in `XXX-XXX-XXX` format. If so, it's used directly, skipping OCR.

3. **OCR Recognition:** Image-only messages go through the OCR path:
   - Download the QQ image to a local temp file
   - Convert to `data:image/jpeg;base64,...` format
   - Iterate through all configured Chat Completion Providers to find one that supports image modality (`modalities` contains `"image"`)
   - Call `text_chat(prompt="Extract SMM2 level ID", image_urls=[base64_url])` for visual recognition
   - Extract the 9-char ID from the response text using regex

4. **OCR Correction:** SMM2 ID charset is `0-9, A-Y` (no I, O, Z). If OCR recognizes I/O/Z, corrections are applied: `O→0, I→1, I→L, I→7`, generating up to 3 candidate schemes to query the API one by one.

5. **Query and Render:** After obtaining the ID, the TGRcode API is called to query level info, then the render method is chosen based on the `image_quality` config:
   - `high`: Call toost to render overworld + underworld HD full images (2x scale, grid removed)
   - `low`: Use the thumbnail returned by TGRcode API directly

6. **Send and Cleanup:** After rendering, images are sent to the chat via `event.send()`, then `stop_event()` is called to block subsequent LLM requests, and temp files are cleaned up.

7. **Failure Fallback:** If OCR fails, no ID is extracted, or the level doesn't exist, the interceptor lets the message through to the normal LLM conversation flow without affecting other features.

**Why not use the main LLM directly?** AstrBot's fallback mechanism switches to a backup model when the main model doesn't support images, but the backup model can't access LLM tools (`tools=[]`), making function calling impossible. Therefore, the interceptor completes the full OCR → query → render pipeline before the LLM, without relying on the LLM tool chain.

## Changelog

### v1.2.1

- Added toost auto-download: auto-downloads and extracts from cloud/GitHub on first use of `/render`, no manual placement needed
- Dual-source download: cloud direct link priority (`now61.cn`), GitHub Releases fallback
- Download progress bar display, SSL certificate compatibility (auto-skip verification for domestic servers)
- toost check in LLM tools unified to `_ensure_toost()`, ensuring auto-download on first use
- Per-session download flag to avoid repeated downloads

### v1.2.0

- Added LLM Tools Master Switch (`enable_llm_tools`), pure command mode with zero token usage when off
- Added Image OCR Recognition: users send Switch screenshots, auto-extract level ID → query → render HD images
- Added LLM natural language calls (requires master switch on):
  - Image recognition (`enable_ocr`): send screenshots to auto-extract level IDs
  - Auto query (`enable_llm_auto`): user says "look up xxx", queries level first then player
  - Query level only (`enable_llm_course`): user says "look up xxx this level", queries level only
  - Query player only (`enable_llm_player`): user says "look up xxx this person", queries player only
  - Random level draw (`enable_llm_random`): user says "draw a level", "give me a hard one", randomly draws and returns image + info
- All LLM sub-switches support conditional display: sub-options auto-hidden when master switch is off
- OCR correction: SMM2 IDs don't contain I/O/Z, auto-corrected (O→0, I→L/1/7), up to 3 schemes
- LLM tools supplement `yield` result after sending images, avoiding empty LLM returns
- `/render` command changed to send only 2 HD rendered images, no longer sends bcd files
- Render logic extracted into `_do_render()` method shared by commands and LLM tools
- Config options `smm2_quality` and `image_quality` support dropdown selection

### v1.1.1

- Streamlined version for AstrBot Plugin Market (151KB)
- Removed toost large files (exe + fonts + assets), auto-downloads on first use of `/render` instead
- Dual download sources: cloud direct link priority, GitHub Releases fallback
- Download progress bar display
- SSL certificate compatibility: auto-skip certificate verification for domestic servers accessing GitHub
- Per-session download flag to avoid repeated downloads

### v1.1.0

- Added `/render <ID>` command: render HD level images (overworld + underworld) + send bcd file
- `/smm2` query results now include a `/render` command hint
- Code optimization and path portability improvements

### v1.0.1

- Initial version: `/smm2`, `/rest`, `/bcd` commands
