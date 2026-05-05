#!/usr/bin/env python3
"""
Automate image generation on mage.space/advanced using Playwright.

Usage:
    # Single prompt
    python scripts/mage_generate.py "a cozy cabin in the mountains at sunset"

    # With options
    python scripts/mage_generate.py "a dragon flying over a castle" --model "Flux.2" --ratio "16:9"

    # Batch from markdown file (parses room-prompts.md format)
    python scripts/mage_generate.py --batch room-prompts.md

    # Save to specific directory
    python scripts/mage_generate.py "a sunset" --output ./my-images

Batch mode reads a markdown file with entries like:

    ### Room Name
    **Ratio:** 16:9

    > Prompt text here...

Each prompt is generated 3x with Flux.2 Dev, then 2x with Z-Image Turbo.

Prerequisites:
    pip install playwright
    playwright install webkit


The script uses your existing browser session (persistent context) so you
stay logged in to mage.space across runs.
"""

import argparse
import asyncio
import functools
import os
import re
import time
from pathlib import Path

# Force unbuffered output
print = functools.partial(print, flush=True)

from playwright.async_api import async_playwright


MAGE_URL = "https://www.mage.space/advanced"
USER_DATA_DIR = os.path.expanduser("~/.mage-playwright-profile")

# Maps user-facing model names to the architecture card name.
# Only the architecture is clicked — clicking the model triggers a preset.
MODEL_MAP = {
    "FLUX.2 Dev": "Flux.2",
    "Z-Image Turbo": "Z-Image",
    "Z-Image": "Z-Image",
    "Mango": "Mango",
    "SDXL": "SDXL",
    "Flux": "Flux",
    "Chroma": "Chroma",
    "HiDream": "HiDream",
    "Qwen": "Qwen",
    "Selfie": "Selfie",
}


def parse_batch_markdown(filepath: str) -> list[dict]:
    """Parse a markdown file with # Section, ### Name, **Ratio:** X:Y, and > prompt entries.

    Returns a list of dicts with keys: section, name, ratio, prompt.
    The section comes from the most recent ``# Heading`` (h1) above each card entry.
    If no ratio is specified per card, a default of ``2:3`` is used.
    """
    with open(filepath) as f:
        content = f.read()

    entries = []
    current_section = None

    # Process line-by-line to track h1 sections and h3 card entries
    # in document order, so each card gets the section that precedes it.
    lines = content.split("\n")
    i = 0
    section_prompt = []
    while i < len(lines):
        line = lines[i]

        # Track h1 section headers (e.g. "# Classic Deck")
        h1 = re.match(r"^#\s+(.+)", line)
        if h1:
            current_section = h1.group(1).strip()
            section_prompt = []
            i += 1
            while i < len(lines):
                sub = lines[i]
                if re.match(r"^#{1,3}\s+", sub):
                    break
                section_prompt.append(sub.strip())
                i += 1
            continue

        # Detect h3 card entry (e.g. "### Ace of Hearts")
        h3 = re.match(r"^###\s+(.+)", line)
        if h3:
            name = h3.group(1).strip()
            ratio = "2:3"
            prompt_lines = []

            # Scan forward for ratio and prompt blockquote
            i += 1
            while i < len(lines):
                sub = lines[i]
                # Stop at next heading
                if re.match(r"^#{1,3}\s+", sub):
                    break
                rm = re.match(r"\*\*Ratio:\*\*\s*(\S+)", sub)
                if rm:
                    ratio = rm.group(1)
                if sub.startswith(">"):
                    prompt_lines.append(sub.lstrip("> ").strip())
                i += 1

            if prompt_lines:
                prompt = " ".join(prompt_lines)
                entries.append(
                    {
                        "section": current_section,
                        "section_prompt": " ".join(section_prompt).strip(),
                        "name": name,
                        "ratio": ratio,
                        "prompt": prompt,
                    }
                )
            continue

        i += 1

    return entries


async def wait_for_page_ready(page, timeout=60000):
    """Wait for the mage.space advanced page to be fully loaded."""
    await page.wait_for_load_state("domcontentloaded", timeout=timeout)
    # Wait for the prompt Send button to appear
    await page.locator("img[alt='Send']").wait_for(state="visible", timeout=timeout)


