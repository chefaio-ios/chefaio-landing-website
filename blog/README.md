# Rivex blog — Tech Writer guide

The marketing blog lives at **https://rivexapp.com/blog/** and is built with [Jekyll](https://jekyllrb.com/) on GitHub Pages.

## Add a new post

1. Create a Markdown file in **`_posts/`** at the repo root.
2. Name it `YYYY-MM-DD-your-slug.md` (date + slug). The slug becomes part of the URL.
3. Add required front matter (YAML between `---` lines) at the top of the file.
4. Write the body in Markdown below the front matter.
5. Preview locally with `mise run jekyll-serve`, then open a PR.

Published URLs follow:

`/blog/YYYY/MM/DD/your-slug/`

Example: `_posts/2025-10-01-shipping-task-templates.md` → `https://rivexapp.com/blog/2025/10/01/shipping-task-templates/`

## Front matter fields

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Page title (shown in `<title>`, post header, and Open Graph). |
| `date` | Yes | Publication date (`YYYY-MM-DD`). Controls sort order on the blog index. |
| `author` | Yes | Byline shown on the post and in `article:author` meta. |
| `description` | Yes | Short summary for SEO, the blog index, and Open Graph. |
| `image` | No | Hero / social image path, e.g. `/blog/assets/my-cover.png`. Used for `og:image` and optional post hero. |
| `canonical` | No | Canonical URL for syndication (Medium, Dev.to). Defaults to the post’s live URL on rivexapp.com. |
| `tags` | No | List of tags (also emitted as `article:tag` meta). |
| `categories` | No | Optional grouping (Jekyll-native; not shown in nav today). |

### Example

```yaml
---
title: "How to monitor stock with Rivex"
date: 2025-10-15
author: "Jane Doe"
description: "Run a repeating check on product pages without babysitting the browser."
image: /blog/assets/stock-monitor.png
canonical: https://rivexapp.com/blog/2025/10/15/monitor-stock-with-rivex/
tags:
  - tutorials
  - stock
categories:
  - guides
---

Your Markdown content starts here.
```

## Images

- Store post-specific images in **`blog/assets/`**.
- Reference them in Markdown: `![Alt text](/blog/assets/filename.png)`
- Or set `image:` in front matter for the hero and social preview.

## Markdown supported in posts

- Headings (`##`, `###`, …)
- **Bold**, *italic*, links
- Blockquotes (`>`)
- Fenced code blocks (``` … ```)
- Ordered and unordered lists

See `_posts/2025-09-16-placeholder-sample-post.md` for a live example (clearly marked as placeholder).

## Local preview

From the repo root (with [mise](https://mise.jdx.dev/) installed):

```bash
mise trust
mise run setup          # first time
bundle install          # first time (Jekyll gems)
mise run jekyll-serve   # http://localhost:4000/
```

Build without serving:

```bash
mise run jekyll-build
```

Output is written to `_site/` (gitignored).

## Syndication notes

Each post page includes:

- `<link rel="canonical" href="…">`
- Open Graph tags (`og:title`, `og:description`, `og:url`, `og:image`, etc.)

When cross-posting to Medium or Dev.to, set `canonical` in front matter to the rivexapp.com URL so search engines and platforms treat this site as the source of truth.
