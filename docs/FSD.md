# ConBot — Frontend Specification Document (TUI)

**Version:** 1.0
**Status:** Approved for development
**Last updated:** 2026-06-17

---

## 1. Scope

ConBot's "frontend" is its terminal UI (TUI) — there is no GUI or web interface. This document specifies every screen, interaction pattern, and visual state the CLI presents, built on `questionary` (menu navigation) and `rich` (banners, progress bars, formatted text).

## 2. Global Interaction Rules

| Key | Action |
|---|---|
| ↑ / ↓ | Move selection within current menu |
| Enter | Confirm selection, proceed to next screen |
| Esc | Go back one screen (not literal Ctrl+Z — see Technical Architecture rationale: Ctrl+Z is intercepted by the shell as SIGTSTP and cannot be reliably captured as a TUI keypress) |
| Ctrl+C | Quit immediately from any non-converting screen; during an active conversion, triggers the interrupt-handling prompt (§6) |

Esc at the root category menu (no previous screen to return to) is a no-op — it does not exit the app or throw an error.

## 3. Screen-by-Screen Specification

### 3.1 Launch banner (every launch)
```
╔════════════════════════════════════════╗
║              ConBot v1.0                ║
║   Convert anything to anything, fast    ║
╚════════════════════════════════════════╝

ConBot converts files in your CURRENT directory only.
Navigate with ↑↓, select with Enter, go back with Esc, quit with Ctrl+C.
```
Displayed on every launch, not just first run. Static text, no dependency check performed here (that's cached separately, §3.2).

### 3.2 Dependency check (first launch only, or after `conbot --recheck`)
Triggered before the banner. Three possible outcomes:

**All present:**
```
✓ pandoc found
✓ ffmpeg found
✓ libreoffice found
```
Brief, then proceeds straight to banner + root menu.

**Some missing, known package manager detected:**
```
✗ pandoc not found
✗ ffmpeg not found

ConBot needs these for Document, Video, and Audio conversions.
(Image and Spreadsheet conversions work without them.)

Run this yourself, then restart ConBot:
  sudo pacman -S pandoc ffmpeg

> OK, got it
```
Single acknowledgment button. ConBot never executes this command (see Security & Access Document §2). Affected categories are marked unavailable in the menu, not removed.

**Some missing, no known package manager detected:**
```
✗ pandoc not found
✗ ffmpeg not found

Couldn't detect a known package manager on this system.

Install manually from:
  pandoc:  https://pandoc.org/installing.html
  ffmpeg:  https://ffmpeg.org/download.html

> OK, continue with limited features
```

### 3.3 Root category menu ("A")
```
Convert `A` to `B`

A:
> Document
  Image
  Video
  Audio
  Spreadsheet
```
If a category's required engine is missing (per §3.2), it renders visually distinct and non-selectable, e.g.:
```
  Document (unavailable — pandoc not installed)
```

### 3.4 Extension picker (within selected category)
```
Convert `A` to `B`

A → Document:
> .md
  .docx
  .pdf
  .html
```
Only extensions with at least one matching file physically present in the current working directory are listed. If none exist for the selected category:
```
A → Image:
  (no image files found in this directory)

Esc → go back
```

### 3.5 File picker (within selected extension)
```
Convert `A` to `B`

A → Document → .md:
> FileA.md
  README.md
  notes.md
```
Filenames are displayed exactly as they appear on disk (original casing preserved), even though matching against the extension is case-insensitive internally.

### 3.6 Target category menu ("B") — filtered by source
```
Convert `FileA.md` to `B`

B:
> Document
  Image
```
Only categories the engine can realistically produce from the selected source file are shown (per the Conversion Engine Matrix in the Technical Architecture Document). A markdown source never shows Video/Audio as viable targets.

### 3.7 Target extension menu
```
Convert `FileA.md` to `B`

B → Document:
> .pdf
  .docx
  .html
  .epub
```
If the highlighted/selected pair is a known degraded-quality conversion (e.g. `.docx` → `.epub`), a warning line appears before the confirmation step (§3.8), not silently after.

### 3.8 Degraded-quality warning (conditional)
```
⚠ Converting .docx to .epub may not preserve custom paragraph
  styles or heading structure correctly.

> Continue anyway
  Go back
```

### 3.9 Metadata preservation prompt (video/audio only)
```
This file contains identifying metadata (location/device info).
ConBot will remove this by default for privacy.

> Strip metadata (recommended)
  Preserve original metadata
```
Shown once per conversion for video/audio sources, not repeated needlessly within the same session unless the source file changes.

### 3.10 Output collision prompt (conditional)
```
⚠ ./conbot_output/FileA.pdf already exists.

> Overwrite
  Save as FileA(1).pdf
  Cancel
```

### 3.11 Active conversion — remux (fast path)
```
Converting `FileA.mov` → `FileA.mkv`
Remuxing (fast, no quality loss)...  ⠋
```

### 3.12 Active conversion — transcode (slow path)
```
Converting `FileA.mov` → `FileA.webm`
This format requires re-encoding and may take a while.
Transcoding...  ⠋  00:00:14 elapsed
```
Elapsed time shown for transcodes specifically, since duration is unpredictable and the user should not assume something has frozen.

### 3.13 Ctrl+C during active conversion
```
^C
Conversion in progress: FileA.mp4 → FileA.webm

> Stop conversion (kills process, deletes partial output)
  Let it finish in background, exit ConBot now
  Cancel, keep waiting
```
Selecting "background" shows a one-time clarifying note:
```
ConBot will exit now. The conversion will continue running,
but you won't see its progress or be notified when it finishes.
Check ./conbot_output/ later for the result.
```

### 3.14 Success
```
✓ Done! Saved to ./conbot_output/FileA.pdf

Esc → convert another file
Ctrl+C → quit
```

### 3.15 Failure
```
✗ Conversion failed: pandoc couldn't parse FileA.md
  (error: unexpected token at line 42)

Esc → go back and try again
```
Raw underlying tool error is shown, not a generic message (PRD FR-17).

## 4. Visual/Styling Conventions

| Element | Convention |
|---|---|
| Success | `✓` prefix, green (via `rich`) |
| Failure/error | `✗` prefix, red |
| Warning | `⚠` prefix, yellow |
| Current menu selection | `>` prefix (questionary default arrow-style cursor) |
| Disabled/unavailable item | Dimmed/grey text + reason in parentheses |
| Spinners | `rich` spinner during indeterminate waits (dependency check, remux) |
| Progress with elapsed time | Shown specifically for transcodes, where duration is unpredictable |

## 5. Responsiveness / Performance Requirements

- Every launch after the first must reach the root category menu near-instantly (no dependency re-check, no venv creation — pipx already isolated the environment at install time).
- Menu navigation (arrow keys, selection) must have no perceptible lag — this is in-process Python, not a subprocess call, so this should be trivially satisfied by `questionary`.
- Conversion progress indicators must update during long-running operations (transcodes) so the terminal never appears frozen.

## 6. Accessibility / Terminal Compatibility Notes

- All interactive elements must degrade gracefully on terminals without full color/unicode support — `rich` and `questionary` both handle this automatically, but should not be overridden with hardcoded ANSI codes that bypass this fallback behavior.
- Esc-to-go-back was chosen specifically because it is the standard convention across other terminal UIs (fzf, lazygit, etc.), making ConBot's interaction model immediately familiar rather than requiring the user to learn a bespoke scheme.