"""Deterministic rendered-scene fingerprint for visual acceptance.

Raw screenshots remain audit artefacts and are still hashed byte-for-byte.  This
module additionally fingerprints the rendered scene (DOM order, visible content,
computed visual styles, geometry and pseudo-elements) so harmless rasterization
noise between otherwise identical GitHub runners does not manufacture a new UI.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Iterator

import yaml
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).resolve().parent.parent
SCREENSHOT_HEIGHT = 900
ROUTE_FILE = {
    "/orders": BASE / "assets/templates/orders-page.html",
    "/settings": BASE / "assets/templates/settings-page.html",
    "/analytics": BASE / "assets/templates/analytics-page.html",
}
MODAL_ROUTES = ("/settings", "/analytics")

VISUAL_PROPERTIES = (
    "display",
    "visibility",
    "opacity",
    "position",
    "z-index",
    "overflow-x",
    "overflow-y",
    "color",
    "background-color",
    "background-image",
    "background-size",
    "background-position",
    "border-top-width",
    "border-right-width",
    "border-bottom-width",
    "border-left-width",
    "border-top-style",
    "border-right-style",
    "border-bottom-style",
    "border-left-style",
    "border-top-color",
    "border-right-color",
    "border-bottom-color",
    "border-left-color",
    "border-radius",
    "box-shadow",
    "outline-width",
    "outline-style",
    "outline-color",
    "font-family",
    "font-size",
    "font-weight",
    "font-style",
    "line-height",
    "letter-spacing",
    "text-align",
    "text-decoration-line",
    "text-transform",
    "white-space",
    "transform",
    "transform-origin",
    "filter",
    "clip-path",
    "object-fit",
    "object-position",
    "pointer-events",
)

SCENE_JS = r"""
(meta) => {
  const properties = meta.properties;
  const round = value => Math.round(Number(value) * 1000) / 1000;
  const normalizeText = value => String(value || '').replace(/\s+/g, ' ').trim();
  const attrs = element => {
    const names = [
      'id', 'class', 'role', 'data-testid', 'aria-label', 'aria-hidden',
      'aria-modal', 'open', 'hidden', 'disabled'
    ];
    const out = {};
    for (const name of names) {
      if (element.hasAttribute(name)) out[name] = element.getAttribute(name);
    }
    return out;
  };
  const styleMap = (style) => {
    const out = {};
    for (const property of properties) out[property] = style.getPropertyValue(property);
    return out;
  };
  const rectOf = element => {
    const rect = element.getBoundingClientRect();
    return [round(rect.x), round(rect.y), round(rect.width), round(rect.height)];
  };
  const pseudo = (element, selector) => {
    const style = getComputedStyle(element, selector);
    const content = style.getPropertyValue('content');
    const visible = content && content !== 'none' && content !== 'normal' && content !== '""';
    if (!visible) return null;
    return {content, style: styleMap(style)};
  };
  const directText = element => normalizeText(
    [...element.childNodes]
      .filter(node => node.nodeType === Node.TEXT_NODE)
      .map(node => node.nodeValue)
      .join(' ')
  );

  const elements = [...document.body.querySelectorAll('*')].map((element, index) => {
    const style = getComputedStyle(element);
    return {
      index,
      tag: element.tagName.toLowerCase(),
      attrs: attrs(element),
      direct_text: directText(element),
      rect: rectOf(element),
      client: [element.clientWidth, element.clientHeight],
      scroll: [element.scrollWidth, element.scrollHeight],
      style: styleMap(style),
      before: pseudo(element, '::before'),
      after: pseudo(element, '::after'),
    };
  });

  const root = document.documentElement;
  const body = document.body;
  return {
    contract: 'render-scene-v1',
    route: meta.route,
    state: meta.state,
    viewport: [window.innerWidth, window.innerHeight, window.devicePixelRatio],
    document: {
      title: document.title,
      body_text: normalizeText(body.innerText),
      root_client: [root.clientWidth, root.clientHeight],
      root_scroll: [root.scrollWidth, root.scrollHeight],
      body_client: [body.clientWidth, body.clientHeight],
      body_scroll: [body.scrollWidth, body.scrollHeight],
    },
    elements,
  };
}
"""


def sha16_json(data: object) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def domain() -> dict:
    return yaml.safe_load((BASE / "supported-domain.yaml").read_text())["supported_domain"]


def case_name(route: str, viewport: int, state: str) -> str:
    suffix = "-modal-open" if state == "modal-open" else ""
    return f"{route.strip('/')}-{viewport}{suffix}.png"


def required_cases() -> Iterator[tuple[str, int, str]]:
    declared = domain()
    for route in declared["routes"]:
        for viewport in declared["viewport_widths"]:
            yield route, viewport, "default"
            if route in MODAL_ROUTES:
                yield route, viewport, "modal-open"


def expected_names() -> set[str]:
    return {case_name(route, viewport, state) for route, viewport, state in required_cases()}


def _settle(page) -> None:
    page.evaluate(
        """async () => {
          if (document.fonts && document.fonts.ready) await document.fonts.ready;
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        }"""
    )


def _prepare_state(page, route: str, state: str) -> None:
    page.goto(ROUTE_FILE[route].as_uri())
    _settle(page)
    if state == "modal-open":
        opener = page.locator('[data-testid="open-modal"]')
        if opener.count() != 1:
            raise RuntimeError(f"{route}: modal opener missing or ambiguous")
        opener.click()
        page.wait_for_function(
            """() => {
              const modal = document.querySelector('[data-testid="modal"]');
              if (!modal) return false;
              const style = getComputedStyle(modal);
              return modal.hasAttribute('open') && style.display !== 'none' && style.visibility !== 'hidden';
            }"""
        )
        _settle(page)


def capture_scene(page, route: str, viewport: int, state: str) -> dict:
    return page.evaluate(
        SCENE_JS,
        {
            "route": route,
            "viewport": viewport,
            "state": state,
            "properties": list(VISUAL_PROPERTIES),
        },
    )


def capture_required_scene_manifest(screenshot_dir: pathlib.Path | None = None) -> dict[str, str]:
    """Capture all required rendered states and return name -> scene digest.

    When ``screenshot_dir`` is supplied the same page instances also emit the raw
    PNG audit artefacts.  The scene digest never depends on PNG encoding or Skia
    anti-aliasing bytes.
    """
    declared = domain()
    height = int(declared.get("viewport_height", SCREENSHOT_HEIGHT))
    if screenshot_dir is not None:
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        for stale in screenshot_dir.glob("*.png"):
            stale.unlink()

    manifest: dict[str, str] = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            for route, viewport, state in required_cases():
                context = browser.new_context(viewport={"width": viewport, "height": height})
                try:
                    page = context.new_page()
                    _prepare_state(page, route, state)
                    name = case_name(route, viewport, state)
                    scene = capture_scene(page, route, viewport, state)
                    manifest[name] = sha16_json(scene)
                    if screenshot_dir is not None:
                        page.screenshot(
                            path=str(screenshot_dir / name),
                            full_page=True,
                            animations="disabled",
                        )
                finally:
                    context.close()
        finally:
            browser.close()
    return dict(sorted(manifest.items()))
