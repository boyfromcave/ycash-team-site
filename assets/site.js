// ycash.team: the rotating word, its pause button, the tile glow, the rise-in.
// Copyright (c) 2026 The Ycash developers. MIT licence (LICENSE).
// Plain script, no dependencies, no inline code. Without it every page still reads
// correctly: "Ycash" and "Your Electronic Cash", and every tile is a normal link.
(function () {
  "use strict";

  var root = document.documentElement;
  root.classList.remove("no-js");
  root.classList.add("js");

  var WORDS = [
    "Electronic Cash", "Team", "Life", "Family", "Collateral", "Assets",
    "Wallet", "Future", "❤️", "Friends", "🛡️", "Vault"
  ];
  var HOLD_MS = 2200;   // how long a word stays
  var SWAP_MS = 430;    // the out-animation, matched to the CSS

  var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------- the rotating word (start page only) ----------

  // The slot reserves the longest phrase in CSS (.sizer), so changing the word moves nothing else:
  // "Your" keeps its place to the pixel.
  var hero = document.getElementById("hero");
  var word = document.getElementById("word");

  function isEmoji(text) { return !/[A-Za-z]/.test(text); }

  function show(text) {
    word.textContent = text;
    word.classList.toggle("is-emoji", isEmoji(text));
    word.classList.remove("is-out");
    // next frame, so the browser sees the starting position first
    requestAnimationFrame(function () {
      requestAnimationFrame(function () { word.classList.add("is-in"); });
    });
  }

  if (hero && word) {
    var index = 0;
    var timer = null;
    var paused = false;

    var step = function () {
      index = (index + 1) % WORDS.length;
      word.classList.remove("is-in");
      word.classList.add("is-out");
      setTimeout(function () { show(WORDS[index]); }, calm ? 200 : SWAP_MS);
    };

    var start = function () {
      if (!timer && !paused && !document.hidden) { timer = setInterval(step, HOLD_MS + SWAP_MS); }
    };
    var stop = function () { clearInterval(timer); timer = null; };

    // A pause button (WCAG 2.2.2): moving text must be stoppable.
    {
      var ns = "http://www.w3.org/2000/svg";
      var button = document.createElement("button");
      button.type = "button";
      button.className = "pause";
      button.setAttribute("aria-pressed", "false");
      button.setAttribute("aria-label", "Pause the moving words");
      [["bars", "M8 5v14M16 5v14"], ["play", "M7 5l12 7-12 7z"]].forEach(function (icon) {
        var svg = document.createElementNS(ns, "svg");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.setAttribute("class", icon[0]);
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("fill", "none");
        svg.setAttribute("stroke", "currentColor");
        svg.setAttribute("stroke-width", "2.2");
        svg.setAttribute("stroke-linecap", "round");
        svg.setAttribute("stroke-linejoin", "round");
        var path = document.createElementNS(ns, "path");
        path.setAttribute("d", icon[1]);
        svg.appendChild(path);
        button.appendChild(svg);
      });
      button.addEventListener("click", function () {
        paused = !paused;
        button.setAttribute("aria-pressed", paused ? "true" : "false");
        button.setAttribute("aria-label", paused ? "Play the moving words" : "Pause the moving words");
        if (paused) { stop(); } else { start(); }
      });
      hero.appendChild(button);
    }

    // do not spin in a background tab
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { stop(); } else { start(); }
    });
    start();
  }

  // ---------- tiles: a glow that follows the pointer, and a staggered rise into view ----------

  var tiles = Array.prototype.slice.call(document.querySelectorAll(".tile"));
  var showAll = function () { tiles.forEach(function (tile) { tile.classList.add("seen"); }); };

  try {
    tiles.forEach(function (tile) {
      tile.addEventListener("pointermove", function (event) {
        var box = tile.getBoundingClientRect();
        tile.style.setProperty("--mx", (event.clientX - box.left) + "px");
        tile.style.setProperty("--my", (event.clientY - box.top) + "px");
      });
    });

    if ("IntersectionObserver" in window && !calm) {
      var answered = false;
      var seen = new IntersectionObserver(function (entries) {
        answered = true;
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) { return; }
          var order = tiles.indexOf(entry.target);
          setTimeout(function () { entry.target.classList.add("seen"); }, (order % 5) * 80);
          seen.unobserve(entry.target);
        });
      }, { threshold: 0.15 });
      tiles.forEach(function (tile) { seen.observe(tile); });
      // The observer reports every tile once right after observe(). If it stays silent (some
      // headless or prerendering browsers), show the tiles rather than leave them hidden.
      setTimeout(function () { if (!answered) { seen.disconnect(); showAll(); } }, 1200);
    } else {
      showAll();
    }
  } catch (e) {
    showAll();
  }
})();
