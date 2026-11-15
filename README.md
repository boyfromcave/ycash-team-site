# ycash-team-site — ycash.team

The start page for people who are new to Ycash: the Ycash logo, "Ycash = Your …" with a rotating
word, and eight product tiles in two rows ("Use Ycash", "Run and build"). Each tile leads to a
one-screen page on the site: what the product is, how to get it, one button. Plain static files,
no build step, no dependencies.

```bash
make serve   # http://127.0.0.1:8095/ (serves this directory as it is)
make check   # copy the published files into public/ and check them
make links   # the same, plus every external link must answer
```

| Path | What |
|---|---|
| `index.html` | the start page |
| `yew/`, `yecwallet/`, `explorer/`, `ycashd/`, `kogany/`, `yolo/`, `x402/`, `lightwalletd/` | one page per product (`index.html` each), served at `/<name>/` |
| `404.html` | the page CloudFront shows for a missing address |
| `assets/site.css` | look, layout and motion; colours are the variables at the top |
| `assets/site.js` | the rotating word and its pause button, the tile glow, the rise-in |
| `assets/ycash-logo.svg` | the Ycash logo (presentation attributes only, no `style=""`, for the CSP) |
| `scripts/check-site.py` | the check `make check` runs (standard library only) |
| `.github/workflows/check.yml` | pull requests: `make check` and `make links` |
| `.github/workflows/deploy.yml` | every push to `upgrade/vault`: check, then upload to S3 and invalidate CloudFront |

## Change things

- **Rotating words:** the `WORDS` list at the top of `assets/site.js` (order is the order shown;
  `HOLD_MS` is how long each stays). Without JavaScript the line reads "Ycash = Your Electronic Cash".
- **Tiles:** each `<li class="tile">` in `index.html`: an icon, the name (the link to the product
  page), one short line, and a small `<span class="tag">` label (Beta, Testnet, In development,
  Coming soon) where it is true.
- **Product pages:** one `<article class="card">` each: the name, one or two plain sentences, how to
  get it, one button. Facts come only from the product's own README and release notes (`AGENTS.md`).
- `make check` must pass: it refuses inline scripts and styles, broken links and skipped headings.

## How it is served

`https://ycash.team` (with `www.ycash.team` redirecting to it): a private S3 bucket behind
CloudFront, with HSTS, a strict Content-Security-Policy and the other security headers set by
CloudFront. The infrastructure is in the private operations repository (`site/ycash-team/`),
applied by hand; this repository's deploy workflow only uploads and invalidates, through an OIDC
role that may touch that bucket and that distribution and nothing else.

The policy the pages are written for:

```
default-src 'none'; script-src 'self'; style-src 'self' https://fonts.googleapis.com;
font-src https://fonts.gstatic.com; img-src 'self'; form-action 'none'; frame-ancestors 'none';
base-uri 'none'; object-src 'none'; upgrade-insecure-requests
```

The pages work with scripts off, with reduced motion (no drifting, no rising, a plain fade), and
down to a 320-pixel-wide phone.

## Licence

MIT (`LICENSE`), as the workspace's other component repositories (yew, chain-viz, x402-ycash).
