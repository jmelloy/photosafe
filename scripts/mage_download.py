#!/usr/bin/env python3
"""
Download all saved images from mage.space/creations with metadata sidecars.

Usage:
    # Download all saved creations
    python scripts/mage_download.py

    # Download specific collection
    python scripts/mage_download.py --collection "Clue"

    # Resume from where you left off (skips already downloaded)
    python scripts/mage_download.py --resume

    # Custom output directory
    python scripts/mage_download.py --output ./my-mage-archive

    # Headless mode
    python scripts/mage_download.py --headless

Output structure:
    output/
      YYYY/MM - Month/DD/{hash}.jpg
      YYYY/MM - Month/DD/{hash}.json  (sidecar with metadata)
      manifest.json                    (tracks downloaded UUIDs for resume)

Prerequisites:
    pip install playwright
    playwright install webkit
"""

import argparse
import asyncio
import base64
import functools
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from playwright.async_api import async_playwright

# Force unbuffered output
print = functools.partial(print, flush=True)

MAGE_URL = "https://www.mage.space/creations"
USER_DATA_DIR = os.path.expanduser("~/.mage-playwright-profile")
DEFAULT_OUTPUT = "./mage-archive"


def slugify(text: str, max_len: int = 80) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:max_len].rstrip("-")


def decode_thumbnail_url(thumb_url: str) -> str | None:
    """Extract full-res CDN URL from resize.mage.space thumbnail URL.

    Thumbnail format: https://resize.mage.space/plain/dpr:2/width:300/{base64_url}
    Decodes to: https://cdn3.mage.space/creations/{userId}/image/{hash}.jpg
    """
    try:
        # The base64 part is the last path segment
        parts = thumb_url.split("/")
        b64 = parts[-1]
        # Add padding if needed
        b64 += "=" * (4 - len(b64) % 4) if len(b64) % 4 else ""
        return base64.b64decode(b64).decode("utf-8")
    except Exception:
        return None


def parse_date(date_str: str) -> tuple[str, str, str]:
    """Parse 'Mar 15, 2026' into ('2026', '03 - March', '15')."""
    try:
        dt = datetime.strptime(date_str.strip(), "%b %d, %Y")
        return (
            dt.strftime("%Y"),
            dt.strftime("%m") + " - " + dt.strftime("%B"),
            dt.strftime("%d"),
        )
    except ValueError:
        # Fallback
        return "unknown", "unknown", "unknown"


def load_manifest(output_dir: Path) -> dict:
    """Load the download manifest (tracks completed UUIDs)."""
    manifest_path = output_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return {"downloaded": {}, "errors": [], "last_updated": None}


def save_manifest(output_dir: Path, manifest: dict):
    """Save the download manifest."""
    manifest["last_updated"] = datetime.now().isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def write_sidecar(json_path: Path, metadata: dict):
    """Write a JSON sidecar file with image metadata."""
    json_path.parent.mkdir(parents=True, exist_ok=True)

    sidecar = {
        "prompt": metadata.get("prompt", ""),
        "model": metadata.get("model", ""),
        "dimensions": metadata.get("dimensions", ""),
        "aspect_ratio": metadata.get("aspect_ratio", ""),
        "date_created": metadata.get("date_created", ""),
        "uuid": metadata.get("uuid", ""),
        "full_url": metadata.get("full_url", ""),
        "thumb_url": metadata.get("thumb_url", ""),
    }
    if metadata.get("collection"):
        sidecar["collection"] = metadata["collection"]

    json_path.write_text(json.dumps(sidecar, indent=2))


async def wait_for_creations_page(page, timeout=60000):
    """Wait for the creations page to be loaded."""
    await page.wait_for_load_state("domcontentloaded", timeout=timeout)
    # Wait for either the History or Saved button to be visible
    await page.get_by_role("button", name="Saved").wait_for(
        state="visible", timeout=timeout
    )


