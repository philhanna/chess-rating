# Ports And Adapters

This project uses a lightweight ports-and-adapters structure.

The main idea is:

- ports define the interfaces the application depends on
- adapters provide concrete implementations of those interfaces
- the CLI entry point wires the concrete pieces together

## Where The Wiring Happens

The composition root is [`rating/application/rating.py`](/home/saspeh/dev/python/chess-rating/rating/application/rating.py).

That is where the application:

- loads configuration with `ConfigLoader`
- creates the concrete HTTP adapter with `RequestsHttpAdapter()`
- selects one concrete rating adapter: `USCF`, `Lichess`, `ChessCom`, or `FIDE`
- injects the HTTP adapter into the selected rating adapter
- calls `fetch()` on the selected adapter

In other words, the actual wiring of ports to adapters is done in the CLI layer, not inside the ports themselves.

## Dependency Diagram

```text
python -m rating
    |
    v
rating/application/rating.py
    |
    +-- ConfigLoader
    |
    +-- RequestsHttpAdapter --------------------+
    |                                           |
    +-- USCF(player, http_client)               |
    +-- Lichess(player, http_client)            |
    +-- ChessCom(player, http_client)           |
    +-- FIDE(player, http_client)               |
                                                |
HttpPort <--------------------------------------+
    ^
    |
RequestsHttpAdapter

RatingPort
    ^
    +-- USCF
    +-- Lichess
    +-- ChessCom
    +-- FIDE
```

## Ports

The abstract ports live in [`rating/ports/`](/home/saspeh/dev/python/chess-rating/rating/ports).

### `HttpPort`

Defined in [`rating/ports/http_port.py`](/home/saspeh/dev/python/chess-rating/rating/ports/http_port.py).

Purpose:
Represents the ability to make an HTTP GET request and return response text.

Method:

- `get(url: str) -> str`

Why it exists:
The rating adapters should not depend directly on the `requests` library. They depend on the abstract HTTP capability instead.

### `RatingPort`

Defined in [`rating/ports/rating_port.py`](/home/saspeh/dev/python/chess-rating/rating/ports/rating_port.py).

Purpose:
Represents the ability to fetch rating data for a configured player.

Method:

- `fetch() -> str`

Why it exists:
The CLI can treat all rating providers uniformly once each provider implements the same interface.

## Adapters

The concrete adapters live in [`rating/adapters/`](/home/saspeh/dev/python/chess-rating/rating/adapters).

### HTTP adapter

[`rating/adapters/requests_http.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/requests_http.py)

- `RequestsHttpAdapter` implements `HttpPort`
- uses the `requests` library to perform real network calls
- is an infrastructure adapter

### Rating adapters

These all implement `RatingPort` and all depend on an injected `HttpPort`.

[`rating/adapters/uscf.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/uscf.py)

- builds the USCF API URL
- fetches JSON through `HttpPort`
- parses the response into the project's pipe-delimited output format

[`rating/adapters/lichess.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/lichess.py)

- builds the Lichess API URL
- fetches JSON through `HttpPort`
- extracts the rating categories with games played

[`rating/adapters/chesscom.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/chesscom.py)

- builds the Chess.com stats URL
- fetches JSON through `HttpPort`
- extracts the supported chess rating categories

[`rating/adapters/fide.py`](/home/saspeh/dev/python/chess-rating/rating/adapters/fide.py)

- builds the FIDE profile URL
- fetches HTML through `HttpPort`
- parses the profile page with BeautifulSoup

## How Injection Works

Each rating adapter accepts an HTTP dependency in its constructor.

Conceptually, the pattern looks like this:

```python
http_client = RequestsHttpAdapter()
app = USCF(player, http_client)
output = app.fetch()
```

That means:

- the CLI decides which concrete implementations to use
- the adapters themselves do not create their own HTTP client
- tests can replace the real HTTP adapter with a mock or fake implementation

## Why This Structure Helps

- It isolates HTTP access behind `HttpPort`.
- It keeps each provider-specific parser in its own adapter.
- It makes tests simpler because adapters can receive mocked HTTP dependencies.
- It keeps the composition logic in one place: [`rating/application/rating.py`](/home/saspeh/dev/python/chess-rating/rating/application/rating.py).

## Short Summary

If you want to know where ports and adapters are actually connected together, look at [`rating/application/rating.py`](/home/saspeh/dev/python/chess-rating/rating/application/rating.py).

That file is the application's composition root.
