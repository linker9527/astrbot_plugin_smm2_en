# -*- coding: utf-8 -*-
"""
AstrBot Plugin: SMM2 (Super Mario Maker 2)
Level query / Player query / Random draw / bcd download / Level rendering
"""
import asyncio
import gzip
import os
import re
import subprocess
import zipfile
from typing import Optional

import aiohttp

from astrbot.api.star import Star, Context, register
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Plain, Image, File
from astrbot.api.all import MessageChain
from astrbot.api import logger


# ============ API Constants ============

API_BASE = "https://tgrcode.com/mm2"
LEVEL_INFO = f"{API_BASE}/level_info"
THUMB_URL = f"{API_BASE}/level_entire_thumbnail"
LEVEL_DATA = f"{API_BASE}/level_data"
USER_INFO = f"{API_BASE}/user_info"
GET_POSTED = f"{API_BASE}/get_posted"
GET_LIKED = f"{API_BASE}/get_liked"
GET_PLAYED = f"{API_BASE}/get_played"
GET_FIRST_CLEARED = f"{API_BASE}/get_first_cleared"
GET_WORLD_RECORD = f"{API_BASE}/get_world_record"
SEARCH_ENDLESS = f"{API_BASE}/search_endless_mode"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://tgrcode.com/",
    "Accept": "application/json, text/plain, */*",
}

MAX_RETRIES = 5
RETRY_DELAY = 2

# toost renderer path (in plugin directory)
_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
TOOST_EXE = os.path.join(_PLUGIN_DIR, "toost", "bin", "toost.exe")
TOOST_WORK = os.path.join(_PLUGIN_DIR, "toost")
TOOST_RENDER = os.path.join(TOOST_WORK, "render")

TOOST_DOWNLOAD_URLS = [
    "https://github.com/TheGreatRambler/toost/"
    "releases/latest/download/toost_windows.zip",
    "https://www.now61.com/f/kVz6Ty/toost_windows.zip",  # backup
]
TOOST_ZIP_PATH = os.path.join(_PLUGIN_DIR, "_tmp", "toost_windows.zip")
TOOST_DOWNLOADED = False
TOOST_SHA256 = "953B1018CE3F23020D3D5292C636898EF4D735622C6B927497C4ED5C0DC9C075"


async def _ensure_toost():
    """If toost does not exist, try downloading from GitHub then backup"""
    global TOOST_DOWNLOADED
    if TOOST_DOWNLOADED:
        return True
    if os.path.exists(TOOST_EXE):
        TOOST_DOWNLOADED = True
        return True

    os.makedirs(os.path.join(_PLUGIN_DIR, "_tmp"), exist_ok=True)

    for url in TOOST_DOWNLOAD_URLS:
        if not url:
            continue
        source = "GitHub" if "github.com" in url else "backup"
        logger.info(f"[SMM2] toost not found, downloading from {source}...")
        ok = await _download_toost(url)
        if ok:
            TOOST_DOWNLOADED = True
            logger.info(f"[SMM2] toost downloaded from {source}")
            return True
        logger.warning(f"[SMM2] Download from {source} failed, trying next source...")

    logger.error("[SMM2] All download sources failed")
    return False


