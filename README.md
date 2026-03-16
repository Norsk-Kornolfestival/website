# Norsk Kornølfestival Website

Website for [Norsk Kornølfestival](https://norskkornolfestival.no/) — the only festival dedicated to traditional Norwegian farmhouse brewing. Built with [Hugo](https://gohugo.io/).

## Updating content

The easiest way to update the website is through **GitHub Issues**. The repo has issue templates for common tasks — fill one out and use Claude Code with the `/update-website` skill to turn it into a PR.

### Issue types

| Template | Label | What it does |
|----------|-------|--------------|
| **News** | `news` | Creates a bilingual news post (nb + en) |
| **Sponsor** | `sponsor` | Adds/updates a sponsor in `data/sponsors.yaml` + optional news post |
| **Brewery** | `brewery` | Adds/updates a brewery in `data/breweries.yaml` + optional news post |
| **Website update** | `website-update` | Edits an existing page (homepage, program, practical info, etc.) |

### Workflow

1. Create an issue using one of the templates on GitHub
2. Run `/update-website #<issue-number>` in Claude Code
3. Claude reads the issue, creates the files, and opens a PR
4. Merge the PR — the site deploys automatically

## Deployment

Deployment is fully automated via GitHub Actions. Every push to `main` builds the site with Hugo and deploys to GitHub Pages. No manual steps required.

The workflow also supports manual re-deploys via `workflow_dispatch` if needed (Actions tab → "Build and deploy" → "Run workflow").

## Project structure

```
content/
  nb/          Norwegian content (served at /)
  en/          English content (served at /en/)
data/
  breweries.yaml
  sponsors.yaml
  schedule.yaml
  ...
layouts/
  index.html       Homepage
  _default/        Default list/single templates
  breweries/       Brewery page template (card grid with logos)
  news/            News list template (nb)
  nyheter/         News list template (en)
static/
  css/main.css
  images/          Logos, photos, etc.
hugo.toml          Site config (languages, menus, params)
```

## Local development

```sh
hugo server
```

The site is bilingual — Norwegian (nb) is the default language at the root, English is at `/en/`. Content for each language lives in `content/nb/` and `content/en/`.

Structured data (breweries, sponsors, schedule, etc.) lives in `data/*.yaml` and is rendered by templates, so update the YAML files rather than the markdown when changing those.