async def wait_for_initial_images(page):
    """Wait for the first batch of images to appear after tab switch."""
    print("  Waiting for images to load...")
    for _ in range(30):
        count = await page.locator('img[alt^="Creation preview"]').count()
        if count > 0:
            print(f"  Initial load: {count} images")
            return count
        await page.wait_for_timeout(500)
    count = await page.locator('img[alt^="Creation preview"]').count()
    if count == 0:
        print("  No images found after waiting.")
    return count


async def scroll_to_load_more(page, current_count: int) -> int:
    """Scroll down to trigger loading of more images. Returns new total count.

    Scrolls using ArrowDown keys and waits for the loading spinner to finish.
    Returns the updated image count (may be the same if no more to load).
    """
    # Scroll the last image into view
    last_img = page.locator('img[alt^="Creation preview"]').last
    try:
        await last_img.scroll_into_view_if_needed(timeout=3000)
    except Exception:
        pass

    # Use keyboard to scroll further
    for _ in range(10):
        await page.keyboard.press("ArrowDown")
    await page.keyboard.press("End")
    await page.wait_for_timeout(500)

    # Check if loading spinner appeared — wait for it to finish
    loading = page.get_by_text("Loading")
    try:
        await loading.first.wait_for(state="visible", timeout=2000)
        print(f"  Loading more... ({current_count} so far)")
        await loading.first.wait_for(state="hidden", timeout=60000)
        await page.wait_for_timeout(500)
    except Exception:
        pass

    return await page.locator('img[alt^="Creation preview"]').count()


async def extract_info_from_dialog(page) -> dict:
    """Extract metadata from the info dialog.

    The info dialog is a <dialog> element that appears when you click the (i) button.
    It contains the prompt text and key-value metadata pairs.
    """
    metadata = {}

    # Check if dialog is visible
    dialog = page.locator("dialog")
    dialog_count = await dialog.count()
    if dialog_count == 0:
        # Dialog might not be a <dialog> element — try finding by the close modal button
        close_modal = page.get_by_role("button", name="Close modal")
        if await close_modal.count() > 0:
            # Use JS to extract all text content near the close modal button
            pass

    # Use JavaScript to extract all metadata from the info panel
    info = await page.evaluate(
        """
        () => {
            const result = { prompt: '', model: '', dimensions: '', aspect_ratio: '', date_created: '' };

            // Try dialog element first
            let container = document.querySelector('dialog');
            if (!container || !container.open) {
                // Try finding the modal by its close button
                const closeModal = Array.from(document.querySelectorAll('button'))
                    .find(b => b.getAttribute('aria-label') === 'Close modal'
                           || b.textContent.trim() === 'Close modal');
                if (closeModal) {
                    // Walk up to find the modal container
                    container = closeModal.closest('[role="dialog"]') || closeModal.parentElement?.parentElement;
                }
            }

            if (!container) return result;

            // Get all paragraphs
            const paragraphs = Array.from(container.querySelectorAll('p'));
            const texts = paragraphs.map(p => p.textContent?.trim() || '');

            // Find prompt (longest text, not a metadata label)
            const labels = new Set(['Model', 'Dimensions', 'Aspect Ratio', 'Date Created', 'Copy Prompt', 'Show more']);
            let promptText = '';
            for (const t of texts) {
                if (t.length > 20 && !labels.has(t)) {
                    if (t.length > promptText.length) {
                        promptText = t;
                    }
                }
            }
            // Strip surrounding quotes
            promptText = promptText.replace(/^[""\u201c]+|[""\u201d]+$/g, '').trim();
            result.prompt = promptText;

            // Find metadata pairs
            for (let i = 0; i < texts.length; i++) {
                if (texts[i] === 'Model' && i + 1 < texts.length) result.model = texts[i + 1];
                if (texts[i] === 'Dimensions' && i + 1 < texts.length) result.dimensions = texts[i + 1];
                if (texts[i] === 'Aspect Ratio' && i + 1 < texts.length) result.aspect_ratio = texts[i + 1];
                if (texts[i] === 'Date Created' && i + 1 < texts.length) result.date_created = texts[i + 1];
            }

            return result;
        }
    """
    )

    if info:
        metadata = info

    # Try clicking "Show more" if prompt seems truncated
    if metadata.get("prompt") and len(metadata["prompt"]) > 200:
        try:
            show_more = page.get_by_role("button", name="Show more")
            if await show_more.count() > 0 and await show_more.first.is_visible():
                await show_more.first.click(timeout=2000)
                await page.wait_for_timeout(300)
                # Re-extract prompt
                expanded = await page.evaluate(
                    """
                    () => {
                        const container = document.querySelector('dialog')
                            || document.querySelector('[role="dialog"]');
                        if (!container) return '';
                        const paragraphs = Array.from(container.querySelectorAll('p'));
                        const labels = new Set(['Model', 'Dimensions', 'Aspect Ratio', 'Date Created', 'Copy Prompt', 'Show more', 'Show less']);
                        let longest = '';
                        for (const p of paragraphs) {
                            const t = p.textContent?.trim() || '';
                            if (t.length > 20 && !labels.has(t) && t.length > longest.length) {
                                longest = t;
                            }
                        }
                        return longest.replace(/^[""\u201c]+|[""\u201d]+$/g, '').trim();
                    }
                """
                )
                if expanded and len(expanded) > len(metadata.get("prompt", "")):
                    metadata["prompt"] = expanded
        except Exception:
            pass

    return metadata