async def _download_toost(url):
    """Download toost from the given URL, verify SHA256, and extract"""
    try:
        # Clean up any leftover partial zip
        if os.path.exists(TOOST_ZIP_PATH):
            os.unlink(TOOST_ZIP_PATH)

        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=180) as r:
                if r.status != 200:
                    logger.error(f"[SMM2] Failed to download toost HTTP {r.status}")
                    return False
                total = int(r.headers.get("Content-Length", "0"))
                downloaded = 0
                bar_len = 30
                with open(TOOST_ZIP_PATH, "wb") as f:
                    async for chunk in r.content.iter_chunked(8192):
                        downloaded += len(chunk)
                        f.write(chunk)
                        if total > 0:
                            pct = downloaded / total
                            filled = int(bar_len * pct)
                            bar = "#" * filled + "." * (bar_len - filled)
                            kb = downloaded / 1024
                            kb_total = total / 1024
                            logger.info(
                                f"[SMM2] toost download [{bar}] {pct:.0%} "
                                f"({kb:.0f}/{kb_total:.0f} KB)"
                            )

        # SHA256 verification
        import hashlib
        sha = hashlib.sha256()
        with open(TOOST_ZIP_PATH, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha.update(chunk)
        file_hash = sha.hexdigest().upper()
        if file_hash != TOOST_SHA256:
            logger.error(f"[SMM2] SHA256 mismatch! Expected {TOOST_SHA256}, got {file_hash}")
            try:
                os.unlink(TOOST_ZIP_PATH)
            except Exception:
                pass
            return False
        logger.info(f"[SMM2] SHA256 verified: {file_hash}")

        with zipfile.ZipFile(TOOST_ZIP_PATH, "r") as z:
            z.extractall(os.path.join(_PLUGIN_DIR, "toost"))
        try:
            os.unlink(TOOST_ZIP_PATH)
        except Exception:
            pass

        if os.path.exists(TOOST_EXE):
            return True
        logger.error("[SMM2] toost exe not found after extraction")
        return False
    except Exception as e:
        logger.error(f"[SMM2] Failed to download toost: {e}")
        return False


# ============ Utility Functions ============

def parse_id(raw: str) -> Optional[str]:
    raw = raw.strip()
    m = re.search(r"[0-9A-Za-z]{3}-[0-9A-Za-z]{3}-[0-9A-Za-z]{3}", raw)
    if m:
        return m.group(0).upper().replace("-", "")
    m = re.search(r"[0-9A-Za-z]{9}", raw)
    if m:
        return m.group(0).upper()
    return None


async def api_get(session: aiohttp.ClientSession, url: str, *, as_json: bool = True):
    last_err = ""
    for i in range(MAX_RETRIES):
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=30)) as r:
                if r.status == 429:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                if r.status != 200:
                    last_err = await r.text()
                    return {"_status": r.status, "_body": last_err}
                if as_json:
                    return await r.json()
                return await r.read()
        except asyncio.TimeoutError:
            await asyncio.sleep(RETRY_DELAY)
            continue
        except Exception as e:
            last_err = str(e)
            await asyncio.sleep(RETRY_DELAY)
            continue
    return {"_status": 429, "_body": "max retries exceeded"}


async def fetch_level(session, pure_id):
    data = await api_get(session, f"{LEVEL_INFO}/{pure_id}")
    if data and isinstance(data, dict) and "_status" not in data:
        return data
    return None


async def fetch_player(session, mid):
    user_data = await api_get(session, f"{USER_INFO}/{mid}")
    lists = {"posted": [], "liked": [], "played": [], "first_clear": [], "wr": []}
    if user_data and isinstance(user_data, dict) and "_status" not in user_data:
        for key, endpoint in [("posted", GET_POSTED), ("liked", GET_LIKED),
                               ("played", GET_PLAYED), ("first_clear", GET_FIRST_CLEARED),
                               ("wr", GET_WORLD_RECORD)]:
            try:
                d = await api_get(session, f"{endpoint}/{mid}")
                if d and isinstance(d, dict) and "_status" not in d:
                    lists[key] = d.get("courses", []) or []
            except Exception:
                pass
    return user_data, lists


async def download_bcd(session, pure_id, cache_dir):
    raw = await api_get(session, f"{LEVEL_DATA}/{pure_id}", as_json=False)
    if not raw or isinstance(raw, dict):
        return None
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    os.makedirs(cache_dir, exist_ok=True)
    fpath = os.path.join(cache_dir, f"{pure_id}.bcd")
    with open(fpath, "wb") as f:
        f.write(raw)
    return fpath


def fmt_courses(courses, limit=5):
    if not courses:
        return "No data"
    parts = []
    for c in courses[:limit]:
        cid = c.get("course_id") or "?"
        cname = c.get("name") or "Unnamed"
        cl = c.get("likes") or 0
        cr = c.get("clear_rate_pretty") or c.get("clear_rate") or "N/A"
        parts.append(f"ID: {cid} | Name: {cname} | Likes: {cl} | Clear Rate: {cr}")
    if len(courses) > limit:
        parts.append(f"... {len(courses)} total")
    return "\n".join(parts)


def _send_text(event, text):
    return event.send(MessageChain([Plain(text)]))


# ============ Plugin Main Class ============

