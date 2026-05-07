(function () {
  var currencyFmt = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function movementMeta(currentRank, previousRank) {
    if (previousRank == null) {
      return { cls: "board-glyph--flat", ch: "\u2013", label: "No prior day rank" };
    }
    if (currentRank < previousRank) {
      return { cls: "board-glyph--up", ch: "\u2191", label: "Rank improved since yesterday" };
    }
    if (currentRank > previousRank) {
      return { cls: "board-glyph--down", ch: "\u2193", label: "Rank dropped since yesterday" };
    }
    return { cls: "board-glyph--flat", ch: "\u2013", label: "Same rank as yesterday" };
  }

  function rowHtml(entry) {
    var m = movementMeta(entry.rank, entry.previous_rank);
    var bal = currencyFmt.format(Number(entry.balance));
    return (
      '<div class="board-row board-row--data">' +
      '<span class="board-glyph ' +
      m.cls +
      '" aria-label="' +
      escapeHtml(m.label) +
      '">' +
      m.ch +
      "</span>" +
      '<span class="board-col board-col--name">' +
      escapeHtml(entry.username) +
      "</span>" +
      '<span class="board-col board-col--pipe" aria-hidden="true">|</span>' +
      '<span class="board-col board-col--bal">' +
      escapeHtml(bal) +
      "</span>" +
      "</div>"
    );
  }

  function setTickerDuration() {
    var set = document.querySelector(".board__set:not(.board__set--dup)");
    if (!set) return;
    var pxPerSec = 22;
    var h = set.offsetHeight;
    var ms = Math.max((h / pxPerSec) * 1000, 1);
    document.documentElement.style.setProperty("--board-loop-duration", ms + "ms");
  }

  function showState(kind) {
    var status = document.getElementById("board-status");
    var err = document.getElementById("board-error");
    var empty = document.getElementById("board-empty");
    var viewport = document.getElementById("board-viewport");
    if (status) status.hidden = kind !== "loading";
    if (err) err.hidden = kind !== "error";
    if (empty) empty.hidden = kind !== "empty";
    if (viewport) viewport.hidden = kind !== "ready";
  }

  function render(entries) {
    var primary = document.getElementById("board-set-primary");
    var dup = document.getElementById("board-set-dup");
    if (!primary || !dup) return;

    var html = entries.map(rowHtml).join("");
    primary.innerHTML = html;
    dup.innerHTML = html;

    requestAnimationFrame(function () {
      setTickerDuration();
    });
  }

  async function load() {
    showState("loading");
    var errEl = document.getElementById("board-error");
    try {
      var res = await fetch("/leaderboard/public?limit=50", {
        headers: { Accept: "application/json" },
      });
      if (!res.ok) {
        throw new Error("Could not load leaderboard.");
      }
      var data = await res.json();
      var entries = data.entries || [];
      if (entries.length === 0) {
        showState("empty");
        return;
      }
      render(entries);
      showState("ready");
    } catch (e) {
      if (errEl) {
        errEl.textContent =
          e && e.message ? e.message : "Could not load leaderboard.";
        errEl.hidden = false;
      }
      showState("error");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", load);
  } else {
    load();
  }
})();
