# scripts/

Utility scripts for automating interactions with mage.space.

## Prerequisites

```bash
pip install playwright
playwright install webkit
```

Scripts use a persistent WebKit browser profile (`~/.mage-playwright-profile`) so your mage.space login is preserved across runs.

## Scripts

| Script | Description |
|--------|-------------|
| `mage_generate.py` | Automate image generation on mage.space/advanced — supports single prompts and batch mode from a markdown file, with configurable model, aspect ratio, and output directory. |
| `mage_download.py` | Download all saved creations from mage.space/creations with JSON sidecar metadata, organized into a `YYYY/MM - Month/DD/` directory structure with resume support via a manifest file. |
