# Project intake
Drop one JSON file per app idea here. LifeOS generates a build brief and task checklist under `state/projects/<project-id>/`.

```json
{
  "name": "Local Worker Discovery",
  "idea": "Help customers discover and contact local workers.",
  "target_users": "Local customers and workers",
  "platform": "Mobile-first web app / PWA",
  "build_tool": "Claude + GitHub",
  "repository": "balaadithya123/App_1",
  "published_url": "",
  "features": ["Worker profiles", "Availability", "Direct contact"],
  "success_metrics": ["Successful worker contacts", "Low error rate"],
  "constraints": ["Free-tier infrastructure", "Mobile-first"]
}
```

Required: `name`, `idea`. Actual building and publishing remain manual gates.
