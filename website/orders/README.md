# `orders/` &mdash; ordering, shifts, products

This is the heart of TOSTI. Bakers run shifts; users place orders during those shifts; the system tracks who paid, what's ready, and who got blacklisted for not picking things up.

It's the biggest app in the project. Treat changes here as production-affecting &mdash; the canteens use this live, daily.

## Data model

```mermaid
classDiagram
    direction LR
    OrderVenue --> Venue : OneToOne
    OrderVenue "1" <--> "0..*" Product : available_at (M2M)
    Shift --> OrderVenue : venue
    Shift "1" <--> "0..*" User : assignees (M2M)
    Order --> Shift
    Order --> Product
    Order --> User : user
    Order --> Association : user_association
    OrderBlacklistedUser --> User : OneToOne
```

- **`OrderVenue`** &mdash; OneToOne wrapper around `venues.Venue`. Holds ordering-specific config (whether ordering is enabled, scanner settings, etc.). `Product.available_at` is the M2M that pins each product to one or more venues.
- **`Product`** &mdash; the catalogue item: `name`, `icon`, `current_price`, `available`, `orderable`, `ignore_shift_restrictions`, and `barcode` (for the scanner flow).
- **`Shift`** &mdash; a time window (`start`, `end`) during which a baker accepts orders. `can_order` is the operator-toggleable "currently taking orders" flag; `finalized` permanently locks the shift once it's closed. Bakers are tracked through the `assignees` M2M to `User`.
- **`Order`** &mdash; ties a `user` (and their `user_association`) to a `product` within a `shift`. Lifecycle is tracked by three boolean+timestamp pairs: `ready` / `ready_at`, `paid` / `paid_at`, `picked_up` / `picked_up_at`. `type` distinguishes a normal counter order from a scanned (pre-packaged) one; `prioritize` / `deprioritize` lets bakers reorder the queue.
- **`OrderBlacklistedUser`** &mdash; OneToOne flag with an `explanation` field. Blacklisted users can't place new orders.

## Where the logic lives

- **`services.py`** &mdash; `add_user_order`, `list_active_shifts`. Permission checks, capacity checks, blacklist checks all happen here. View and MCP tool both call into the same service.
- **`models.py`** &mdash; the data and its invariants. `Shift.is_active`, `Shift.number_of_orders` are regular `@property`s; they hit the database on access, so when you need them in bulk for a queryset, annotate explicitly rather than looping.
- **`mcp.py`** &mdash; `list_active_shifts` (read), `place_order` (scope-gated by `orders:order`).
- **`api/v1/`** &mdash; the REST endpoints powering the baker view's live queue, the user order page, the scanner.

## Polling

The baker view, the user order list, and the scanner all poll every few seconds. **Anything you add to the order-list endpoints needs to be cheap at scale.** Use `select_related` / `prefetch_related`, lean on queryable properties, and count queries with `django.db.connection.queries` if in doubt. There's a section on this in [`CONTRIBUTING.md`](../../CONTRIBUTING.md#performance-and-database-queries).

## The scanner

`/orders/<shift>/admin/scanner/` is the barcode-scanner flow for selling pre-packaged products at the counter (cans, snacks). Camera capture lives in `static/orders/js/admin-scanner.js`; the API endpoint is `PlayerTrackAddAPIView`-style POST that resolves the barcode → product → order. Scanned orders are marked with a "scanned" user-icon (`<i class="fa-solid fa-desktop">`) instead of a real user.

## Deposit transactions

Deposit cans are processed at the counter through the `transactions/` app, not this one. See the *Process deposit* explainer tab for the baker flow.

## Explainers

This app contributes the *Order*, *Manage a shift*, *Hand in deposit*, and *Process deposit* tabs to `/explainers/`. See `apps.py:OrdersConfig.explainer_tabs` for the registration and `templates/orders/explainer*.html` for the content.

## Gotchas

- **Two shifts in one venue at the same time is forbidden.** The constraint is in the model `clean`; rely on it rather than re-checking in views.
- **Finalizing a shift is permanent.** Once `finalized=True`, the shift is locked. There's no admin path to un-finalize without writing SQL by hand.
- **Don't roll your own "is the shift active" check.** Use `Shift.is_active` &mdash; it accounts for start, end, finalised, and the operator-flipped accepting-orders flag.
</content>
</invoke>