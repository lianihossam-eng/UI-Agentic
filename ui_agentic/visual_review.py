"""External-project visual capture and review identity."""
from __future__ import annotations

import hashlib
import json
import pathlib

from playwright.sync_api import sync_playwright

from core.coverage import measurement_readiness
from core.visual_fingerprint import REVIEW_FINGERPRINT_ALGO, review_fingerprint_manifest


class VisualReviewError(RuntimeError):
    pass


def _sha256_json(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _slug(route: str) -> str:
    return route.strip("/").replace("/", "-") or "root"


def _apply_state(page, state: str) -> None:
    if state == "default":
        return
    if state == "modal-open":
        opener = page.locator('[data-testid="open-modal"]')
        if opener.count() != 1:
            raise VisualReviewError("modal-open requires exactly one [data-testid='open-modal']")
        opener.click()
        page.wait_for_function(
            """() => {
              const modal=document.querySelector('[data-testid="modal"]');
              if(!modal) return false;
              const style=getComputedStyle(modal);
              const rect=modal.getBoundingClientRect();
              return modal.hasAttribute('open') && style.display!=='none' &&
                     style.visibility!=='hidden' && rect.width>0 && rect.height>0;
            }"""
        )
        return
    raise VisualReviewError(f"visual capture does not support declared state: {state}")


def expected_names(domain: dict) -> set[str]:
    names: set[str] = set()
    states_by_route = domain.get("states_by_route", {})
    for route in domain["routes"]:
        states = states_by_route.get(route, ["default"])
        if not states:
            states = ["default"]
        for viewport in domain["viewport_widths"]:
            for state in states:
                names.add(f"{_slug(route)}-{viewport}-{state}.png")
    return names


def capture_review_matrix(
    *,
    domain: dict,
    route_targets: dict[str, str],
    screenshot_dir: pathlib.Path,
) -> dict:
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    for old in screenshot_dir.glob("*.png"):
        old.unlink()

    captured: set[str] = set()
    browser_version = None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        browser_version = f"chromium@{browser.version}"
        states_by_route = domain.get("states_by_route", {})
        for route in domain["routes"]:
            target = route_targets.get(route)
            if not target:
                raise VisualReviewError(f"missing navigation target for {route}")
            states = states_by_route.get(route, ["default"]) or ["default"]
            for viewport in domain["viewport_widths"]:
                for state in states:
                    context = browser.new_context(
                        viewport={
                            "width": viewport,
                            "height": domain.get("viewport_height", 900),
                        }
                    )
                    page = context.new_page()
                    page.goto(target)
                    _apply_state(page, state)
                    readiness = measurement_readiness(page)
                    if readiness.get("status") != "PASS":
                        context.close()
                        raise VisualReviewError(
                            f"{route}@{viewport}:{state}: measurement readiness is not PASS"
                        )
                    name = f"{_slug(route)}-{viewport}-{state}.png"
                    page.screenshot(path=str(screenshot_dir / name), full_page=True)
                    captured.add(name)
                    context.close()
        browser.close()

    expected = expected_names(domain)
    if captured != expected:
        raise VisualReviewError(
            f"visual matrix mismatch missing={sorted(expected-captured)} "
            f"extra={sorted(captured-expected)}"
        )

    exact = {
        name: hashlib.sha256((screenshot_dir / name).read_bytes()).hexdigest()
        for name in sorted(expected)
    }
    paths = {name: screenshot_dir / name for name in sorted(expected)}
    review_manifest = review_fingerprint_manifest(paths)
    snapshot_digest = _sha256_json(exact)
    review_fingerprint_digest = _sha256_json(review_manifest)
    return {
        "browser": browser_version,
        "image_count": len(exact),
        "states": sorted(
            {
                state
                for route in domain["routes"]
                for state in (domain.get("states_by_route", {}).get(route, ["default"]) or ["default"])
            }
        ),
        "screenshot_digests": exact,
        "snapshot_digest": snapshot_digest,
        "review_fingerprint_algo": REVIEW_FINGERPRINT_ALGO,
        "review_fingerprint_manifest": review_manifest,
        "review_fingerprint_digest": review_fingerprint_digest,
    }
