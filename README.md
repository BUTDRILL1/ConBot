# ConBot 🤖

**The Universal, Privacy-First Offline File Converter.**

ConBot is a globally installed, Python-based CLI tool that lets you seamlessly convert documents, spreadsheets, images, and media files without memorizing complex command-line flags. Driven by an interactive Terminal User Interface (TUI), ConBot smartly orchestrates system-level engines (`ffmpeg`, `pandoc`, `LibreOffice`, `pandas`) to deliver production-grade conversions straight to a local output folder.

> **Status:** MVP Complete & Published! Available globally on PyPI. Fully tested on Windows, natively compatible with Linux/macOS.

---

## ✨ Why ConBot?

- **Zero Command Memorization:** Built with `questionary`, ConBot uses a stack-based state machine to provide an intuitive, continuous arrow-key menu. You are never kicked out after a successful conversion.
- **Smart Engine Routing:** ConBot isn't just a wrapper; it's smart. 
  - *Multi-sheet Excel files* automatically fan out into separate CSVs.
  - *Markdown to PDF* invisibly chains through `pandoc` into `LibreOffice` for flawless layout rendering.
  - *Video conversions* automatically attempt a rapid container remux (`-c copy`) before falling back to a full re-encode, saving immense time and quality.
- **Privacy-First Defaults:** Video and audio conversions automatically strip identifying metadata (GPS coordinates, device models) via `-map_metadata -1`.
- **Almost 100% Offline:** All conversions happen entirely locally on your machine.
  - *Exception:* If you convert a Markdown (`.md`) file containing a Mermaid flowchart (````mermaid`), ConBot briefly pings the free `kroki.io` API to magically render the diagram as an image in your final document.

---

## 🚀 Installation

### Install Globally from pipx

ConBot is published on PyPI and designed to be installed globally via `pipx`.

```bash
pipx install conbot
```

*(Note: If you don't have `pipx` installed, you can get it via `pip install pipx` or your system package manager).*

### Install from Source

If you prefer to install directly from the latest source code:

```bash
# 1. Clone the repo
git clone https://github.com/BUTDRILL1/conbot.git
cd conbot
```

### System Dependencies

ConBot acts as a conductor for powerful system-level tools. On your first run, ConBot will intelligently scan your system path (including Windows `WinGet` and `Program Files` defaults) and tell you exactly how to install any missing engines. 

| Category | Required Engine |
|---|---|
| **Documents** | `pandoc` & `libreoffice` (headless) |
| **Spreadsheets** | Native Python (`pandas`, `openpyxl`) + `libreoffice` (for PDFs) |
| **Video & Audio** | `ffmpeg` |
| **Images** | Native Python (`Pillow`, `pillow-heif`) — *no extra install needed* |

---

## 💻 Usage

Simply open your terminal in the directory containing the files you want to convert and type:

```bash
conbot
```

1. **Select Category:** Navigate with `↑` / `↓` and press `Enter`.
2. **Select File:** Choose your source file from the auto-scanned list.
3. **Select Format:** Pick your target format.
4. **Done:** Your converted file instantly appears in `./conbot_output/`.
5. **Continuous Loop:** You'll be prompted to generate a different format, start over with a new file, or exit cleanly.

*Press `Esc` at any time to go back a step, or `Ctrl+C` to quit.*

---

## 🔒 Security & Access

- ConBot never executes privileged (`sudo`/admin) commands on your behalf.
- If dependencies are missing, ConBot merely *suggests* the installation command; it never runs arbitrary package managers on your machine.
- All file I/O is restricted to your current working directory (specifically saving to `./conbot_output/` with robust collision handling).

---

## 📄 License

MIT License — see [LICENSE](./LICENSE) for full text. Free to use, modify, and distribute, including commercially, as long as the original copyright notice is retained.