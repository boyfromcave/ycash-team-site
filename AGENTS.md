# ycash-team-site — agent instructions

1. **Facts only, sourced.** Every product description, version, status label and host name comes from
   the yellowback workspace (`~/projects/yellowback-workspace`): the component repositories' READMEs and
   release notes (yew, yecwallet-dd, ycash6, kogany, yolo, x402-ycash, lightwalletd-dd), the explorer plan
   (`docs/plans/explorer/`) and kogany-site's pages. Never invent a release, date, feature or URL, and no
   roadmap promises. A service that is not live is labelled "Coming soon" and gets no button.
2. **Written for a newcomer.** Almost no text: the start page is the logo, "Ycash = Your …" and the
   tiles (no sentence under the rotating line, beta3 plan decision B3-D10); a product page is one or two
   plain sentences, how to get it, one button.
3. **Strict CSP.** No inline `<script>`, no `<style>` element, no `style=""` attribute (also not in an
   SVG), no `on*=` handler. `make check` enforces it; the policy itself is in ycash-ops `site/ycash-team/`.
4. **Works without JavaScript and with reduced motion.** `assets/site.js` only enhances.
5. **Naming** (workspace rule 6): Yellowback is the system, YED the unit; first mention
   "Ycash Yellowback (YED)". The decision-maker is "the Yellowback lead architect".
6. **Commits** as `boyfromcave <57612331+boyfromcave@users.noreply.github.com>` (from `~/.gitconfig`; no
   local `user.*`). No AI attribution anywhere: no trailers, footers or links.
