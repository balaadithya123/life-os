# Production observations
Add JSON files for errors, deployment regressions, uptime failures, performance alerts or maintenance findings. Use a stable `category`; never include secrets or sensitive logs.

```json
[
  {"project":"my-app","category":"deployment-health","title":"Health check returned HTTP 503","severity":"high","source":"uptime monitor"}
]
```
The pipeline reports evidence-based recommendations; it does not merge or deploy fixes.