@register(
    "astrbot_plugin_smm2_en",
    "linker9527",
    "Super Mario Maker 2 level/player query, random draw, bcd download, level rendering",
    "1.1.3",
    "https://github.com/linker9527/astrbot_plugin_smm2_en",
)
class Smm2Plugin(Star):
    def __init__(self, context: Context, config=None):
        super().__init__(context)
        self.config = config or {}
        self._tmp_dir = os.path.join(_PLUGIN_DIR, "_tmp")
        os.makedirs(self._tmp_dir, exist_ok=True)
        os.makedirs(TOOST_RENDER, exist_ok=True)

    # ---------- /smm2 ----------

    @filter.command("smm2", priority=1)
    async def cmd_smm2(self, event: AstrMessageEvent, id: str = ""):
        """Query SMM2 level or player"""
        text = event.get_message_str() or ""
        pure_id = parse_id(text)
        if not pure_id:
            await _send_text(event, "Usage: /smm2 <level or player ID> (9 chars or XXX-XXX-XXX)")
            return
        pure_id = pure_id.upper()

        async with aiohttp.ClientSession() as s:
            level = await fetch_level(s, pure_id)
            if level:
                body = self._fmt_level(pure_id, level)
                body += f"\n\nRender HD images: /render {pure_id[0:3]}-{pure_id[3:6]}-{pure_id[6:9]}"
                img_url = f"{THUMB_URL}/{pure_id}"
                try:
                    await event.send(MessageChain([Plain(body), Image(file=img_url, url=img_url)]))
                except Exception as e:
                    await _send_text(event, body)
                return

            user_data, lists = await fetch_player(s, pure_id)
            if user_data and isinstance(user_data, dict) and "_status" not in user_data:
                body = self._fmt_player(pure_id, user_data, lists)
                await _send_text(event, body)
                return

        await _send_text(event, f"ID {pure_id} does not exist (level/player not found)")

    def _fmt_level(self, pure_id, d):
        lines = [
            "📊 Level Info",
            f"Level ID: {pure_id}",
            f"Level Name: {d.get('name') or 'Unnamed'}",
            f"Maker ID: {d.get('maker_id') or 'No data'}",
            f"Total Plays: {d.get('courses_played') or 'No data'}",
            f"Likes / Boos: {d.get('likes') or 0} / {d.get('dislikes') or 0}",
        ]
        cr = d.get("clear_rate")
        if cr is not None:
            try:
                lines.append(f"Clear Rate: {float(cr):.2f}%")
            except (ValueError, TypeError):
                lines.append(f"Clear Rate: {cr}%")
        else:
            lines.append("Clear Rate: No data")
        lines.append(f"Versus: Total {d.get('battle_total') or 'N/A'}, Wins {d.get('battle_win') or 'N/A'}")
        return "\n".join(lines)

    def _fmt_player(self, mid, u, lists):
        lines = ["👤 Player Info", f"Player ID: {mid}", f"Player Name: {u.get('name') or 'Unnamed'}"]
        mii = u.get("mii_image") or u.get("mii_img_url") or u.get("mii_avatar") or ""
        if mii:
            lines.append(f"Mii Avatar: {mii}")
        lines.append(f"Total Uploaded Levels: {u.get('uploaded_levels') or 'No data'}")
        lines.append(f"Maker Points: {u.get('maker_points') or 0}")
        lines.append(f"Total Likes: {u.get('likes') or 'No data'}")
        lines.append(f"Total Boos: {u.get('boos') or 'No data'}")
        lines.append(f"Total Plays: {u.get('courses_played') or 'No data'}")
        lines.append(f"Total Clears: {u.get('courses_cleared') or 'No data'}")
        lines.append(f"Total Deaths: {u.get('courses_deaths') or 'No data'}")
        lines.append(f"Versus Rank: {u.get('versus_rank_name') or 'No rank'}")
        tb = u.get("versus_plays") or 0
        bw = u.get("versus_won") or 0
        bl = u.get("versus_lost") or 0
        wr_pct = "0.00%" if tb == 0 else f"{(bw / tb * 100):.2f}%"
        lines.append(f"Total Versus Plays: {tb}")
        lines.append(f"Versus Wins: {bw}")
        lines.append(f"Versus Losses: {bl}")
        lines.append(f"Versus Win Rate: {wr_pct}")
        acr = u.get("total_clear_rate")
        lines.append(f"Overall Clear Rate: {acr}%" if acr else "Overall Clear Rate: No data")
        lines.append(f"World Records Held: {u.get('world_records', 0)}")
        lines.append(f"First Clears: {u.get('first_clears', 0)}")
        lines.append("")
        lines.append("📤 Uploaded Levels")
        lines.append(fmt_courses(lists["posted"]))
        lines.append("")
        lines.append("❤️ Liked Levels")
        lines.append(fmt_courses(lists["liked"]))
        lines.append("")
        lines.append("🎮 Played Levels")
        lines.append(fmt_courses(lists["played"]))
        lines.append("")
        lines.append("🏆 First Clears")
        lines.append(fmt_courses(lists["first_clear"]))
        lines.append("")
        lines.append("🌟 World Record Levels")
        lines.append(fmt_courses(lists["wr"]))
        return "\n".join(lines)

    # ---------- /rest ----------

    @filter.command("rest", priority=1)
    async def cmd_rest(self, event: AstrMessageEvent, mode: str = ""):
        """Random level draw with bcd download"""
        text = event.get_message_str() or ""
        m = re.search(r"\d", text)
        if not m and not mode:
            await _send_text(event, "Usage: /rest <0-4>\n0=Any 1=Easy 2=Normal 3=Hard 4=Expert")
            return
        try:
            mode_int = int(mode or m.group(0))
        except (ValueError, AttributeError):
            await _send_text(event, "Difficulty range: 0-4")
            return
        if mode_int not in (0, 1, 2, 3, 4):
            await _send_text(event, "Difficulty range: 0-4")
            return

        diff_map = {0: "Any", 1: "Easy", 2: "Normal", 3: "Hard", 4: "Expert"}
        api_diff = {0: "", 1: "e", 2: "n", 3: "ex", 4: "sex"}
        await _send_text(event, f"⏳ Drawing a {diff_map[mode_int]} level...")

        async with aiohttp.ClientSession() as s:
            qs = f"?difficulty={api_diff[mode_int]}" if api_diff[mode_int] else ""
            data = await api_get(s, f"{SEARCH_ENDLESS}{qs}")
            if not data or (isinstance(data, dict) and "_status" in data):
                await _send_text(event, "Draw failed, please try again later")
                return

            pure_id, cname = self._extract_first_id(data)
            if not pure_id:
                await _send_text(event, "No level list retrieved")
                return
            pure_id = pure_id.upper().replace("-", "")

            await _send_text(event, f"Drew level {pure_id}, downloading bcd file...")
            fpath = await download_bcd(s, pure_id, self._tmp_dir)
            if not fpath:
                await _send_text(event, f"bcd file download failed for level {pure_id}")
                return

            await self._send_bcd_file(event, pure_id, cname, fpath)

    @staticmethod
    def _extract_first_id(data):
        if isinstance(data, list) and data:
            first = data[0]
            return (first.get("course_id") or first.get("id"), first.get("name")) if isinstance(first, dict) else (first, "")
        if isinstance(data, dict):
            for key in ("courses", "data", "results", "levels"):
                if isinstance(data.get(key), list) and data[key]:
                    first = data[key][0]
                    return (first.get("course_id") or first.get("id"), first.get("name")) if isinstance(first, dict) else (first, "")
            cid = data.get("course_id") or data.get("id")
            return (cid, data.get("name"))
        return ("", "")

    # ---------- /bcd ----------

    @filter.command("bcd", priority=1)
    async def cmd_bcd(self, event: AstrMessageEvent, id: str = ""):
        """Download bcd file for a specific level"""
        text = event.get_message_str() or ""
        pure_id = parse_id(text)
        if not pure_id:
            await _send_text(event, "Usage: /bcd <level ID>")
            return
        pure_id = pure_id.upper()

        await _send_text(event, f"⏳ Downloading bcd file for level {pure_id}...")

        async with aiohttp.ClientSession() as s:
            level = await fetch_level(s, pure_id)
            cname = level.get("name") if level else ""
            fpath = await download_bcd(s, pure_id, self._tmp_dir)
            if not fpath:
                await _send_text(event, f"bcd file download failed for level {pure_id}")
                return
            await self._send_bcd_file(event, pure_id, cname, fpath)

    # ---------- /render ----------

    @filter.command("render", priority=1)
    async def cmd_render(self, event: AstrMessageEvent, id: str = ""):
        """Render HD level images (overworld + underworld)"""
        text = event.get_message_str() or ""
        pure_id = parse_id(text)
        if not pure_id:
            await _send_text(event, "Usage: /render <level ID>\nRenders overworld and underworld HD images")
            return
        pure_id = pure_id.upper()

        if not os.path.exists(TOOST_EXE):
            downloaded = await _ensure_toost()
            if not downloaded:
                await _send_text(event, "Renderer toost auto-download failed, please try again later")
                return

        await _send_text(event, f"⏳ Rendering images for level {pure_id}...")

        async with aiohttp.ClientSession() as s:
            raw = await api_get(s, f"{LEVEL_DATA}/{pure_id}", as_json=False)
            if not raw or isinstance(raw, dict):
                await _send_text(event, f"bcd download failed for level {pure_id}")
                return

            if raw[:2] == b"\x1f\x8b":
                try:
                    raw = gzip.decompress(raw)
                except Exception:
                    pass

            bcd_path = os.path.join(TOOST_RENDER, f"{pure_id}.bcd")
            with open(bcd_path, "wb") as f:
                f.write(raw)

            ow_path = os.path.join(TOOST_RENDER, f"{pure_id}_ow.png")
            sw_path = os.path.join(TOOST_RENDER, f"{pure_id}_sw.png")

            cmd = [TOOST_EXE, "-p", bcd_path, "-a", "2", "-r", "-o", ow_path, "-s", sw_path]
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=60, cwd=TOOST_WORK,
                                        encoding="utf-8", errors="replace")
                if result.returncode != 0:
                    await _send_text(event, f"Render failed: {result.stderr or result.stdout}")
                    try: os.unlink(bcd_path)
                    except: pass
                    return
            except subprocess.TimeoutExpired:
                await _send_text(event, "Render timed out")
                try: os.unlink(bcd_path)
                except: pass
                return

            level = await fetch_level(s, pure_id)
            label = level.get("name") if level else ""

            # Send images
            chains = []
            if os.path.exists(ow_path) and os.path.getsize(ow_path) > 100:
                chains.append(MessageChain([Image(file=ow_path)]))
            if os.path.exists(sw_path) and os.path.getsize(sw_path) > 100:
                chains.append(MessageChain([Image(file=sw_path)]))

            sent_ow = False
            sent_sw = False
            for i, chain in enumerate(chains):
                try:
                    await event.send(chain)
                    if i == 0:
                        sent_ow = True
                    else:
                        sent_sw = True
                except Exception as e:
                    logger.error(f"[SMM2] Failed to send image: {e}")

            msg = f"{pure_id} ({label})" if label else f"{pure_id}"
            msg += " ✅ Overworld" if sent_ow else " ❌ Overworld"
            msg += " + Underworld done" if sent_sw else " + Underworld"
            await _send_text(event, msg)

            # Send bcd
            sent_bcd = False
            try:
                await event.send(MessageChain([
                    Plain(f"Level {pure_id} bcd file"),
                    File(name=f"{pure_id}.bcd", file=bcd_path),
                ]))
                sent_bcd = True
            except Exception as e:
                logger.error(f"[SMM2] bcd send failed: {e}")

            # Cleanup all
            for fp in [bcd_path, ow_path, sw_path]:
                try: os.unlink(fp)
                except: pass

    # ---------- File Sending ----------

    async def _send_bcd_file(self, event, pure_id, cname, fpath):
        label = cname or pure_id
        try:
            await event.send(
                MessageChain([
                    Plain(f"Level {pure_id} ({label}) bcd file"),
                    File(name=f"{pure_id}.bcd", file=fpath),
                ])
            )
        except Exception as e:
            logger.error(f"[SMM2] Failed to send bcd file: {e}")
            await _send_text(event, f"bcd file send failed: {e}")
        finally:
            try:
                os.remove(fpath)
            except OSError as e:
                logger.error(f"[SMM2] Failed to delete temp file: {e}")
