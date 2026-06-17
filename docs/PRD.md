# ConBot — Product Requirements Document

**Version:** 1.0
**Status:** Approved for development
**Owner:** Amil
**Last updated:** 2026-06-17

---

## 1. Summary

ConBot is a CLI-first, interactive file conversion tool. It runs as a globally installed command (`conbot`) that scans the current working directory, lets the user navigate via arrow-key menus to select a source file and target format, and produces a converted file in `./conbot_output/`. It supports Documents, Images, Videos, Audio, and Spreadsheets, using best-in-class conversion engines per format pair rather than a single generic converter.

## 2. Problem Statement

Free web-based file converters are ad-saturated, require uploading files to third-party servers (privacy concern), and are inconsistent in quality. Existing CLI tools (pandoc, ffmpeg) are powerful but require memorizing flags and commands per format pair — there is no unified, interactive, beginner-friendly CLI wrapper that picks the *correct* engine and flags automatically.

## 3. Goals

- Single command (`conbot`) to convert any supported file type to any sane target type, fully offline (no upload to any server).
- Menu-driven, no command memorization required.
- Production-grade output quality — correct engine chosen per format pair, not just "whatever's easiest to wire up."
- Privacy-respecting by default (strips identifying metadata like GPS/device IDs unless user opts in to keep them).
- Cross-platform: Linux (Arch primary), macOS, Windows.

## 4. Non-Goals (v1)

- No GUI.
- No batch/multi-file conversion (single file at a time only, by design).
- No cloud upload or server-side processing of any kind.
- No video/audio editing (trimming, filters, effects) — conversion only.
- No OCR.

## 5. Target User

Primary: the developer themself, for daily personal use (markdown notes to PDF, phone videos to web formats, voice memos to mp3, spreadsheets to PDF for sharing).
Secondary (post-v1, if open-sourced): developers and technical users comfortable with a terminal who want a fast, ad-free, offline converter.

## 6. Supported Conversions (v1 scope)

| Category | Formats in scope |
|---|---|
| Document | `.md`, `.html`, `.docx`, `.doc`, `.odt`, `.rtf`, `.pdf`, `.epub` |
| Image | All Pillow-supported formats + HEIC/HEIF via pillow-heif |
| Spreadsheet | `.xlsx`, `.xls`, `.csv`, `.ods` |
| Video | Common containers/codecs supported by the installed ffmpeg build |
| Audio | Common containers/codecs supported by the installed ffmpeg build |

Exact source→target pairs and which engine handles each are defined in the Technical Architecture Document (§4, Conversion Engine Matrix).

## 7. Functional Requirements

### 7.1 Installation
- FR-1: User installs via `pipx install conbot`. No manual venv steps required from the user.
- FR-2: `conbot` becomes a globally typeable command immediately after install, on Linux/macOS/Windows.

### 7.2 Dependency detection
- FR-3: On first launch, ConBot detects presence of `pandoc`, `ffmpeg`, and `libreoffice`/`soffice` via `shutil.which()`.
- FR-4: ConBot detects the system's package manager (pacman/apt/dnf/brew/winget/choco) and prints — but never executes — the correct install command for any missing dependency.
- FR-5: Result of the dependency check is cached after first run; not re-checked on every launch unless the user runs `conbot --recheck`.
- FR-6: Categories whose required engine is missing are shown in the menu but visually marked unavailable, with the reason stated.

### 7.3 Navigation
- FR-7: Every launch shows the ConBot banner, a one-line usage hint, and the root category menu (Document / Image / Video / Audio / Spreadsheet).
- FR-8: Navigation uses ↑/↓ to move, Enter to select, Esc to go back one level, Ctrl+C to quit at any time.
- FR-9: File lists are filtered to extensions that actually exist as files in the current working directory. Empty categories show "no files found" rather than an empty list.
- FR-10: After selecting a source file, the target-format menu (`B`) is filtered to only formats that are realistically convertible from the selected source — no nonsensical pairs offered (e.g. `.md` → `.mp4`).
- FR-11: Conversion pairs known to produce degraded output (e.g. `.docx` → `.epub` losing custom styles) display a warning before the user confirms, but are not blocked.

### 7.4 Conversion execution
- FR-12: Output is always written to `./conbot_output/` relative to the directory ConBot was launched from.
- FR-13: If the output filename already exists, the user is prompted: Overwrite / Save as new name / Cancel.
- FR-14: Video conversions automatically attempt remux (stream copy) before falling back to transcode (re-encode), and inform the user which path was taken plus an approximate time expectation if transcoding.
- FR-15: All conversions strip identifying metadata (GPS coordinates, device model, recording UUIDs) by default. A "Preserve original metadata" toggle is available per conversion.
- FR-16: Rotation metadata on video is always preserved/correctly applied regardless of the metadata-stripping setting above — rotation is a display-correctness concern, not a privacy concern.
- FR-17: On conversion failure, ConBot shows the real underlying tool error (pandoc/ffmpeg/LibreOffice stderr), not a generic "something went wrong" message.

### 7.5 Interruption handling
- FR-18: Ctrl+C during an active conversion presents: Stop (kill process, delete partial output) / Let it finish in background / Cancel (resume waiting).
- FR-19: "Let it finish in background" detaches the subprocess so it survives ConBot's own exit; this is documented to the user as having no further progress visibility once detached.

## 8. Success Metrics (informal, personal-use tool)

- Can convert a real phone-shot video (Android H.264 or iPhone H.264/HEVC) without manual flag-fiddling.
- Can convert a real voice memo (iPhone .m4a) to mp3 at transparent quality without manual flag-fiddling.
- Can convert a real Word doc with formatting to PDF with layout fidelity preserved.
- Zero crashes on missing dependencies — always degrades gracefully with a clear message.
- Zero silent data loss (metadata leaks, dropped audio channels, wrong sample rates) — verified against real sample files during development, not just documentation.

## 9. Constraints

- No sudo/elevated execution performed by ConBot itself, on any OS — install commands are always printed for manual execution, never auto-run.
- Single file conversion only, no batch processing, by explicit design decision.
- No network calls of any kind during conversion (fully offline operation).

## 10. Release Plan

Incremental, pushed to GitHub in stages:
1. Document + Image (lowest risk, highest immediate personal utility)
2. Spreadsheet
3. Video
4. Audio
5. Polish pass: error message taxonomy, cross-platform dependency installer messaging, README

## 11. Open Questions Carried Into Development

None outstanding as of this version — all engine choices and known degraded-quality pairs were verified against documentation and real sample files prior to this PRD being finalized. Any new pairs discovered during implementation that weren't covered in research should be tested against real files before being added to the conversion matrix.