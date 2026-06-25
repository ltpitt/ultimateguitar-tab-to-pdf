# ugpdf

Download Ultimate Guitar tabs as clean, print-ready PDFs from the command line.

```
$ ugpdf teen spirit nirvana

🔍 Searching: teen spirit nirvana
✓ Selected: Nirvana – Smells Like Teen Spirit
  Type: Chords  Rating: ★4.0  Votes: 4.2K
  URL: https://tabs.ultimate-guitar.com/tab/nirvana/smells-like-teen-spirit-chords-807883

🖨️  Generating PDF...
✅ Saved: nirvana-smells-like-teen-spirit.pdf
```

## Features

- **Smart selection** — Automatically picks the highest-voted community version (skips pay-to-view official tabs)
- **Clean output** — Generates print-formatted PDFs with chord diagrams, strumming patterns, and lyrics
- **Simple UX** — One command, no accounts, no fuss
- **Browse mode** — Use `--list` to see all available versions and `--pick` to choose

## Install

```bash
# Clone and install
git clone https://github.com/yourusername/ugpdf.git
cd ugpdf
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Install browser (first time only)
playwright install chromium
```

> **Requires:** Python 3.10+ and Google Chrome installed on your system.

## Usage

```bash
# Basic — searches and auto-selects best version
ugpdf teen spirit nirvana

# Specify output path
ugpdf "hotel california" -o hotel.pdf

# Filter by type (Chords, Tab, Guitar Pro, Bass)
ugpdf wonderwall oasis --type Chords

# Browse all available versions
ugpdf "stairway to heaven" --list

# Pick a specific version from the list
ugpdf "stairway to heaven" --list --pick 2
```

## Options

| Flag | Description |
|------|-------------|
| `-o`, `--output PATH` | Output PDF file path (auto-generated if omitted) |
| `-t`, `--type TYPE` | Filter by tab type: Chords, Tab, Guitar Pro, Bass |
| `--list` | Show all available versions in a table |
| `--pick N` | Select version N from the list |
| `-h`, `--help` | Show help |
| `--version` | Show version |

## How it works

1. Searches Ultimate Guitar for your query
2. Picks the best community version (most votes, highest rating, non-official)
3. Opens the tab page in a headless browser
4. Clicks "Download PDF" to trigger the print-formatted view
5. Saves the result as a clean A4 PDF

## License

MIT
