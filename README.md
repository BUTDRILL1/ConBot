# ConBot 🤖

**Convert anything to anything, fast. Fully offline, privacy-first, menu-driven.**

ConBot is a CLI-first, interactive file conversion tool. It runs as a globally installed command (`conbot`) that scans your current working directory, lets you navigate via arrow-key menus to select a source file and target format, and produces a converted file in a local `./conbot_output/` folder.

It supports Documents, Images, Videos, Audio, and Spreadsheets, automatically orchestrating best-in-class conversion engines (`pandoc`, `ffmpeg`, `LibreOffice`, `Pillow`, `pandas`) behind a simple, unified interface.

> **Status:** Early development, built incrementally and pushed in stages. Not yet published to PyPI — see Installation below for installing from source.

## ✨ Features

- **Zero Command Memorization:** Interactive TUI (Terminal User Interface). No need to memorize `ffmpeg` flags or `pandoc` syntax.
- **Production-Grade Quality:** Uses the correct engine for each format pair (e.g., LibreOffice for strict `.docx` layout fidelity, ffmpeg for rapid video remuxing).
- **100% Offline & Private:** No cloud uploads, no ads, no telemetry.
- **Privacy-First Defaults:** Automatically strips identifying metadata (GPS coordinates, device models) from video and audio conversions by default.
- **Smart Engine Routing:** Automatically detects if a video just needs a rapid container change (remux) vs a full re-encode (transcode).

## 🚀 Installation

ConBot isn't published on PyPI yet, so `pipx install conbot` won't work yet. For now, install from source:

```bash
# Clone the repo
git clone https://github.com/BUTDRILL1/conbot.git
cd conbot

# Install globally via pipx, from the local source folder
pipx install .
```

Once published to PyPI, installation will simply be:

```bash
pipx install conbot
```

### System Dependencies

ConBot orchestrates system-level tools to perform high-quality conversions. On your first run, ConBot will detect which engines you have installed and tell you exactly how to install any missing ones for your OS (e.g., via `apt`, `brew`, `pacman`, or `winget`).

ConBot never runs these install commands for you automatically — it only ever prints the correct command for your system, so you stay in control of what gets installed at the system level.

| Category | Required engine |
|---|---|
| Documents / Spreadsheets | `pandoc` & `libreoffice` (headless) |
| Video / Audio | `ffmpeg` |
| Images | Handled natively via Python dependencies (Pillow + pillow-heif) — no extra install needed |

## 💻 Usage

Simply open your terminal in the directory containing the files you want to convert and type:

```bash
conbot
```

1. Navigate categories with `↑` / `↓` and press `Enter` to select.
2. Choose your source file.
3. Choose your target format.
4. Your converted file will appear in `./conbot_output/`!

Press `Esc` at any time to go back, or `Ctrl+C` to quit.

## 🔒 Privacy & Security

- ConBot makes no network calls at runtime — all conversion happens locally.
- ConBot never executes privileged (`sudo`/admin) commands on your behalf, on any OS.
- Video/audio metadata that can identify you or your device (GPS location, device model, recording IDs) is stripped by default; you can opt to preserve it per conversion if you want it kept.

Full details in the project's Security & Access documentation.

## 🗺️ Roadmap

Built and released in stages:

- [ ] Document + Image conversion
- [ ] Spreadsheet conversion
- [ ] Video conversion
- [ ] Audio conversion
- [ ] Cross-platform polish (Windows/macOS dependency messaging, error handling)

## 🤝 Contributing

ConBot was built primarily for personal use — fast, private, offline file conversion without ads or uploads. It's shared here in case it's useful to others. Issues and PRs are welcome, but please expect modest response times since this is a side project, not a maintained product.

## 📄 License

MIT License — see [LICENSE](./LICENSE) for full text. Free to use, modify, and distribute, including commercially, as long as the original copyright notice is retained.