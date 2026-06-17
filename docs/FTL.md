# ConBot — Feature Ticket List

**Version:** 1.0
**Last updated:** 2026-06-17

Tickets are grouped by milestone, matching the incremental GitHub release plan (PRD §10). Each ticket has an ID, description, acceptance criteria, and references to the relevant spec section. Priority: P0 = blocks milestone release, P1 = should have, P2 = nice to have / can slip to a later milestone.

---

## Milestone 0 — Foundation (blocks all other milestones)

**CONBOT-1** [P0] Project scaffolding
- Set up `pyproject.toml` with `[project.scripts] conbot = "conbot.__main__:main"`, no `setup.py`.
- Module structure per Technical Architecture §3.
- AC: `pipx install .` from local source produces a working global `conbot` command that prints the banner and exits.

**CONBOT-2** [P0] Dependency detection (`bootstrap.py`)
- Implement `shutil.which()` checks for pandoc, ffmpeg, soffice/libreoffice.
- Implement OS + package manager detection (pacman/apt/dnf/zypper/brew/winget/choco).
- Cache result to `~/.conbot/deps_cache.json` (or platform-appropriate config dir).
- AC: Running on a machine missing ffmpeg shows the correct install command for the detected package manager, never executes it. Running `conbot --recheck` forces a fresh check. Ref: Tech Arch §5, Security §2.

**CONBOT-3** [P0] Navigation engine (`menu.py`)
- Stack-based screen navigation using `questionary.select`.
- Esc = pop stack / go back. Ctrl+C = quit (except during active conversion, see CONBOT-13).
- AC: Matches every screen transition in Frontend Spec §3.1–3.7 exactly, including the root-Esc no-op behavior.

**CONBOT-4** [P0] `format_graph.py` — extension/category map + CONVERSION_RULES
- Implement the full matrix from Technical Architecture §4 as a queryable data structure.
- Include per-pair engine assignment and warning flags (e.g. docx→epub).
- AC: Given a source extension, returns only the categories/extensions that are valid targets per the matrix — no nonsensical pairs returned.

**CONBOT-5** [P1] Case-insensitive, compound-extension-aware file scanning
- Normalize extension matching to lowercase. Handle compound extensions (`.tar.gz`) as distinct from their final segment alone. Exclude dotfiles and extensionless files from all category listings.
- AC: A file named `FileA.MD` appears correctly under the `.md` category. A `.gitignore` file never appears in any category.

---

## Milestone 1 — Document + Image

**CONBOT-6** [P0] Document engine: pandoc wrapper
- Implements `.md`/`.html` ↔ `.docx`/`.pdf`/`.epub` pairs per the matrix.
- AC: Real `.md` file with embedded HTML converts to `.pdf` without manual flags.

**CONBOT-7** [P0] Document engine: LibreOffice headless wrapper
- Implements `.docx`/`.doc`/`.odt`/`.rtf` → `.pdf` pairs.
- Includes lock-file cleanup/retry logic for `soffice` headless flakiness (Tech Arch §8).
- AC: A real Word doc with tables/images/headers converts to PDF with layout preserved.

**CONBOT-8** [P0] Degraded-quality warning system
- Generic warning-prompt mechanism in the UI layer, driven by the `warning` field in `CONVERSION_RULES`.
- AC: Selecting `.docx` → `.epub` shows the exact warning text from Frontend Spec §3.8 before proceeding.

**CONBOT-9** [P0] Image engine: Pillow + pillow-heif wrapper
- Covers all Pillow-supported formats plus HEIC/HEIF.
- AC: A HEIC photo converts to `.jpg`/`.png` correctly.

**CONBOT-10** [P1] Output collision handling
- Implements Overwrite / Save as new name / Cancel flow (PRD FR-13, Frontend Spec §3.10).
- AC: Running the same conversion twice triggers the prompt on the second run; "Save as new name" produces `FileA(1).pdf` without touching the original.

**CONBOT-11** [P2] Document/Spreadsheet metadata audit
- Investigate whether pandoc/LibreOffice propagate author/org metadata the way ffmpeg does for video/audio (flagged as unverified in Security & Access §4.3).
- AC: A decision (strip by default / leave as-is, with rationale) is documented and implemented consistently with the video/audio precedent if applicable.

---

## Milestone 2 — Spreadsheet