async def select_model(page, model_name: str):
    """Select a model by clicking the architecture card.

    1. Type first 2 chars of the architecture name in the architecture Search box
    2. Click the architecture card (h5 heading)

    Only the architecture is clicked — clicking the model would trigger a preset.
    """
    arch_name = MODEL_MAP.get(model_name, model_name)

    # Step 1: Filter architectures by typing in the architecture search bar (top one)
    # The architecture search has placeholder "Search..." while the model search
    # has "Search models..." — use exact match to target the right one
    arch_search = page.get_by_placeholder("Search...", exact=True)
    try:
        await arch_search.click(timeout=5000)
        await arch_search.fill(arch_name[:2])
        await page.wait_for_timeout(500)
    except Exception as e:
        print(f"  Warning: Could not use architecture search: {e}")
        return

    # Step 2: Click the architecture card (h5 heading)
    arch_heading = page.get_by_role("heading", name=arch_name, level=5, exact=True)
    try:
        await arch_heading.click(timeout=5000)
        await page.wait_for_timeout(500)
        print(f"  Selected architecture: {arch_name}")
    except Exception:
        print(f"  Warning: Could not find architecture '{arch_name}'")
        await arch_search.fill("")
        return

    # Clear the architecture search
    await arch_search.fill("")
    await page.wait_for_timeout(200)


async def select_aspect_ratio(page, ratio: str):
    """Select an aspect ratio by clicking the named button on the advanced page.

    Buttons are labeled like "16:9 cinema", "1:1 square", "4:5 portrait", etc.
    """
    ratio_btn = page.get_by_role("button", name=re.compile(rf"^{re.escape(ratio)}\s"))
    try:
        await ratio_btn.click(timeout=5000)
        await page.wait_for_timeout(200)
        print(f"  Selected ratio: {ratio}")
    except Exception as e:
        print(f"  Warning: Could not select ratio '{ratio}': {e}")


