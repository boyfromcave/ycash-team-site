# ycash.team: plain static files, no build step beyond copying what is published into public/.
# Copyright (c) 2026 The Ycash developers. MIT licence (LICENSE).
SITE := index.html 404.html robots.txt assets yew yew-web yecwallet explorer ycashd kogany yolo x402 lightwalletd

.PHONY: build check links serve clean
build:
	rm -rf public && mkdir public && cp -R $(SITE) public/
	find public -name .DS_Store -delete
check: build
	python3 -I scripts/check-site.py public
links: build
	python3 -I scripts/check-site.py --external public
serve:
	python3 -I -m http.server 8095 --bind 127.0.0.1
clean:
	rm -rf public