**CONBOT-12** [P0] Spreadsheet engine: pandas wrapper (`.csv` ↔ `.xlsx`)
- AC: Round-trip csv→xlsx→csv preserves all values exactly.

**CONBOT-13** [P0] Spreadsheet engine: LibreOffice wrapper (`.xls`/`.ods` → any, any → `.pdf`)
- Reuses the LibreOffice wrapper built in CONBOT-7 rather than duplicating subprocess logic.
- AC: A legacy `.xls` file converts successfully (openpyxl alone cannot open this format, confirming the LibreOffice routing decision).

**CONBOT-14** [P0] xlsx→csv warning prompts
- Date-serialization warning and multi-sheet fan-out behavior (one CSV per sheet, named accordingly).
- AC: A multi-sheet workbook produces N separate CSV files in `conbot_output/`, each named after its source sheet. A date column does not silently become a meaningless integer without the user being warned first.

---

## Milestone 3 — Video

**CONBOT-15** [P0] Video engine: ffmpeg wrapper with remux-first logic
- Implements the decision flow from Technical Architecture §4.1: attempt `-c copy`, detect failure via stderr pattern matching, fall back to transcode.
- AC: Matches verified behavior from real test files — mp4→mkv same-codec remux completes near-instantly; mp4→webm correctly falls back to transcode and informs the user of the longer wait.

**CONBOT-16** [P0] HEVC output tagging
- Apply `-tag:v hvc1` whenever the output codec is HEVC.
- AC: An HEVC-encoded output file plays correctly in QuickTime/iOS (or is at minimum tagged correctly per the verified fix — direct device testing if available).

**CONBOT-17** [P0] Metadata stripping default + preserve toggle
- Apply `-map_metadata -1` by default on all video conversions; implement the opt-in preserve toggle (Frontend Spec §3.9).
- AC: Converting the test iPhone `.MOV` file with default settings produces an output with no GPS/device tags, confirmed via `ffprobe`. Selecting "preserve" retains them.

**CONBOT-18** [P0] Rotation metadata preservation, independent of stripping toggle
- AC: Rotation survives correctly regardless of the metadata-stripping setting — verified via `ffprobe` showing the correct `rotation` value on output even when other metadata is stripped.

**CONBOT-19** [P0] Ctrl+C interrupt handling during conversion
- Implements Stop / Background / Cancel per Technical Architecture §6 and Frontend Spec §3.13.
- AC: "Stop" leaves no partial file in `conbot_output/`. "Background" detaches the subprocess such that it continues after ConBot's process exits (verified via process inspection, not just assumed).

---

## Milestone 4 — Audio

**CONBOT-20** [P0] Audio engine: ffmpeg wrapper with verified quality defaults
- `-q:a 2` for mp3 (VBR, not maxed CBR), `-compression_level 5` for flac.
- AC: Matches verified output from real test file — mono/sample-rate preserved, no unwanted upmixing or resampling.

**CONBOT-21** [P0] Audio metadata stripping (shares logic with CONBOT-17)
- AC: Converting the test `.m4a` voice memo strips the `voice-memo-uuid` tag by default; preserve toggle retains it.

**CONBOT-22** [P1] Error message taxonomy
- Catalog common pandoc/ffmpeg/LibreOffice failure patterns (corrupt file, missing codec, permission denied, disk full) and decide which get a translated user-friendly prefix vs. raw passthrough (PRD FR-17 specifies raw passthrough as the baseline; this ticket evaluates whether any patterns deserve a friendlier wrapper without hiding the underlying detail).

---

## Milestone 5 — Polish & Release Readiness

**CONBOT-23** [P1] README + installation docs
- Cover `pipx install conbot`, dependency install per OS, basic usage walkthrough.

**CONBOT-24** [P1] Cross-platform smoke test
- Verify dependency detection and install-command messaging on at least one non-Arch Linux distro, macOS (if accessible), and Windows.
- AC: Each platform shows the correct package-manager-specific install command; no crashes on any of the three.

**CONBOT-25** [P2] `conbot --recheck` flag and any other CLI flags beyond the interactive default
- AC: Documented and working as specified in Frontend Spec §3.2.

**CONBOT-26** [P2] Packaging size/footprint review
- Revisit the LibreOffice multi-GB dependency concern flagged in Technical Architecture §8 — decide if this remains acceptable or needs a lighter-weight alternative path for users who only need Document/Image/basic Spreadsheet support.