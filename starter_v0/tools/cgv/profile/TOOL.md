---
name: cgv_profile
track: bonus
kind: live_api
provider: CGV Cinema mobile API (unofficial)
requires_env: []
inputs: []
outputs: [profile]
side_effect: false
---
# cgv_profile

`GET /en/api/customer/profile/id/{id}` with the `U-Token` header. Ported from
`get_profile`.

The current web request's server-side `CgvSession` supplies the customer ID and
token. The agent calls `cgv_profile()` with no arguments and cannot access or
provide either secret.

CGV has no response model for this endpoint, so the payload is passed through as
a dict — except that access tokens and session ids are stripped and phone / email
/ card numbers are masked before the model sees them.
