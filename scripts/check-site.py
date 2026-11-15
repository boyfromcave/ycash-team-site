#!/usr/bin/env python3
# Copyright (c) 2026 The Ycash developers. MIT licence (LICENSE).
"""Check the built site (public/) before it is deployed. Standard library only.

  python3 -I scripts/check-site.py public              # structure, CSP, accessibility basics, internal links
  python3 -I scripts/check-site.py --external public   # the same, plus every external link answers

Fails (exit 1) on:
- HTML that does not nest: an end tag without its start tag, an element left open;
- a page without <!doctype html>, <html lang>, <meta charset>, the viewport, one <title>, a description;
- anything a strict Content-Security-Policy (no 'unsafe-inline') would block: an inline <script>, a
  <style> element, a style="" attribute (also inside the SVG files), an on*="" handler, a javascript: URL;
  a script or stylesheet from an origin the policy does not list;
- accessibility basics: an <img> without alt, not exactly one <h1>, a heading level skipped, a
  duplicate id, a link without text, an <svg> that is neither hidden nor labelled;
- a stylesheet whose braces do not balance (a stray } silently drops every rule after it);
- an internal link or #fragment that leads nowhere; an external link that is not https;
- with --external: an external link that does not answer 2xx/3xx (HEAD, then GET).
"""
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
# Elements whose end tag HTML lets you leave out; we never do, but do not fail on them.
OPTIONAL_END = {"p", "li", "dt", "dd", "option", "tr", "td", "th", "thead", "tbody", "tfoot"}
# SVG children written as self-closing (<path .../>) arrive as startendtag: fine.
SCRIPT_ORIGINS = {"self"}
STYLE_ORIGINS = {"self", "https://fonts.googleapis.com"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.errors = []
        self.stack = []
        self.doctype = False
        self.lang = None
        self.charset = False
        self.viewport = False
        self.description = False
        self.titles = 0
        self.headings = []
        self.ids = set()
        self.links = []          # (href, line)
        self.svg_depth = 0
        self.in_script_src = False
        self.link_text = None    # collecting text of the current <a>
        self.link_label = False
        self.link_line = 0

    def err(self, msg):
        self.errors.append(f"line {self.getpos()[0]}: {msg}")

    def handle_decl(self, decl):
        if decl.lower() == "doctype html":
            self.doctype = True

    def check_attrs(self, tag, attrs):
        a = dict(attrs)
        for name, value in attrs:
            if name == "style":
                self.err(f"<{tag} style=...>: inline style, blocked by the CSP")
            if name.startswith("on"):
                self.err(f"<{tag} {name}=...>: inline handler, blocked by the CSP")
            if value and value.strip().lower().startswith("javascript:"):
                self.err(f"<{tag} {name}=javascript:...>: blocked by the CSP")
        if "id" in a:
            if a["id"] in self.ids:
                self.err(f"duplicate id {a['id']!r}")
            self.ids.add(a["id"])
        return a

    def handle_starttag(self, tag, attrs):
        a = self.check_attrs(tag, attrs)
        self.visit(tag, a, self_closing=False)
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_startendtag(self, tag, attrs):
        a = self.check_attrs(tag, attrs)
        self.visit(tag, a, self_closing=True)

    def visit(self, tag, a, self_closing):
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "meta":
            if "charset" in a:
                self.charset = True
            if a.get("name") == "viewport":
                self.viewport = True
            if a.get("name") == "description" and a.get("content"):
                self.description = True
        elif tag == "title":
            self.titles += 1
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append((int(tag[1]), self.getpos()[0]))
        elif tag == "img":
            if "alt" not in a:
                self.err("<img> without alt")
            self.links.append((a.get("src", ""), self.getpos()[0]))
        elif tag == "script":
            src = a.get("src")
            if not src:
                self.err("inline <script>: blocked by the CSP")
            else:
                self.origin_ok(src, SCRIPT_ORIGINS, "script")
                self.links.append((src, self.getpos()[0]))
        elif tag == "style":
            self.err("<style> element: blocked by the CSP")
        elif tag == "link":
            href = a.get("href", "")
            if "stylesheet" in a.get("rel", "").split():
                self.origin_ok(href, STYLE_ORIGINS, "stylesheet")
            if a.get("rel") not in ("preconnect", "canonical"):
                self.links.append((href, self.getpos()[0]))
        elif tag == "a":
            self.links.append((a.get("href", ""), self.getpos()[0]))
            if not self_closing:
                self.link_text = ""
                self.link_label = bool(a.get("aria-label"))
                self.link_line = self.getpos()[0]
        elif tag == "svg":
            labelled = a.get("aria-hidden") == "true" or a.get("aria-label") or a.get("role") == "img"
            if not labelled:
                self.err("<svg> neither aria-hidden nor labelled")
        if tag == "img" and self.link_text is not None and a.get("alt"):
            self.link_text += a["alt"]

    def origin_ok(self, url, allowed, what):
        if url.startswith("/") and not url.startswith("//"):
            return
        origin = "/".join(url.split("/")[:3])
        if origin not in allowed:
            self.err(f"{what} from {origin}: not in the CSP")

    def handle_data(self, data):
        if self.link_text is not None:
            self.link_text += data

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "a" and self.link_text is not None:
            if not self.link_text.strip() and not self.link_label:
                self.errors.append(f"line {self.link_line}: link without text")
            self.link_text = None
        while self.stack and self.stack[-1][0] != tag and self.stack[-1][0] in OPTIONAL_END:
            self.stack.pop()
        if not self.stack or self.stack[-1][0] != tag:
            open_tag = self.stack[-1] if self.stack else None
            self.err(f"</{tag}> does not close {('<%s> from line %d' % open_tag) if open_tag else 'anything'}")
            return
        self.stack.pop()

    def finish(self):
        self.close()
        for tag, line in self.stack:
            if tag not in OPTIONAL_END:
                self.errors.append(f"line {line}: <{tag}> never closed")
        if not self.doctype:
            self.errors.append("no <!doctype html>")
        if not self.lang:
            self.errors.append("<html> without lang")
        if not self.charset:
            self.errors.append("no <meta charset>")
        if not self.viewport:
            self.errors.append("no viewport <meta>")
        if not self.description:
            self.errors.append("no description <meta>")
        if self.titles != 1:
            self.errors.append(f"{self.titles} <title> elements, want 1")
        h1 = [h for h in self.headings if h[0] == 1]
        if len(h1) != 1:
            self.errors.append(f"{len(h1)} <h1> elements, want 1")
        level = 0
        for lvl, line in self.headings:
            if lvl > level + 1:
                self.errors.append(f"line {line}: <h{lvl}> after <h{level}> skips a level")
            level = lvl


def check_svg(path):
    text = path.read_text(encoding="utf-8")
    bad = []
    if " style=" in text or "<style" in text:
        bad.append("style in an SVG: the CSP (style-src without 'unsafe-inline') applies to it as served")
    if "<script" in text:
        bad.append("<script> in an SVG")
    return bad


def check_css(path):
    """Braces must balance (outside comments and strings): one stray } drops the rules after it."""
    text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    depth = 0
    for n, line in enumerate(text.split("\n"), 1):
        for ch in line:
            depth += ch == "{"
            depth -= ch == "}"
            if depth < 0:
                return [f"line {n}: a }} without its {{"]
    return [f"{depth} unclosed {{"] if depth else []


def check_external(url):
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": "ycash-team-site-linkcheck"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                if resp.status < 400:
                    return None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                return None  # rate limited: the link exists
            if method == "GET":
                return f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001 - report any network failure
            if method == "GET":
                return str(e)
    return "no answer"


def main(argv):
    external = "--external" in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    root = Path(args[0])
    errors = 0
    pages = {}
    externals = {}

    for svg in sorted(root.rglob("*.svg")):
        for msg in check_svg(svg):
            print(f"{svg.relative_to(root)}: {msg}")
            errors += 1

    for css in sorted(root.rglob("*.css")):
        for msg in check_css(css):
            print(f"{css.relative_to(root)}: {msg}")
            errors += 1

    for html in sorted(root.rglob("*.html")):
        p = Page()
        p.feed(html.read_text(encoding="utf-8"))
        p.finish()
        pages[html] = p
        for msg in p.errors:
            print(f"{html.relative_to(root)}: {msg}")
            errors += 1

    for html, p in pages.items():
        rel = html.relative_to(root)
        for href, line in p.links:
            if not href:
                print(f"{rel}: line {line}: empty link")
                errors += 1
            elif href.startswith("http://"):
                print(f"{rel}: line {line}: {href} is not https")
                errors += 1
            elif href.startswith("https://"):
                externals.setdefault(href, f"{rel}:{line}")
            elif href.startswith("mailto:"):
                continue
            elif href.startswith("#"):
                if href[1:] not in p.ids:
                    print(f"{rel}: line {line}: no id {href[1:]!r} on this page")
                    errors += 1
            elif href.startswith("/"):
                path, _, frag = href.partition("#")
                target = root / path.lstrip("/")
                if path.endswith("/"):
                    target = target / "index.html"
                if not target.exists():
                    print(f"{rel}: line {line}: broken link {href}")
                    errors += 1
                elif frag and target.suffix == ".html" and frag not in pages[target].ids:
                    print(f"{rel}: line {line}: {href}: no id {frag!r} there")
                    errors += 1
            else:
                print(f"{rel}: line {line}: relative link {href!r}: use a root-relative /path")
                errors += 1

    if external:
        for url, where in sorted(externals.items()):
            problem = check_external(url)
            if problem:
                print(f"{where}: {url}: {problem}")
                errors += 1

    print(f"{len(pages)} pages, {len(externals)} external links"
          f"{' checked' if external else ''}, {errors} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
