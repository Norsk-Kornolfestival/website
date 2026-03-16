# Norsk Kornølfestival — Site Structure Reference

## Overview

Hugo site, bilingual: Norwegian (nb) at root, English (en) at `/en/`.
Config: `hugo.toml`. Default language: `nb`.

## Content directories

```
content/
├── nb/                          # Norwegian (default)
│   ├── _index.md                # Homepage
│   ├── program/_index.md
│   ├── bryggerier/_index.md     # Breweries
│   ├── frivillige/_index.md     # Volunteers
│   ├── praktisk/_index.md       # Practical info
│   ├── billetter/_index.md      # Tickets
│   ├── hjemmebryggere/_index.md # Home brewers
│   └── nyheter/                 # News
│       ├── _index.md
│       └── YYYY-MM-DD-slug.md   # Individual posts
└── en/                          # English
    ├── _index.md
    ├── program/_index.md
    ├── breweries/_index.md
    ├── volunteers/_index.md
    ├── practical/_index.md
    ├── tickets/_index.md
    ├── homebrewers/_index.md
    └── news/
        ├── _index.md
        └── YYYY-MM-DD-slug.md   # Same filenames as nb
```

## Data files

All in `data/`, YAML format with bilingual fields:

### sponsors.yaml
```yaml
- name: Sponsor Name
  url: https://...
  description:
    nb: Norwegian description
    en: English description
  logo: images/sponsors/filename.png  # relative to static/
```

### breweries.yaml
```yaml
- name: Brewery Name
  location:
    nb: Norwegian location
    en: English location
  url: https://...
  description:
    nb: Norwegian description
    en: English description
  logo: images/breweries/filename.png
```

### Other data files
- `festival.yaml` — dates, venue, board members
- `schedule.yaml` — bilingual program/schedule
- `tickets.yaml` — ticket types and pricing
- `accommodation.yaml` — lodging options

## Static files

```
static/
├── css/main.css
├── images/
│   ├── hero/          # Site header images
│   ├── sponsors/      # Sponsor logos
│   ├── breweries/     # Brewery logos/photos
│   ├── festival/      # Festival photos
│   └── wp/            # Migrated WordPress uploads
└── files/
    └── wp/            # Migrated PDFs
```

## News post format

```markdown
---
title: "Post title"
date: YYYY-MM-DDT00:00:00+01:00
author: "Author Name"
---

Post content in markdown.

![alt text](/images/path/to/image.jpg)
```

NB and EN posts use identical filenames for Hugo's translation linking.
Image paths start with `/` — Hugo's render hooks handle the base path.

## Slug generation

From title: lowercase, replace æ→ae ø→o å→a, replace non-alphanumeric with hyphens, trim.
Prefix with date: `2026-03-16-the-slug.md`
