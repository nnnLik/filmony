# Progress — profile-rating-contrast-stats

Status: **completed** (2026-08-15T010600Z)

- Shipped rating contrast computation and stats API field.
- UI section on Statistics → Overview; insight grid items when data present.
- Fixed schema mismatch that hid the block entirely (commit `c191d42`).
- Added empty state when `compared_count === 0`.
- Verification: unit + integration pytest, frontend lint/build OK.
