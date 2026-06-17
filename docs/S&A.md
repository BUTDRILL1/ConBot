# ConBot — Security & Access Document

**Version:** 1.0
**Status:** Approved for development
**Last updated:** 2026-06-17

---

## 1. Threat Model Summary

ConBot is a local, offline CLI tool with no network calls, no server component, and no remote data transmission. The primary security considerations are therefore not "attacker on the network" but: (a) privilege escalation surface, (b) unintended data leakage via file metadata, (c) safe subprocess execution, (d) safe handling of files outside ConBot's intended scope.

## 2. Privilege Escalation — Explicit Non-Goal

**Decision: ConBot never executes `sudo`, `runas`, or any other privilege-elevation mechanism programmatically, on any operating system, under any circumstance.**

### 2.1 Rationale
An earlier design draft considered having ConBot run `sudo pacman -S pandoc ffmpeg` directly on the user's behalf after a single confirmation prompt. This was deliberately rejected. Reasoning:
- A file conversion tool has no legitimate ongoing need for root-level execution capability. Granting it anyway means a bug, a tampered package, or a future careless code change could escalate to root-level system modification — a disproportionate risk for the convenience gained (saving the user a copy-paste).
- The time saved by auto-running the install command (~10 seconds) does not justify permanently carrying "this tool can execute root commands" as an attribute of the codebase.
- This also eliminates the Windows UAC-elevation code path entirely, since there is nothing for ConBot to elevate.

### 2.2 Implementation requirement
- `bootstrap.py` may **detect** the OS and package manager and **construct** the correct install command string.
- `bootstrap.py` must **never** pass that string to `subprocess.run()`, `os.system()`, or any execution function. It is for display only.
- Any future contributor proposing to add auto-execution of install commands must treat this as a breaking change to the security model requiring explicit re-review, not a routine feature addition.

## 3. Subprocess Execution Safety

- All calls to pandoc, ffmpeg, and soffice use `subprocess.run()`/`Popen()` with an argument **list**, never a shell string, and never `shell=True`. This avoids shell injection regardless of characters present in filenames.
- Filenames are passed as `Path` objects / list arguments, not interpolated into a shell command string.
- ConBot does not construct conversion commands from any user-supplied free-text input beyond filename/format selection from a pre-enumerated menu — there is no open text field that flows into a subprocess argument unsanitized.

## 4. Metadata & Privacy

### 4.1 Verified leakage risk
Direct testing (see Technical Architecture Document §4.2) confirmed that ffmpeg, by default, propagates container-level metadata through conversions — including:
- Precise GPS coordinates (`com.apple.quicktime.location.ISO6709`)
- Device make/model (`com.apple.quicktime.make`, `.model`)
- Unique recording identifiers (`voice-memo-uuid`)

This metadata survives **even a full re-encode to an unrelated codec/container**, not just simple remuxing — confirmed on both a video and an audio test file.

### 4.2 Default behavior
- ConBot applies `-map_metadata -1` (strip all container/format metadata) to every video and audio conversion **by default**.
- An explicit, opt-in "Preserve original metadata" toggle is available per conversion for cases where the user deliberately wants it retained (e.g. personal archival with timestamp/location intentionally kept).
- Rotation/orientation metadata is treated separately from this privacy-stripping logic and is always correctly preserved regardless of the toggle state — it is a display-correctness concern (incorrect playback orientation), not a privacy concern, and stripping it would degrade output quality for no privacy benefit.
- This default-strip behavior is documented to the user the first time a video/audio conversion runs, so it is not a silent, undiscoverable change in file properties.

### 4.3 Document/Spreadsheet metadata (not yet independently verified)
Word/Excel/PDF files can also carry author names, organization metadata, and revision history. This was not directly tested during the research phase (research focused on Video/Audio per available sample files) and should be verified during the Document/Spreadsheet implementation milestone before the same default-strip behavior is assumed to be correctly implemented for those engines (pandoc/LibreOffice may handle metadata propagation differently than ffmpeg).

## 5. File System Access Scope

- ConBot only reads files within the directory it is launched from (current working directory). It does not recursively scan subdirectories or access files outside cwd as part of normal menu navigation.
- Output is always written to a single, predictable location: `./conbot_output/` relative to the launch directory. ConBot does not write files anywhere else on the filesystem during normal operation.
- ConBot's own installation/config data (dependency-check cache) is stored under the user's standard config/cache directory (e.g. `~/.conbot/` on Linux/macOS, `%APPDATA%\conbot\` on Windows) — not inside the user's working directories, to avoid cluttering or accidentally being picked up by the file-scanning logic.

## 6. Output Collision Handling

- Before overwriting any existing file in `conbot_output/`, ConBot explicitly prompts: Overwrite / Save as new name / Cancel (PRD FR-13). ConBot never silently overwrites a user's existing file.

## 7. Failure & Partial-Output Handling

- On Ctrl+C during an active conversion, if the user selects "Stop," ConBot deletes the partial output file before exiting, to avoid leaving a corrupted, truncated file that could be mistaken for a complete conversion (Technical Architecture Document §6).
- On any conversion failure (non-zero exit from the underlying engine), ConBot does not leave a zero-byte or partially-written file silently sitting in `conbot_output/` without clearly surfacing the failure to the user.

## 8. Supply Chain / Dependency Hygiene

- Python dependencies (questionary, rich, Pillow, pillow-heif, pandas, openpyxl) are installed via pipx from PyPI — standard trust model, no private/unverified package sources.
- System binaries (pandoc, ffmpeg, LibreOffice) are installed by the user via their own OS package manager or official installer, not bundled or fetched by ConBot from any third-party mirror. ConBot does not download executable binaries from the internet at any point.
- No telemetry, analytics, or any form of network call exists in ConBot. This should remain true for all future versions unless explicitly revisited as a deliberate, disclosed product decision.

## 9. Out of Scope for v1

- Sandboxing of the conversion engines themselves (pandoc/ffmpeg/LibreOffice) beyond what the OS provides natively — ConBot trusts these are legitimate, unmodified installations from the user's own package manager.
- Protection against a maliciously crafted input file designed to exploit a vulnerability in pandoc/ffmpeg/LibreOffice itself — this is the responsibility of those projects' own security processes, not ConBot's.
- Multi-user permission models — ConBot is a single-user local tool.