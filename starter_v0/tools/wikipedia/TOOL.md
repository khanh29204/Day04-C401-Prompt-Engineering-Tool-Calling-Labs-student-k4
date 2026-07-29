---
name: wikipedia
track: bonus
kind: live_api
provider: Wikipedia (MediaWiki Action API)
requires_env: []
inputs: [query, language, max_results]
outputs: [items, language]
side_effect: false
---
# wikipedia

Searches Wikipedia for `query` and returns article summaries. No API key
required.

`language` accepts `"vi"`, `"en"`, or `"auto"` (default). In `auto` mode the
tool searches Vietnamese Wikipedia first and only falls back to English
Wikipedia if the Vietnamese search returns no results.
