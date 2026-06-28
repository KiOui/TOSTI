# `venues/` &mdash; venues + reservations + calendar

A "venue" in TOSTI is a physical room or area (canteen, meeting room, brew room, etc.) that can host shifts, host music players, be reserved, or all three. This app owns the venue catalogue and the reservation system; other apps (`orders`, `thaliedje`, `borrel`) hang their own concerns off the `Venue` model.

## Data model

```mermaid
classDiagram
    direction LR
    Venue --> "0..*" Reservation
    Reservation --> User : created by
    Reservation --> "0..1" User : accepted by
```

- **`Venue`** &mdash; name, slug, opening hours, can-it-be-reserved flag, color shown in the calendar.
- **`Reservation`** &mdash; user-created request to use a venue for some time window. Has a title, optional comments, an `accepted` flag (false by default; a manager flips it true), start and end times.

Other apps refer to `Venue` as a foreign key (`orders.OrderVenue.venue`, `thaliedje.Player.venue`, etc.) but they don't extend the venue itself. If you need venue-related config for your app, follow that pattern.

## The calendar

`/venues/calendar/` shows a FullCalendar view of all reservations across all reservable venues. Each reservation is colour-coded by its venue. iCal feeds are exposed via `django-ical` so anyone can subscribe to a venue's reservations in their own calendar app.

## Approval workflow

New reservations are created with `accepted=False`. The user gets an email confirming the request was received; a notification email goes to the venue manager. The manager reviews and either accepts (flips the flag, optional email back to the user) or rejects (deletes / leaves unaccepted, depending on convention).

There's an `automatically_accept_first_reservation` venue-level flag that lets specific venues short-circuit this for the first booking. Use carefully.

## Services

`services.py:create_reservation` is the canonical reservation-creation path:

- Checks the venue accepts reservations (`venue.can_be_reserved`).
- Checks `end > start`.
- Runs model `full_clean()` (catches collisions and other model-level invariants).
- Calls `send_reservation_request_email`.

The MCP `create_venue_reservation` tool and any future REST creation endpoint should both go through this service rather than re-implementing the validation. The `venues:write` scope gates the MCP path.

## Gotchas

- **`Venue.objects.all()` includes inactive venues.** Use the queryset manager methods to filter active-only if that's what you want.
- **Reservations don't lock out other reservations on save** &mdash; collision detection happens in `full_clean`. If you create a reservation without `full_clean`, you can double-book a venue.
- **The `slug` is the public identifier**, not the pk. URL converters and the MCP tool both resolve by slug.
</content>
</invoke>