async def _close_all_overlays(page):
    """Close any open dialogs/detail views and verify we're back to the grid."""
    # Close info dialog if open
    for _ in range(3):
        close_modal = page.get_by_role("button", name="Close modal")
        if await close_modal.count() > 0:
            try:
                await close_modal.click(timeout=2000)
                await page.wait_for_timeout(400)
            except Exception:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(300)
        else:
            break

    # Close any modal overlays via JS (handles the data-fixed overlay)
    await page.evaluate(
        """
        () => {
            // Remove any modal overlays blocking the grid
            document.querySelectorAll('[data-fixed="true"].mage-Modal-overlay, .mage-Overlay-root').forEach(el => {
                // Click the overlay to dismiss, or find its close button
                const portal = el.closest('[data-portal="true"]');
                if (portal) {
                    const closeBtn = portal.querySelector('button[aria-label="Close modal"], button[aria-label="Close"]');
                    if (closeBtn) closeBtn.click();
                }
            });
        }
    """
    )
    await page.wait_for_timeout(300)

    # Close detail view if open
    for _ in range(3):
        close_btn = page.get_by_role("button", name="Close").last
        if await close_btn.count() > 0:
            try:
                await close_btn.click(timeout=2000)
                await page.wait_for_timeout(400)
            except Exception:
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(300)

        # Check if grid is visible and no overlay is blocking
        overlay = page.locator('[data-fixed="true"].mage-Modal-overlay')
        if await overlay.count() == 0:
            grid_img = page.locator('img[alt^="Creation preview"]').first
            if await grid_img.count() > 0 and await grid_img.is_visible():
                return

    # Last resort — spam Escape
    for _ in range(5):
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)

    # Final check — if overlay persists, remove it from DOM
    await page.evaluate(
        """
        () => {
            document.querySelectorAll('[data-portal="true"]').forEach(el => {
                if (el.querySelector('.mage-Modal-overlay, .mage-Overlay-root')) {
                    el.remove();
                }
            });
        }
    """
    )
    await page.wait_for_timeout(200)


async def _reload_and_setup(page, args):
    """Reload the creations page and re-navigate to the right tab/collection."""
    print("  Reloading page...")
    await page.goto(MAGE_URL, wait_until="domcontentloaded")
    await wait_for_creations_page(page)
    if args.tab == "saved":
        await page.get_by_role("button", name="Saved").click()
        await page.wait_for_timeout(1000)
    if args.collection:
        collection_tab = page.get_by_role("tab", name=re.compile(args.collection, re.I))
        if await collection_tab.count() > 0:
            await collection_tab.first.click()
            await page.wait_for_timeout(1000)
    total = await wait_for_initial_images(page)
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)
    return total


