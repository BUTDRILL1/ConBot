# ConBot — Technical Architecture Document

**Version:** 1.0
**Status:** Approved for development
**Last updated:** 2026-06-17

---

## 1. System Overview

ConBot is a Python CLI application distributed via PyPI/pipx. It has no server component and no network dependency at runtime. It orchestrates three external engines (pandoc, ffmpeg, LibreOffice headless) plus two in-process Python libraries (Pillow, pandas/openpyxl) depending on the conversion requested.

```
┌─────────────────────────────────────────────┐
│                  conbot (CLI)                 │
│  ┌──────────┐  ┌───────────┐  ┌────────────┐ │
│  │  menu.py │  │bootstrap.py│  │format_graph│ │
│  │ (nav     │  │ (dep check,│  │.py (valid  │ │
│  │  engine) │  │  OS detect)│  │  pairs)    │ │
│  └────┬─────┘  └─────┬──────┘  └─────┬──────┘ │
│       └───────────────┴───────────────┘       │
│                       │                        │
│              ┌────────┴────────┐               │
│              │  engines/ registry│              │
│              └────────┬────────┘               │
│      ┌────────┬───────┼───────┬────────┐       │
│      ▼        ▼       ▼       ▼        ▼       │
│  documents  images  video   audio  spreadsheets│
│  (pandoc +  (Pillow) (ffmpeg)(ffmpeg)(pandas + │
│  LibreOffice)                       LibreOffice)│
└─────────────────────────────────────────────┘
         │            │           │
         ▼            ▼           ▼
   [pandoc binary][ffmpeg binary][soffice binary]
    (system-installed, not bundled)
```

## 2. Distribution & Packaging

- **Build system:** `pyproject.toml`, `[build-system]` table using setuptools (or flit_core), no `setup.py`.
- **Entry point:** `[project.scripts] conbot = "conbot.__main__:main"`.
- **Install method:** `pipx install conbot`. pipx creates an isolated venv for ConBot and symlinks the `conbot` command onto the user's PATH. This handles all Python-level dependency installation (questionary, rich, Pillow, pillow-heif, pandas, openpyxl) automatically — no custom bootstrap code is needed for this layer.
- **System binaries (pandoc, ffmpeg, LibreOffice):** never installed by pipx/pip, since they are not Python packages. ConBot detects their presence at runtime and instructs the user to install them via their OS package manager. ConBot never executes privileged install commands itself.

## 3. Module Structure

```
conbot/
├── __main__.py          # entry point; calls bootstrap check then menu loop
├── bootstrap.py          # dependency detection, OS/package-manager detection, caching
├── menu.py                # stack-based navigation engine (questionary-driven)
├── format_graph.py        # extension→category map + CONVERSION_RULES matrix (§4 below)
├── engines/
│   ├── __init__.py        # ENGINES registry: dict[str, Callable[[Path, Path], ConversionResult]]
│   ├── documents.py       # pandoc + LibreOffice subprocess wrappers
│   ├── images.py           # Pillow + pillow-heif wrapper
│   ├── video.py             # ffmpeg subprocess wrapper, remux/transcode decision logic
│   ├── audio.py             # ffmpeg subprocess wrapper, quality defaults
│   └── spreadsheets.py    # pandas + LibreOffice wrapper
├── ui.py                   # banner, progress bars, warning prompts (rich)
├── process_control.py      # Ctrl+C handling, subprocess lifecycle, background detach
├── pyproject.toml
└── tests/
    └── (engine-level tests against real sample files, see §7)
```

## 4. Conversion Engine Matrix

Engine assignment is per **specific pair**, not per category — verified against real test files during the research phase, not assumed from documentation alone.

| Source | Target | Engine | Notes |
|---|---|---|---|
| `.md` | `.pdf`, `.docx`, `.html`, `.epub` | pandoc | Pandoc's core competency |
| `.docx` | `.pdf` | LibreOffice headless | Layout fidelity > pandoc's PDF-via-LaTeX route |
| `.doc` | any | LibreOffice headless | Pandoc cannot read legacy `.doc` at all |
| `.docx` | `.epub` | pandoc | **Warn user**: custom Word paragraph styles flatten to generic tags, headings may not map correctly |
| `.odt`, `.rtf` | any | LibreOffice headless | |
| `.xlsx`, `.ods` | `.pdf` | LibreOffice headless | |
| `.xls` | any | LibreOffice headless | openpyxl cannot open legacy `.xls` |
| `.xlsx` | `.csv` | pandas | **Warn user**: dates may become serial numbers; multi-sheet workbooks fan out to one CSV per sheet |
| `.csv` | `.xlsx` | pandas | Low risk, adding structure not losing it |
| Image (any Pillow-supported) | Image (any Pillow-supported) | Pillow + pillow-heif | In-process, no subprocess overhead |
| Video container change, compatible codec | same codec, new container | ffmpeg, `-c copy` (remux) | Verified: ~20x realtime speed, lossless |
| Video codec change required | — | ffmpeg, full transcode | Verified: can be 0.05–0.3x realtime depending on target codec; user is warned before running |
| Any video | HEVC output | ffmpeg, `-tag:v hvc1` | Required for Apple/QuickTime playback compatibility; default `hev1` tag is rejected by iOS/QuickTime |
| Audio (lossy/lossless) | `.mp3` | ffmpeg, `-c:a libmp3lame -q:a 2` | VBR; verified higher perceptual quality per file size than maxed CBR `-b:a 320k` |
| Audio | `.flac` | ffmpeg, `-compression_level 5` | Balanced default, not slowest/smallest |
| Audio | `.wav` | ffmpeg | Verified channel count and sample rate preserved without forced resampling |