async def generate_image(
    page,
    prompt: str,
    model: str = None,
    ratio: str = None,
    output_dir: Path = None,
    name: str = None,
):
    """Generate a single image from a prompt.

    Returns the path to the saved image, or None if saving was skipped.
    """
    print(f"\n--- Generating: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

    # Optionally change model
    if model:
        print(f"  Model: {model}")
        await select_model(page, model)

    # Optionally change aspect ratio
    if ratio:
        print(f"  Ratio: {ratio}")
        await select_aspect_ratio(page, ratio)

    # Clear and type the prompt — the input is a contenteditable paragraph
    prompt_el = None
    selectors = [
        "div[contenteditable='true']",
        "[contenteditable='true'] p",
        "p[data-placeholder]",
        "div[role='textbox']",
        "[placeholder*='Describe']",
    ]
    for sel in selectors:
        loc = page.locator(sel).first
        if await loc.count() > 0 and await loc.is_visible():
            prompt_el = loc
            break

    if not prompt_el:
        # Fallback: click just above the Send button
        print("  Using fallback: clicking near Send button")
        send_box = await page.locator("img[alt='Send']").bounding_box()
        if send_box:
            await page.mouse.click(send_box["x"] - 200, send_box["y"])
        else:
            raise RuntimeError("Cannot find prompt input or Send button")
    else:
        await prompt_el.click()
    await page.wait_for_timeout(200)

    # Select all and delete to clear any previous text
    await page.keyboard.press("Meta+a")
    await page.keyboard.press("Backspace")
    await page.wait_for_timeout(200)

    # Type the prompt character by character (contenteditable needs this)
    await page.keyboard.type(prompt, delay=10)
    await page.wait_for_timeout(len(prompt) * 10 + 500)

    # Click send
    send_btn = page.locator("img[alt='Send']")
    await send_btn.click()
    print("  Submitted, waiting for generation...")

    # Wait for generation to complete by watching the "Generating: X / 10" text
    generating_text = page.get_by_text("Generating:")
    try:
        await generating_text.first.wait_for(state="visible", timeout=15000)
        print("  Generation started...")
    except Exception:
        print("  Warning: Generation may not have started, checking sidebar...")

    # Wait for queue count to reach zero (e.g. "Generating: 0") — up to 5 minutes
    try:
        await page.wait_for_function(
            """
            () => {
              const el = Array.from(document.querySelectorAll('*')).find((n) =>
                n.textContent && /^Generating:\\s*\\d+/.test(n.textContent.trim())
              );
              if (!el || !el.textContent) return false;
              const m = el.textContent.trim().match(/^Generating:\\s*(\\d+)/);
              return !!m && Number(m[1]) === 0;
            }
            """,
            timeout=300000,
        )
    except Exception:
        print(
            "  Warning: Generation may have timed out before reaching 'Generating: 0'"
        )
        return None

    # Wait for the sidebar image to confirm
    sidebar_img = page.locator("img[alt='Mage media']")
    try:
        await sidebar_img.first.wait_for(state="visible", timeout=10000)
    except Exception:
        print("  Warning: Sidebar image not found, but generation text disappeared")

    print("  Generation complete!")
    await page.wait_for_timeout(500)

    # Click the generated image in the sidebar to open detail view
    filepath = None
    try:
        await sidebar_img.first.click(timeout=5000)
        await page.wait_for_timeout(1000)

        # Click "Save" to save it to your mage.space account
        save_btn = page.get_by_role("button", name="Save", exact=True)
        await save_btn.click(timeout=5000)
        await page.get_by_text("Success").first.wait_for(state="visible", timeout=10000)
        print("  Saved to mage.space account!")

        # Download locally if output_dir specified
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            detail_img = page.locator("img[alt='Mage media']").first
            src = await detail_img.get_attribute("src", timeout=5000)
            if src:
                if name:
                    safe_name = "".join(
                        c if c.isalnum() or c in " -_" else "_" for c in name
                    )
                else:
                    safe_name = "".join(
                        c if c.isalnum() or c in " -_" else "_" for c in prompt[:50]
                    )
                timestamp = int(time.time())
                filename = f"{safe_name}_{timestamp}.jpg"
                filepath = output_dir / filename

                response = await page.request.get(src)
                body = await response.body()
                filepath.write_bytes(body)
                print(f"  Downloaded: {filepath}")

        # Close the detail view
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)

        return str(filepath) if filepath else "saved"

    except Exception as e:
        print(f"  Warning: Could not save/download image: {e}")
        try:
            await page.keyboard.press("Escape")
        except Exception:
            pass

    return None


