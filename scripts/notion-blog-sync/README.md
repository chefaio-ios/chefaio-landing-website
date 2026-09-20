# Notion blog sync

Exports **Published** posts from the Notion Blog Posts database into Jekyll `_posts/` and downloads images to `blog/assets/`.

## Required environment variables

| Variable | Description |
|----------|-------------|
| `NOTION_TOKEN` | Notion integration secret with access to the Blog Posts database |
| `NOTION_BLOG_DATABASE_ID` | Database ID (`62c4f7e431b3477aad89da0e6880abcc` for Rivex) |

## Tests

```bash
pip install -r scripts/notion-blog-sync/requirements.txt
python3 -m unittest scripts/notion-blog-sync/test_sync.py -v
```

## Local run

From the repo root:

```bash
mise install
python -m venv .venv-notion-sync
source .venv-notion-sync/bin/activate
pip install -r scripts/notion-blog-sync/requirements.txt

export NOTION_TOKEN="secret_..."
export NOTION_BLOG_DATABASE_ID="62c4f7e431b3477aad89da0e6880abcc"
python scripts/notion-blog-sync/sync.py
```

Preview the generated site:

```bash
bundle install
mise run jekyll-serve
```

## Behavior

- Queries Notion for rows where `Status` is `Published`
- Writes `_posts/YYYY-MM-DD-slug.md` with required front matter (`title`, `date`, `author`, `description`) plus `notion_id`
- Slug is used in the filename only (not exported as a front-matter key)
- Sets `canonical` from Notion or computes `https://rivexapp.com/blog/YYYY/MM/DD/<slug>/`
- Downloads cover and inline images to `blog/assets/<page-id>/`
- Removes previously synced posts (those with `notion_id`) when they are no longer `Published`
- Leaves hand-written posts without `notion_id` untouched

The GitHub Action runs the same script and commits changes to `main` when posts differ.