### 4.1 Remux-vs-transcode decision logic (video)

```
1. Attempt: ffmpeg -i <src> -c copy <dst>
2. If ffmpeg stderr contains "Could not write header" / codec incompatibility message:
     → fall back to full transcode with codec-appropriate flags
     → inform user this will take longer than a remux
3. If step 1 succeeds: done, near-instant
```
This was verified directly against a real Android-shot H.264/AAC mp4 file: remux to `.mkv` completed in 0.37s at 20.8x realtime; forced transcode to `.webm` (VP9/Opus) took 11.5s at 0.27x realtime on the same 3-second clip. ffmpeg fails cleanly (non-zero exit, descriptive stderr) on an incompatible `-c copy` attempt rather than producing a corrupt file — confirmed by deliberately forcing H.264 into a WebM container.

### 4.2 Metadata handling (video and audio)

Verified against real files: ffmpeg copies container-level metadata (GPS coordinates, device model/make, recording UUIDs) through **even on a full transcode** to an unrelated codec/container, unless explicitly told not to. Confirmed on:
- An iPhone-shot `.MOV` carrying `com.apple.quicktime.location.ISO6709` (precise GPS) — survived a full mp4→webm-equivalent transcode unchanged.
- An iPhone Voice Memo `.m4a` carrying a `voice-memo-uuid` tag — survived an m4a→flac conversion unchanged.

Default behavior: `-map_metadata -1` is applied to all video/audio conversions, stripping this data, unless the user explicitly opts to preserve it via the "Preserve original metadata" toggle (FR-15 in PRD). Rotation metadata (`Display Matrix` / `rotate` tags) is handled separately from this stripping and is always preserved/correctly applied (FR-16) — confirmed surviving a remux operation on the same iPhone test file.

## 5. Cross-Platform Dependency Detection

```python
def detect_package_manager() -> str | None:
    system = platform.system()  # "Linux" | "Darwin" | "Windows"
    candidates = {
        "Linux":   ["pacman", "apt", "dnf", "zypper"],
        "Darwin":  ["brew"],
        "Windows": ["winget", "choco"],
    }
    for mgr in candidates.get(system, []):
        if shutil.which(mgr):
            return mgr
    return None
```

Install command is looked up per manager and **only ever printed**, never executed:

| Manager | Command shown to user |
|---|---|
| pacman | `sudo pacman -S pandoc ffmpeg libreoffice-fresh` |
| apt | `sudo apt install pandoc ffmpeg libreoffice` |
| dnf | `sudo dnf install pandoc ffmpeg libreoffice` |
| brew | `brew install pandoc ffmpeg libreoffice` |
| winget | `winget install --id JohnMacFarlane.Pandoc -e` (and equivalent for ffmpeg/LibreOffice — exact IDs verified at implementation time, winget catalog naming has shifted historically) |
| choco | `choco install pandoc ffmpeg libreoffice -y` |
| none detected | Direct download links to pandoc.org, ffmpeg.org, libreoffice.org |

No elevation (sudo/UAC) is ever triggered programmatically by ConBot. See Security & Access Document §2 for rationale.

## 6. Process Lifecycle & Interruption Handling

- All external engine calls (pandoc, ffmpeg, soffice) run via `subprocess.run()` or `subprocess.Popen()`, never `os.system()` or shell=True with unsanitized input.
- A `SIGINT` (Ctrl+C) handler is registered during active conversions. On trigger, the user is presented the Stop/Background/Cancel choice (PRD §7.5).
- "Background" detachment: `Popen(..., start_new_session=True)` on POSIX, `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` on Windows, so the child subprocess survives ConBot's own process exit.
- "Stop" sends `SIGTERM` (escalating to `SIGKILL` after a grace period if unresponsive) to the child process and deletes any partial output file in `conbot_output/` to avoid leaving corrupt files behind.

## 7. Testing Approach

Given the "production grade, not prototype" requirement, engine logic is validated against real sample files, not just synthetic/documentation examples, before being considered done:
- Android-shot H.264/AAC mp4 — verified remux and transcode paths, timing, codec compatibility error handling.
- iPhone-shot H.264/AAC `.MOV` with rotation metadata and GPS — verified rotation survival on remux, metadata leak on transcode, informing the default-strip decision.
- iPhone Voice Memo `.m4a` — verified mono/sample-rate preservation, VBR quality flag behavior, metadata leak on lossless conversion.

Document/Spreadsheet/Image engine choices were verified against current (2026) documentation, changelogs, and real-world reported issues (e.g. pandoc docx→epub style-flattening, LibreOffice vs pandoc fidelity tradeoffs) rather than against live test files at the architecture stage; real-file testing for these categories should occur during their respective implementation milestones (PRD §10).

## 8. Known Constraints / Future Considerations

- LibreOffice headless adds significant install footprint (multi-GB) compared to pandoc/ffmpeg. Acceptable for v1 given the fidelity requirement; worth revisiting if install size becomes a real adoption blocker.
- `soffice` headless mode has known real-world flakiness (stale lock files after crashes). A lock-file cleanup/retry step should be added to the LibreOffice wrapper during implementation, not deferred.
- Windows elevation (winget/choco install of dependencies) cannot be inline-streamed into ConBot's own terminal output — this is an accepted, intentional platform asymmetry, not a bug (see conversation history / PRD constraints).