async def main():
    parser = argparse.ArgumentParser(description="Generate images on mage.space")
    parser.add_argument("prompt", nargs="?", help="Text prompt for image generation")
    parser.add_argument(
        "--batch",
        type=str,
        help="Markdown file with ### Name, **Ratio:**, and > prompt entries (e.g. room-prompts.md)",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model name for single-prompt mode (batch mode uses Flux.2 + Z-Image Turbo)",
    )
    parser.add_argument(
        "--ratio", type=str, help="Aspect ratio (e.g. '1:1', '16:9', '4:5')"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="./mage-output",
        help="Output directory for saved images",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no visible browser)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=60.0,
        help="Delay between batch generations (seconds)",
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Number of generations to skip (for resuming batches)",
    )
    args = parser.parse_args()

    if not args.prompt and not args.batch:
        parser.error("Provide a prompt or --batch file")

    # Collect prompts
    prompts = []
    if args.batch:
        prompts = parse_batch_markdown(args.batch)
        print(f"Loaded {len(prompts)} prompts from {args.batch}")
        current_sec = None
        for entry in prompts:
            if entry.get("section") != current_sec:
                current_sec = entry.get("section")
                print(f"\n  [{current_sec}]")
            print(f"    - {entry['name']} (ratio: {entry['ratio']})")
    else:
        prompts = [{"name": "prompt", "ratio": args.ratio, "prompt": args.prompt}]

    output_dir = Path(args.output)

    # Build generation plan: each prompt N times per model
    # Model names must match keys in MODEL_MAP
    MODELS = [
        ("Mango", 2),
        # ("Z-Image Turbo", 3),
        ("FLUX.2 Dev", 1),
    ]

    total_generations = len(prompts) * sum(count for _, count in MODELS)
    print(
        f"\nGeneration plan: {len(prompts)} prompts x {len(MODELS)} models = {total_generations} total images"
    )
    for model_name, count in MODELS:
        print(f"  {model_name}: {count}x each prompt")

    async with async_playwright() as p:
        # Use persistent context to preserve login session
        browser = await p.webkit.launch_persistent_context(
            USER_DATA_DIR,
            headless=args.headless,
            viewport={"width": 1280, "height": 900},
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        print(f"\nNavigating to {MAGE_URL}...")
        await page.goto(MAGE_URL, wait_until="domcontentloaded")
        await wait_for_page_ready(page)
        print("Page ready!")

        # Check if logged in
        send_visible = await page.locator("img[alt='Send']").is_visible()
        if not send_visible:
            print("\nNot logged in! Please log in manually in the browser window.")
            print("The script will continue once you're logged in (up to 5 min)...")
            await page.locator("img[alt='Send']").wait_for(
                state="visible", timeout=300000
            )
            print("Login detected, continuing...")
        else:
            print("Logged in!")

        results = []
        gen_num = 0
        batch = 0
        for model_name, count in MODELS:
            print(f"\n{'='*60}")
            print(f"MODEL: {model_name} ({count}x per prompt)")
            print(f"{'='*60}")

            # Select model once per model batch
            await select_model(page, model_name)
            await page.wait_for_timeout(500)
            batch += 1

            for entry in prompts:
                for run in range(1, count + 1):
                    gen_num += 1
                    if gen_num <= args.skip:
                        print(
                            f"\nSkipping generation {gen_num}/{total_generations} for {entry['name']} ({model_name} run {run}/{count})"
                        )
                        continue
                    if model_name.startswith("Z-Image") and run > 1:
                        print(
                            f"\nNote: Skipping run {run} for {model_name} since Z-Image models are deterministic"
                        )
                        continue
                    section = entry.get("section") or ""
                    section_label = f" [{section}]" if section else ""
                    print(
                        f"\n[{gen_num}/{total_generations}]{section_label} {entry['name']} — {model_name} (run {run}/{count})"
                    )

                    if gen_num > 1:
                        await asyncio.sleep(args.delay)

                    # Include section in output path for organization
                    section_dir = section.replace(" ", "_") if section else ""
                    model_dir = f"{batch} - {model_name}"
                    sub_dir = (
                        output_dir / section_dir / model_dir
                        if section_dir
                        else output_dir / model_dir
                    )

                    try:
                        result = await generate_image(
                            page,
                            (
                                entry.get("section_prompt", "") + ". "
                                if entry.get("section_prompt")
                                else "" if entry.get("section_prompt") else ""
                            )
                            + entry["prompt"],
                            model=None,  # already selected above
                            ratio=entry["ratio"],
                            output_dir=sub_dir,
                            name=entry.get("name"),
                        )
                    except Exception as e:
                        print(f"  ERROR: {e}")
                        print("  Waiting 60s, then restarting browser...")
                        await asyncio.sleep(60)
                        try:
                            await browser.close()
                        except Exception:
                            pass
                        browser = await p.webkit.launch_persistent_context(
                            USER_DATA_DIR,
                            headless=args.headless,
                            viewport={"width": 1280, "height": 900},
                        )
                        page = (
                            browser.pages[0]
                            if browser.pages
                            else await browser.new_page()
                        )
                        await page.goto(MAGE_URL, wait_until="domcontentloaded")
                        await wait_for_page_ready(page)
                        # Re-select model after browser restart
                        await select_model(page, model_name)
                        await page.wait_for_timeout(500)
                        result = None

                    results.append(
                        {
                            "section": entry.get("section"),
                            "name": entry["name"],
                            "model": model_name,
                            "run": run,
                            "prompt": entry["prompt"],
                            "file": result,
                        }
                    )

        print(f"\n{'='*60}")
        print(f"Done! Generated {len(results)} image(s)")
        print(f"{'='*60}")
        current_sec = None
        for r in results:
            if r.get("section") != current_sec:
                current_sec = r.get("section")
                if current_sec:
                    print(f"\n  [{current_sec}]")
            status = f"-> {r['file']}" if r["file"] else "(not saved)"
            print(f"    {r['name']} [{r['model']} #{r['run']}]: {status}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
