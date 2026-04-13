# Ports And Adapters

This project uses a small hexagonal architecture: the core application depends
on abstract ports, while concrete adapters handle HTTP, third-party APIs, and
HTML scraping.

The current flow is:

1. the CLI parses arguments and loads default player ids from config
2. the composition root creates the concrete HTTP adapter
3. the composition root selects one concrete rating adapter
4. the rating adapter fetches provider data through `HttpPort`
5. the rating adapter maps provider-specific data into a shared domain model
6. the CLI formats that normalized model as pipe-delimited text or JSON

## Composition Root

The composition root is [`rating/application/rating.py`](/home/saspeh/dev/python/chess-rating/rating/application/rating.py).

That module is responsible for wiring the system together:

- builds the CLI with `argparse`
- loads configuration through `ConfigLoader`
- creates `RequestsHttpAdapter()`
- chooses one `RatingPort` implementation: `USCF`, `Lichess`, `ChessCom`, or `FIDE`
- injects the shared HTTP dependency into that adapter
- calls `fetch()` to obtain a `NormalizedRatingProfile`
- renders the result as JSON or the project's plain-text output format

It also handles the `rating config` subcommand, which prints the active config
file path and contents.

## Dependency Picture

```text
python -m rating
    |
    v
rating/application/rating.py
    |
    +-- ConfigLoader
    +-- RequestsHttpAdapter --------------------------+
    |                                                 |
    +-- USCF(player, http_client)                     |
    +-- Lichess(player, http_client)                  |
    +-- ChessCom(player, http_client)                 |
    +-- FIDE(player, http_client)                     |
                                                      |
HttpPort <--------------------------------------------+
    ^
    |
RequestsHttpAdapter

RatingPort
    ^
    +-- USCF
    +-- Lichess
    +-- ChessCom
    +-- FIDE
        |
        v
NormalizedRatingProfile
    |
    +-- PlayerIdentity
    +-- ratings
    +-- extras
    +-- RatingMetadata
```

## Ports

The abstract ports live in [`rating/ports/`](/home/saspeh/dev/python/chess-rating/rating/ports).

### `HttpPort`

Defined in [`rating/ports/http_port.py`](/home/saspeh/dev/python/chess-rating/rating/ports/http_port.py).

Purpose:
Represents the application's outbound HTTP capability.

Method:

- `get(url: str) -> str | None`

Why it exists:
The provider adapters should not depend directly on `requests`. They only need
the ability to fetch a URL and receive response text.

### `RatingPort`

Defined in [`rating/ports/rating_port.py`](/home/saspeh/dev/python/chess-rating/rating/ports/rating_port.py).

Purpose:
Represents the ability to fetch rating data for one configured player and
return it in the application's normalized form.

Method:

- `fetch() -> NormalizedRatingProfile | None`

Why it exists:
The CLI can work with every provider through one shared interface even though
each provider has a different endpoint and response format.

## Domain Model

The shared provider-independent model lives in
[`rating/domain/models.py`](/home/saspeh/dev/python/chess-rating/rating/domain/models.py).

This is an important part of the architecture because the adapters no longer
return provider-specific strings directly. They return a normalized object:

- `NormalizedRatingProfile` is the main result returned by every `RatingPort`
- `PlayerIdentity` captures the provider id and optional display name
- `ratings` stores canonical categories such as `standard`, `rapid`, `blitz`,
  `bullet`, and `correspondence`
- `extras` stores provider-specific categories that do not fit the canonical set
- `RatingMetadata` carries supporting fields such as `as_of` and `source_url`

The CLI formatting functions in
[`rating/application/rating.py`](/home/saspeh/dev/python/chess-rating/rating/application/rating.py)
convert that normalized model into either JSON or the pipe-delimited text
output shown to users.

## Adapters

The concrete adapters live in [`rating/adapters/`](/home/saspeh/dev/python/chess-rating/rating/adapters).

### HTTP adapter

[`rating/adapters/requests_http.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/requests_http.py)

- `RequestsHttpAdapter` implements `HttpPort`
- uses the `requests` library for real network calls
- translates `requests` exceptions into stderr output plus `None`
- keeps transport details out of the rating adapters

### Rating adapters

Each provider adapter implements `RatingPort` and depends on an injected
`HttpPort`.

[`rating/adapters/uscf.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/uscf.py)

- builds the USCF sections endpoint
- fetches JSON through `HttpPort`
- selects the newest section entry
- maps the latest post-rating into `NormalizedRatingProfile`

[`rating/adapters/lichess.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/lichess.py)

- builds the Lichess user endpoint
- fetches JSON through `HttpPort`
- filters to categories with games played
- maps canonical and extra ratings into `NormalizedRatingProfile`

[`rating/adapters/chesscom.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/chesscom.py)

- builds the Chess.com stats endpoint
- fetches JSON through `HttpPort`
- extracts `chess_*` rating sections
- maps canonical and extra ratings into `NormalizedRatingProfile`

[`rating/adapters/fide.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/fide.py)

- builds the FIDE profile URL
- fetches HTML through `HttpPort`
- scrapes the page with BeautifulSoup
- maps visible rating cards into `NormalizedRatingProfile`

## Config Loading

[`rating/config_loader.py`](/home/saspeh/dev/python/chess-rating/rating/config_loader.py)
is not itself a port, but it is part of the outer application layer.

Its job is to:

- find the platform-specific `config.yaml` location with `platformdirs`
- load YAML configuration for default per-provider users
- expose both the resolved filename and parsed config object to the CLI

This keeps config lookup separate from provider adapters and from the domain
model.

## How Dependency Injection Works

Each rating adapter receives its HTTP dependency from the composition root.

```python
http_client = RequestsHttpAdapter()
app = Lichess(player, http_client)
profile = app.fetch()
```

That means:

- the CLI decides which concrete objects to assemble
- adapters do not create their own HTTP client
- tests can replace the real HTTP adapter with a mock or fake
- provider parsing stays isolated from transport concerns

## Why This Structure Helps

- Ports keep the application logic independent from `requests` and from each provider API.
- Adapters isolate provider-specific JSON parsing and HTML scraping.
- The normalized domain model gives the CLI one shared shape to render.
- The composition root keeps wiring in one place instead of scattering it across modules.
- Tests can mock `HttpPort` and exercise parsing logic with canned payloads.

## Short Summary

If you want to see where ports are connected to adapters, start with
[`rating/application/rating.py`](/home/saspeh/dev/python/chess-rating/rating/application/rating.py).

If you want to see what every adapter returns after normalization, look at
[`rating/domain/models.py`](/home/saspeh/dev/python/chess-rating/rating/domain/models.py).