async def download_creation(
    page, index: int, total: int, output_dir: Path, manifest: dict
) -> dict | None:
    """Click the i-th image, extract info, download, and return metadata.

    Uses keyboard arrows to navigate (assumes detail view is already open for previous image,
    or clicks the image to open it fresh).
    """
    # Get the image element
    images = page.locator('img[alt^="Creation preview"]')
    count = await images.count()
    if index >= count:
        return None

    img = images.nth(index)

    # Extract UUID from alt text
    alt = await img.get_attribute("alt")
    uuid = alt.replace("Creation preview ", "").strip()

    # Check if already downloaded — return "skipped" sentinel (not a new download)
    if uuid in manifest.get("downloaded", {}):
        return "skipped"

    # Get thumbnail URL for decoding full-res URL
    thumb_url = await img.get_attribute("src") or ""
    full_url = decode_thumbnail_url(thumb_url)

    print(f"\n[{index + 1}/{total}] {uuid}")

    # Ensure no overlays are blocking before clicking
    await _close_all_overlays(page)
    await page.wait_for_timeout(300)

    # Scroll image into view and click to open detail view
    try:
        await img.scroll_into_view_if_needed(timeout=5000)
        await page.wait_for_timeout(200)
        try:
            await img.click(timeout=5000)
        except Exception:
            # Overlay may still be intercepting — force-dismiss and retry
            print(f"  Click intercepted, dismissing overlays and retrying...")
            for _ in range(5):
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(300)
            await _close_all_overlays(page)
            await page.wait_for_timeout(500)
            await img.scroll_into_view_if_needed(timeout=5000)
            await page.wait_for_timeout(200)
            try:
                await img.click(timeout=5000)
            except Exception:
                # Last resort: force click bypasses actionability checks
                print(f"  Retrying with force click...")
                await img.click(timeout=5000, force=True)
        await page.wait_for_timeout(800)
    except Exception as e:
        print(f"  Error clicking image: {e}")
        manifest.setdefault("errors", []).append({"uuid": uuid, "error": str(e)})
        return None

    # Click the info (i) button — it's the button right before "Edit" in the toolbar
    # Toolbar order: [+] [-] [shuffle] [download] [(i)] [Edit] [Post] [Copy Prompt] ...
    try:
        # Wait for the detail view toolbar to appear
        await page.get_by_role("button", name="Edit").wait_for(
            state="visible", timeout=5000
        )
        await page.wait_for_timeout(300)

        # Find the (i) button: it's a sibling button just before "Edit"
        # Use JS to find it reliably
        info_clicked = await page.evaluate(
            """
            () => {
                // Find all buttons with specific text that appear in the detail toolbar
                const allButtons = Array.from(document.querySelectorAll('button'));
                const closeBtn = allButtons.find(b => b.textContent.trim() === 'Close');
                if (!closeBtn) return 'no-close. visible buttons: ' +
                    allButtons.filter(b => b.offsetParent !== null).map(b => b.textContent.trim().substring(0, 30)).filter(t => t).join(' | ');

                // Walk up from Close button to find the container with all toolbar buttons
                let container = closeBtn.parentElement;
                let buttons = [];
                for (let depth = 0; depth < 5; depth++) {
                    buttons = Array.from(container.querySelectorAll('button'));
                    if (buttons.length >= 5) break;
                    container = container.parentElement;
                    if (!container) break;
                }

                const btnTexts = buttons.map(b => b.textContent.trim());

                // The (i) button is icon-only right before "Edit"
                const editIdx = btnTexts.indexOf('Edit');
                if (editIdx < 0) return 'no-edit in ' + buttons.length + ' buttons: ' + btnTexts.join(' | ');

                if (editIdx > 0) {
                    buttons[editIdx - 1].click();
                    return 'clicked-idx-' + (editIdx - 1) + ' of ' + btnTexts.join(' | ');
                }
                return 'edit-at-0';
            }
        """
        )

        if not info_clicked.startswith("clicked"):
            raise RuntimeError(f"Info button result: {info_clicked}")

        await page.wait_for_timeout(800)
    except Exception as e:
        print(f"  Warning: Could not click info button: {e}")
        # Try to close detail view and continue
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
        manifest.setdefault("errors", []).append(
            {"uuid": uuid, "error": f"info button: {e}"}
        )
        return None

    # Extract metadata from the info dialog
    metadata = await extract_info_from_dialog(page)
    metadata["uuid"] = uuid
    metadata["full_url"] = full_url or ""
    metadata["thumb_url"] = thumb_url

    # If metadata extraction failed (no date = dialog wasn't showing), raise to trigger reload
    if not metadata.get("date_created"):
        print(f"  Metadata extraction failed (no date_created), page state is stale")
        raise RuntimeError(f"Empty metadata for {uuid} — need page reload")

    # Close the info dialog
    await _close_all_overlays(page)

    # Determine output paths
    date_created = metadata.get("date_created", "")
    year, month_name, day = parse_date(date_created)

    # Determine image filename from CDN URL or UUID
    if full_url:
        img_filename = full_url.split("/")[-1]
    else:
        img_filename = f"{uuid}.jpg"

    img_dir = output_dir / year / month_name / day
    img_path = img_dir / img_filename

    # JSON sidecar named same as image
    img_stem = Path(img_filename).stem
    json_path = img_dir / f"{img_stem}.json"

    # Download the full-res image
    if full_url and not img_path.exists():
        try:
            img_dir.mkdir(parents=True, exist_ok=True)
            response = await page.request.get(full_url)
            body = await response.body()
            img_path.write_bytes(body)
            print(f"  Downloaded: {img_path} ({len(body) // 1024}KB)")
        except Exception as e:
            print(f"  Error downloading image: {e}")
            manifest.setdefault("errors", []).append(
                {"uuid": uuid, "error": f"download: {e}"}
            )
    elif img_path.exists():
        print(f"  Image already exists: {img_path}")

    # Write JSON sidecar
    write_sidecar(json_path, metadata)
    print(f"  Sidecar: {json_path}")

    # Record in manifest
    record = {
        "uuid": uuid,
        "prompt": metadata.get("prompt", "")[:200],
        "model": metadata.get("model", ""),
        "date_created": metadata.get("date_created", ""),
        "image_path": str(img_path),
        "sidecar_path": str(json_path),
        "downloaded_at": datetime.now().isoformat(),
    }
    manifest["downloaded"][uuid] = record
    return record


