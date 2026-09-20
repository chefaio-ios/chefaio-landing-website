# Notion → Rivex blog sync

The **Notion Blog Posts** database is the CMS for published articles. Only rows with **Status = Published** are exported to this repo by the [Notion Blog Sync](../../.github/workflows/notion-blog-sync.yml) GitHub Action.

Draft and Review posts stay in Notion and are **not** synced.

## Writer workflow

1. Create or edit a post in the Notion Blog Posts database.
2. Fill in the properties below (especially **Slug** and **Date**).
3. Write the article body as Notion page blocks.
4. Set **Status** to **Published** when ready for rivexapp.com.
5. Trigger a sync (see [Triggering a sync](#triggering-a-sync)) or wait for the hourly schedule.

Do **not** hand-edit synced Markdown files in `_posts/` that contain a `notion_id` field. The next sync will overwrite or remove them. Hand-written posts without `notion_id` are left alone.

## Property → Jekyll front matter

| Notion property | Jekyll front matter | Notes |
|-----------------|---------------------|-------|
| Name | `title` | Page title |
| Slug | filename slug | Used in `_posts/YYYY-MM-DD-<slug>.md` and the public URL |
| Date | `date` | `YYYY-MM-DD`; controls sort order |
| Status | *(not exported)* | Must be **Published** to sync |
| Description | `description` | SEO summary and Open Graph text |
| Author | `author` | Byline |
| Cover | `image` | Downloaded to `/blog/assets/notion/...` |
| Tags | `tags` | Multi-select → YAML list |
| Canonical url | `canonical` | Optional syndication canonical URL |
| Page body blocks | Markdown body | Headings, lists, quotes, code, images, etc. |
| *(system)* | `notion_id` | Added by the sync script to track managed posts |

Published URLs follow the existing pattern:

`/blog/YYYY/MM/DD/your-slug/`

## Images

- **Cover** files are stored under `blog/assets/notion/` and referenced from front matter `image`.
- Inline images in the Notion body are downloaded to the same folder and rewritten in Markdown.

## Triggering a sync

**Automatic:** the workflow runs on an hourly schedule.

**Manual:** in GitHub → **Actions** → **Notion Blog Sync** → **Run workflow** (branch: `main`).

**Local (developers):** see [`scripts/notion-blog-sync/README.md`](../scripts/notion-blog-sync/README.md).

## GitHub secrets (repository admins)

| Secret | Value |
|--------|-------|
| `NOTION_TOKEN` | Notion internal integration secret with read access to the Blog Posts database |
| `NOTION_BLOG_DATABASE_ID` | `62c4f7e431b3477aad89da0e6880abcc` |

Without these secrets, the Action fails with a clear error and makes no commits.

## What is not synced

- **Draft**, **Review**, and **Archived** statuses
- Hand-written `_posts/*.md` files that do not include `notion_id` (for example the placeholder sample and legacy engineering posts)
