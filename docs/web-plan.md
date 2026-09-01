# Running Chess Rating in a Browser with Pyodide

## Goal

Run the existing `rating` lookup logic in a browser tab via
[Pyodide](https://pyodide.org), driven by a small HTML/JS front end instead
of the `argparse` CLI, while keeping the desktop CLI and its pytest suite as
the primary development environment.

## Scope note

All development and testing continues on the desktop (`pytest`, the `rating`
console script, `.venv`). The browser/Pyodide layer is a **deployment
target**, not a second codebase to maintain: it gets no unit tests, no
README, and no doc coverage of its own beyond this plan. Anything that needs
real test coverage should be pushed down into the existing `rating` package
so it's exercised by the normal desktop pytest suite.

## Current architecture (recap)

See [ports_and_adapters.md](ports_and_adapters.md). Relevant for this plan:

- `rating/application/rating.py` is the composition root: it parses `argv`,
  builds a `RequestsHttpAdapter`, picks a `RatingPort` adapter, calls
  `fetch()`, logs the result through `SQLiteProfileLogAdapter`, and prints.
- `RequestsHttpAdapter` uses the `requests` library and real TCP sockets.
- `ConfigLoader` reads a `.env` file from a `platformdirs` OS config
  directory.
- `SQLiteProfileLogAdapter` writes to a local file
  (`~/.local/share/chess-rating/ratings.db`) using the stdlib `sqlite3`
  module.
- Provider adapters (`uscf.py`, `lichess.py`, `chesscom.py`, `fide.py`) hard-code
  their base URLs as f-strings and call `requests`/BeautifulSoup indirectly
  through `HttpPort`.

None of this was written with a browser sandbox in mind, so several pieces
need new adapters or small seams. The hexagonal structure already in place
is what makes this tractable — the plan below adds **driving and driven
adapters**, not new domain logic.

## Blockers, in order of how much they constrain the design

### 1. CORS — the biggest unknown

Browser `fetch`/XHR is subject to CORS. Each provider needs to be checked:

| Provider | Endpoint | CORS (best guess, verify before building) |
|---|---|---|
| Lichess | `lichess.org/api/user/{id}` | Public API, commonly consumed client-side — likely fine |
| Chess.com | `api.chess.com/pub/player/{id}/stats` | Public API, commonly consumed client-side — likely fine |
| USCF | `ratings-api.uschess.org/...` | Internal-looking API, not designed for browser callers — likely **blocked** |
| FIDE | `ratings.fide.com/profile/{id}` | Plain HTML page, not an API — almost certainly **blocked**, and scraping HTML from a browser context is fragile anyway |

**Action:** verify all four with a quick `fetch()` from a browser devtools
console before writing any Pyodide code. For any that fail, the only fix is
a small CORS-forwarding proxy (e.g. a one-file Cloudflare Worker) that
fetches server-side and adds `Access-Control-Allow-Origin`. That proxy is
infra, not Python, and out of scope for the `rating` package's own tests.

To support routing through a proxy only in the web build, the provider
adapters need their base URL to be overridable instead of hard-coded:

```python
class USCF(RatingPort):
    def __init__(self, player, http_client=None, base_url="https://ratings-api.uschess.org"):
        ...
```

Same treatment for `FIDE.get_url()` and its base URL. Lichess/Chess.com can
get the same parameter for consistency even if they end up unused. This is
a small, desktop-testable change — normal pytest coverage applies.

### 2. `requests` doesn't work under Pyodide

`requests` needs real sockets, which Pyodide doesn't have. Two options:

- **`pyodide-http`** — a patch package that makes `requests`/`urllib`
  transparently use browser `fetch`/`XMLHttpRequest`. Synchronous XHR only
  works off the main thread, so the app needs to run **inside a Web
  Worker**. This is the path of least resistance: `RequestsHttpAdapter`
  keeps working almost unmodified, so no new `HttpPort` implementation is
  strictly required.
- **A native `HttpPort` adapter using `pyodide.http.pyfetch`** — async,
  works on the main thread, but forces `HttpPort.get()` and everything above
  it (`RatingPort.fetch()`, the composition root) to become `async`. Bigger
  ripple, not worth it unless the worker approach hits a wall.

**Recommendation:** run the Pyodide runtime in a Web Worker and use
`pyodide-http` so the existing synchronous `HttpPort`/`RatingPort` contracts
are untouched. Only fall back to an async `HttpPort` adapter if the worker
approach proves unworkable in practice.

### 3. No filesystem / config directory for `ConfigLoader`

`platformdirs.user_config_dir()` + a `.env` file doesn't map onto a browser.
Rather than porting `ConfigLoader` to browser storage, the web front end
should just not use it: the HTML form collects provider + player id
directly from the user (with browser `localStorage` handling "remember my
last player id" if wanted, entirely in JS). `ConfigLoader` stays CLI-only —
no Python-side change needed.

### 4. `sqlite3` file persistence

Pyodide ships `sqlite3` in the stdlib and it works out of the box, but the
default filesystem (`MEMFS`) is wiped on every page reload. To persist
`ratings.db` across sessions:

1. Mount an `IDBFS` directory before running any Python that touches the
   database (JS side, once per page load):
   ```js
   pyodide.FS.mkdir('/ratings');
   pyodide.FS.mount(pyodide.FS.filesystems.IDBFS, {}, '/ratings');
   await new Promise(r => pyodide.FS.syncfs(true, r)); // pull from IndexedDB
   ```
2. Point `SQLiteProfileLogAdapter(database_path=...)` at a path under
   `/ratings` for the web build (the constructor already accepts an
   explicit path — no code change needed there).
3. After each write, flush back to IndexedDB from JS:
   ```js
   await new Promise(r => pyodide.FS.syncfs(false, r));
   ```

This is entirely a driving-adapter (JS) responsibility; `SQLiteProfileLogAdapter`
itself is already storage-path-agnostic and needs no change.

If this turns out to be more trouble than it's worth for a v1, logging can
simply be skipped in the web build (call `app.fetch()` without
`log_profile()`) and revisited later.

### 5. Composition root is CLI-shaped

`main()` in `rating/application/rating.py` mixes `argv` parsing, `print`,
and orchestration together. The web front end needs the orchestration
(pick adapter → fetch → log → normalize) without the `argparse`/`print`
parts. Extract that middle step into a small, desktop-testable function:

```python
def fetch_rating(provider: str, player: str, http_client: HttpPort,
                  profile_log: Optional[ProfileLogPort] = None) -> NormalizedRatingProfile | None:
    """Look up one player's rating and log it. Raises AmbiguousUSCFPlayerError as today."""
```

`main()` calls this instead of duplicating the branch-and-fetch logic
inline; the future Pyodide entry point calls the same function and turns
the result into JSON via `profile.to_dict()`, which already exists. This
keeps behavior identical between CLI and browser and is covered by the
existing `tests/test_rating_application.py` pattern — no special web test
needed.

### 6. Dependency footprint

- `beautifulsoup4` — available as a prebuilt Pyodide package; load with
  `pyodide.loadPackage` or `micropip.install`. No change needed.
- `numpy` — declared in `pyproject.toml` but **not imported anywhere** in
  `rating/`. Drop it from `dependencies` regardless of the web work; it's
  currently dead weight and would otherwise pull in a large wasm package for
  nothing.
- `python-dotenv` / `platformdirs` — only used by `ConfigLoader`, which per
  §3 stays CLI-only. Not needed in the web build's dependency set (they can
  stay in `pyproject.toml`; the web build simply doesn't install them).
- `requests` — replaced at runtime by `pyodide-http`'s patched version
  inside the worker (§2); no source change.

### 7. Packaging and hosting

- Build a wheel of the existing package: `python -m build --wheel` (already
  pure Python, no compiled extensions).
- Serve the wheel as a static asset alongside the page; in the worker,
  `micropip.install("/dist/chess_rating-<version>-py3-none-any.whl")` plus
  `micropip.install(["beautifulsoup4"])`.
- The whole thing is static files (HTML/JS/wasm/wheel) plus, if §1 requires
  it, one small CORS-proxy endpoint for USCF/FIDE. No Python server
  component. Can be hosted on GitHub Pages / Cloudflare Pages.

## New/changed pieces, by side of the hexagon

- **Driving adapter (new, JS/HTML, no tests):** `web/index.html`,
  `web/worker.js` — loads Pyodide + `pyodide-http` + the wheel, mounts
  IDBFS, wires a form to `fetch_rating()`, renders `profile.to_dict()` as
  JSON, and catches `AmbiguousUSCFPlayerError` to show the candidate list
  (mirrors what `main()` already does for the CLI).
- **Application layer (existing package, gets normal pytest coverage):**
  extract `fetch_rating()` per §5; add overridable `base_url` params to the
  USCF/FIDE adapters per §1.
- **Driven adapter (existing, unmodified or lightly configured):**
  `RequestsHttpAdapter` continues to be used as-is inside the worker thanks
  to `pyodide-http`'s monkeypatch; `SQLiteProfileLogAdapter` continues to be
  used as-is with a different `database_path`.
- **Not ported:** `ConfigLoader` (§3) and `rating config` subcommand — CLI-only.

## Suggested build order

1. Extract `fetch_rating()` and add the `base_url` params (§1, §5) — pure
   desktop change, covered by existing pytest patterns, ships independently
   of any browser work.
2. Verify CORS for all four providers from a browser console. This decides
   whether a proxy is needed at all before more work is done.
3. Stand up the minimal Pyodide worker harness locally (`python -m
   http.server` + Pyodide from CDN) and confirm Lichess/Chess.com lookups
   work end-to-end through `pyodide-http`.
4. If needed, stand up the CORS proxy for USCF/FIDE and point the web
   build's `base_url` at it.
5. Add IDBFS-backed SQLite persistence (§4) — optional, can ship without it
   first.
6. Package and host the static site.
