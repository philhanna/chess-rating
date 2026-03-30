# USCF Sections Schema

This document describes the inferred schema of the sample USCF sections payload
stored in [tests/testdata/sections.json](/home/saspeh/dev/python/chess-rating/tests/testdata/sections.json).

The payload appears to be a paginated response where each item represents one
event section played by a member, along with one or more rating updates derived
from that section.

## Top-Level Shape

```json
{
  "offset": 0,
  "pageSize": 100,
  "hasPreviousPage": false,
  "hasNextPage": false,
  "items": []
}
```

Observed top-level fields:

- `offset`: integer pagination offset
- `pageSize`: integer page size
- `hasPreviousPage`: boolean
- `hasNextPage`: boolean
- `items`: array of section entries

## Section Entry

Each entry in `items` has this inferred shape:

```json
{
  "id": "string",
  "sectionNumber": 1,
  "sectionName": "string",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "format": "Swiss",
  "ratingSystem": "R",
  "ratingRecords": [],
  "event": {}
}
```

Observed fields:

- `id`: opaque section identifier
- `sectionNumber`: integer section number within the event
- `sectionName`: human-readable section name
- `startDate`: section start date
- `endDate`: section end date
- `format`: observed values include `Swiss` and `RoundRobin`
- `ratingSystem`: observed values include `R` and `D`
- `ratingRecords`: list of rating updates associated with this section
- `event`: nested event summary

## Rating Record

Each section contains one or more rating records:

```json
{
  "eventId": "string",
  "sectionNumber": 1,
  "preRating": 1227,
  "preRatingDecimal": 1227.41,
  "postRating": 1260,
  "postRatingDecimal": 1260.03,
  "ratingSource": "R"
}
```

Observed fields:

- `eventId`: opaque event identifier
- `sectionNumber`: integer section number, matching the parent section
- `preRating`: published rating before the event
- `preRatingDecimal`: higher-precision pre-event value
- `postRating`: published rating after the event
- `postRatingDecimal`: higher-precision post-event value
- `ratingSource`: observed values include `R` and `Q`

## Event Summary

Each section entry includes nested event metadata:

```json
{
  "id": "string",
  "name": "string",
  "startDate": "YYYY-MM-DD",
  "endDate": "YYYY-MM-DD",
  "stateCode": "NC"
}
```

Observed fields:

- `id`: event identifier
- `name`: human-readable event name
- `startDate`: event start date
- `endDate`: event end date
- `stateCode`: two-letter state or jurisdiction code

Observed values in the sample include `DC`, `NC`, `PA`, and `VA`.

## Python TypedDict Sketch

```python
from typing import Literal, TypedDict


class EventSummary(TypedDict):
    id: str
    name: str
    startDate: str
    endDate: str
    stateCode: str


class RatingRecord(TypedDict):
    eventId: str
    sectionNumber: int
    preRating: int
    preRatingDecimal: float
    postRating: int
    postRatingDecimal: float
    ratingSource: Literal["R", "Q"]


class SectionItem(TypedDict):
    id: str
    sectionNumber: int
    sectionName: str
    startDate: str
    endDate: str
    format: Literal["Swiss", "RoundRobin"]
    ratingSystem: Literal["R", "D"]
    ratingRecords: list[RatingRecord]
    event: EventSummary


class SectionsResponse(TypedDict):
    offset: int
    pageSize: int
    hasPreviousPage: bool
    hasNextPage: bool
    items: list[SectionItem]
```

## Notes

- The current USCF adapter only uses the first section item's `endDate` and the
  first rating record's `postRating`.
- The sample data suggests the payload is significantly richer than the current
  adapter contract exposes.
- Most section dates match the nested event dates, but not every item appears to
  do so exactly, so the two date ranges should not be assumed identical without
  validation.
