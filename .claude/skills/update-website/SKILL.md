---
name: update-website
description: >-
  Process GitHub issues to update the Norsk Kornølfestival Hugo website.
  Handles issues labeled "news", "sponsor", "brewery", or "website-update"
  from the Norsk-Kornolfestival/website repo. Creates bilingual content
  (Norwegian + English), downloads attached images, and updates data files.
  Use this skill whenever the user mentions processing issues, updating the
  website from issues, adding a sponsor, adding a brewery, creating news posts
  from GitHub, or anything about the festival website content workflow.
---

# Update Website from GitHub Issues

This skill processes GitHub issues from `Norsk-Kornolfestival/website` and turns them into website content. The festival website is a bilingual Hugo site (Norwegian at root, English at `/en/`).

## How it works

1. Read the GitHub issue (user provides an issue number or URL)
2. Determine the action from the issue's label
3. Parse the structured form fields from the issue body
4. Create/update the appropriate files
5. Translate content to the other language
6. Download any attached images
7. Commit the changes on a branch and offer to create a PR

## Reading an issue

Use `gh issue view <number> --repo Norsk-Kornolfestival/website --json title,body,labels,createdAt,author` to fetch the issue. The body contains structured form responses from our issue templates.

### Parsing form responses

GitHub issue templates render as markdown with `### Field Label` headings followed by the response. Parse them like:

```
### Tittel / Title

Speaker: Jan Steensels

### Språk / Language

English

### Innhold / Content

Jan Steensels from VIB-KU Leuven will present...
```

Extract each field by finding the `### ` headings and taking the text between them.

## Actions by label

### `news` — Create a news post

Create two files with matching filenames:
- `content/nb/nyheter/YYYY-MM-DD-slug.md`
- `content/en/news/YYYY-MM-DD-slug.md`

Use today's date. Generate the slug from the title (lowercase, ASCII, hyphens).

**Front matter:**
```yaml
---
title: "The title"
date: YYYY-MM-DDT00:00:00+01:00
author: "Issue author's GitHub display name"
---
```

The issue's "Språk / Language" field tells you which language the content is in. Write that version directly, then translate for the other language. Keep the tone natural and festival-appropriate — not overly formal.

Preserve all image references and markdown formatting from the issue body.

### `sponsor` — Add/update sponsor + optional news post

1. **Update `data/sponsors.yaml`** — add a new entry or update an existing one:
   ```yaml
   - name: Sponsor Name
     url: https://...
     description:
       nb: Norwegian description
       en: English description
     logo: images/sponsors/slug.png
   ```

2. **Download the logo** — if the issue has an attached image, download it to `static/images/sponsors/`. If not, use a placeholder path and note it in the PR.

3. **Create news post** — if the "Nyhetsartikkel" field has content, create bilingual news posts (same as the `news` action). If it's empty, skip the news post.

### `brewery` — Add/update brewery + optional news post

1. **Update `data/breweries.yaml`**:
   ```yaml
   - name: Brewery Name
     location:
       nb: Norwegian location
       en: English location
     url: https://...
     description:
       nb: Norwegian description
       en: English description
     logo: images/breweries/slug.png
   ```

2. **Download images** from the issue into `static/images/breweries/`.

3. **Create news post** if the "Nyhetsartikkel" field has content.

Also add a section to `content/nb/bryggerier/_index.md` and `content/en/breweries/_index.md` for the new brewery.

### `website-update` — Edit existing content

The issue describes a change to an existing page. Read the "Hvilken side?" field to know which page, then apply the described change to both the Norwegian and English versions.

Page mapping:
| Form value | NB file | EN file |
|---|---|---|
| Forside / Homepage | `content/nb/_index.md` | `content/en/_index.md` |
| Program | `content/nb/program/_index.md` | `content/en/program/_index.md` |
| Bryggerier / Breweries | `content/nb/bryggerier/_index.md` | `content/en/breweries/_index.md` |
| Frivillige / Volunteers | `content/nb/frivillige/_index.md` | `content/en/volunteers/_index.md` |
| Praktisk / Practical info | `content/nb/praktisk/_index.md` | `content/en/practical/_index.md` |
| Billetter / Tickets | `content/nb/billetter/_index.md` | `content/en/tickets/_index.md` |
| Hjemmebryggere / Home brewers | `content/nb/hjemmebryggere/_index.md` | `content/en/homebrewers/_index.md` |

For "Annet / Other", read the description to figure out what needs changing.

## Downloading images from issues

GitHub-hosted images in issue bodies look like:
```
![image](https://github.com/user-attachments/assets/abc123...)
```

Download them with `curl -fL -o <local-path> <url>`. Name them based on context (e.g., `sponsor-name.png`, `brewery-name.jpg`).

## Translation

When translating between Norwegian and English:
- Keep proper nouns as-is (place names, person names, beer/brewery names)
- Keep the tone natural and casual — this is a festival website
- Norwegian variety is bokmål (nb), not nynorsk
- Keep all image paths, links, and markdown formatting identical

## Git workflow

After making changes:
1. Create a branch: `git checkout -b issue-<number>-<short-description>`
2. Stage and commit the changes
3. Push and create a PR that references the issue: `Closes #<number>`
4. Tell the user the PR URL

If the user prefers to commit directly to main, do that instead — but ask first.

## Multiple issues

If the user asks to "process all open issues" or similar, use `gh issue list --repo Norsk-Kornolfestival/website --label <label> --state open` to find them, then process each one. Create a separate branch/PR per issue to keep changes reviewable.

## Reference

For details on the Hugo site structure, data file formats, and content organization, read `references/site-structure.md` in this skill's directory.