async def main():
    parser = argparse.ArgumentParser(
        description="Download saved images from mage.space/creations"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=DEFAULT_OUTPUT,
        help="Output directory (default: ./mage-archive)",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Download only a specific collection tab (e.g. 'Clue', 'Unorganized')",
    )
    parser.add_argument(
        "--tab",
        type=str,
        default="saved",
        choices=["saved", "history"],
        help="Which tab to download from (default: saved)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no visible browser)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from manifest, skipping already-downloaded images",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of images to download (0 = unlimited)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=0,
        help="Start from this image index (0-based)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between downloads in seconds (default: 0.5)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load manifest for resume capability
    manifest = (
        load_manifest(output_dir)
        if args.resume
        else {
            "downloaded": {},
            "errors": [],
            "last_updated": None,
        }
    )

    print(f"Output directory: {output_dir}")
    if args.resume:
        print(f"Resuming: {len(manifest.get('downloaded', {}))} already downloaded")
        manifest["errors"] = []

    async with async_playwright() as p:
        browser = await p.webkit.launch_persistent_context(
            USER_DATA_DIR,
            headless=args.headless,
            viewport={"width": 1400, "height": 900},
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        print(f"\nNavigating to {MAGE_URL}...")
        await page.goto(MAGE_URL, wait_until="domcontentloaded")
        await wait_for_creations_page(page)
        print("Page ready!")

        # Click the appropriate tab
        if args.tab == "saved":
            saved_btn = page.get_by_role("button", name="Saved")
            await saved_btn.click()
            await page.wait_for_timeout(1000)
            print("Switched to Saved tab")

        # Click collection tab if specified
        if args.collection:
            collection_tab = page.get_by_role(
                "tab", name=re.compile(args.collection, re.I)
            )
            if await collection_tab.count() > 0:
                await collection_tab.first.click()
                await page.wait_for_timeout(1000)
                print(f"Selected collection: {args.collection}")
            else:
                print(f"Warning: Collection '{args.collection}' not found")

        # Wait for initial images (don't load all upfront)
        total = await wait_for_initial_images(page)

        if total == 0:
            print("No images found!")
            await browser.close()
            return

        # Scroll back to top
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)

        print(f"\nStarting download ({total} images loaded so far)...")
        if args.start > 0:
            print(f"Starting from index {args.start}")

        downloaded = 0
        errors = 0
        consecutive_errors = 0
        i = args.start
        limit_remaining = args.limit if args.limit > 0 else float("inf")
        stale_scroll_rounds = 0
        STALE_SCROLL_LIMIT = 5
        CONSECUTIVE_ERROR_LIMIT = 3

        while limit_remaining > 0:
            # If we've caught up to loaded images, scroll to load more
            if i >= total:
                prev_total = total
                total = await scroll_to_load_more(page, total)
                if total > prev_total:
                    stale_scroll_rounds = 0
                    print(f"  Loaded more: {total} images now available")
                else:
                    stale_scroll_rounds += 1
                    if stale_scroll_rounds >= STALE_SCROLL_LIMIT:
                        # One last long wait
                        await page.keyboard.press("End")
                        await page.wait_for_timeout(10000)
                        total = await page.locator(
                            'img[alt^="Creation preview"]'
                        ).count()
                        if total <= prev_total:
                            print(f"  No more images to load. Total: {total}")
                            break
                        stale_scroll_rounds = 0
                    continue

            try:
                result = await download_creation(page, i, total, output_dir, manifest)
                if result == "skipped":
                    # Already in manifest — don't count as new download
                    consecutive_errors = 0
                elif result:
                    downloaded += 1
                    limit_remaining -= 1
                    consecutive_errors = 0
                elif result is None:
                    # download_creation returned None (soft error)
                    consecutive_errors += 1

                # Save manifest periodically
                if (i + 1) % 10 == 0:
                    save_manifest(output_dir, manifest)
                    print(
                        f"\n  --- Progress: {i + 1}/{total} processed, {downloaded} downloaded ---\n"
                    )

                if args.delay > 0:
                    await asyncio.sleep(args.delay)

            except Exception as e:
                errors += 1
                consecutive_errors += 1
                print(f"  ERROR processing image {i}: {e}")
                manifest.setdefault("errors", []).append(
                    {
                        "index": i,
                        "error": str(e),
                        "time": datetime.now().isoformat(),
                    }
                )

                # Close any overlays and keep going
                try:
                    await _close_all_overlays(page)
                except Exception:
                    pass

            # If too many consecutive errors, reload the page to reset state
            if consecutive_errors >= CONSECUTIVE_ERROR_LIMIT:
                print(
                    f"\n  {consecutive_errors} consecutive errors — reloading page..."
                )
                save_manifest(output_dir, manifest)
                try:
                    total = await _reload_and_setup(page, args)
                    consecutive_errors = 0
                    print(
                        f"  Page reloaded. {total} images loaded. Continuing from index {i + 1}..."
                    )
                except Exception as reload_err:
                    print(f"  Reload failed: {reload_err}")
                    break

            i += 1

        # Final save
        save_manifest(output_dir, manifest)

        print(f"\n{'='*60}")
        print(f"Done! Downloaded {downloaded} new images")
        print(f"Total in manifest: {len(manifest.get('downloaded', {}))}")
        print(f"Errors: {len(manifest.get('errors', []))}")
        print(f"Output: {output_dir}")
        print(f"{'='*60}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
