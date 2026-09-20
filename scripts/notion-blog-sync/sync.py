#!/usr/bin/env python3
"""Sync Published posts from the Notion Blog Posts database to Jekyll _posts/."""

from __future__ import annotations

import hashlib
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
import yaml
from notion_client import Client
from notion_client.errors import APIResponseError

REPO_ROOT = Path(__file__).resolve().parents[2]
POSTS_DIR = REPO_ROOT / "_posts"
ASSETS_DIR = REPO_ROOT / "blog" / "assets"
SITE_URL = "https://rivexapp.com"
PUBLISHED_STATUS = "Published"
NOTION_ID_KEY = "notion_id"
LIST_BLOCK_TYPES = frozenset({"bulleted_list_item", "numbered_list_item", "to_do"})
SMART_QUOTE_MAP = {
    "\u201c": '"',
    "\u201d": '"',
    "\u2018": "'",
    "\u2019": "'",
}
LAYER_HEADING_RE = re.compile(r"^Layer\s+\d+\s+—", re.IGNORECASE)


def normalize_smart_quotes(text: str) -> str:
    for source, target in SMART_QUOTE_MAP.items():
        text = text.replace(source, target)
    return text


def rich_text_plain(rich_text: list[dict[str, Any]]) -> str:
    return normalize_smart_quotes(
        "".join(item.get("plain_text", "") for item in rich_text),
    ).strip()


def is_layer_heading_paragraph(rich_text: list[dict[str, Any]]) -> bool:
    return bool(LAYER_HEADING_RE.match(rich_text_plain(rich_text)))


@dataclass
class PostData:
    notion_id: str
    title: str
    slug: str
    post_date: date
    author: str
    description: str
    image: str | None = None
    canonical: str | None = None
    tags: list[str] = field(default_factory=list)
    body: str = ""


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(
            f"ERROR: Missing required environment variable {name}.\n"
            f"Set {name} locally or add it as a GitHub Actions secret.",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-") or "post"


def rich_text_to_markdown(
    rich_text: list[dict[str, Any]],
    *,
    strip_bold: bool = False,
) -> str:
    has_code = any(item.get("annotations", {}).get("code") for item in rich_text)
    suppress_bold = strip_bold or has_code
    parts: list[str] = []
    for item in rich_text:
        text = normalize_smart_quotes(item.get("plain_text", ""))
        if not text:
            continue
        annotations = item.get("annotations", {})
        href = item.get("href")
        if annotations.get("code"):
            text = f"`{text}`"
        else:
            if annotations.get("bold") and not suppress_bold:
                text = f"**{text}**"
            if annotations.get("italic"):
                text = f"*{text}*"
            if annotations.get("strikethrough"):
                text = f"~~{text}~~"
        if href:
            text = f"[{text}]({href})"
        parts.append(text)
    return "".join(parts)


def get_property_value(properties: dict[str, Any], name: str) -> Any:
    prop = properties.get(name)
    if not isinstance(prop, dict):
        return None
    prop_type = prop.get("type")
    if prop_type == "title":
        return rich_text_to_markdown(prop.get("title", []))
    if prop_type == "rich_text":
        return rich_text_to_markdown(prop.get("rich_text", []))
    if prop_type == "select":
        selected = prop.get("select")
        return selected.get("name") if selected else None
    if prop_type == "multi_select":
        return [item.get("name", "") for item in prop.get("multi_select", []) if item.get("name")]
    if prop_type == "date":
        date_value = prop.get("date")
        return date_value.get("start") if date_value else None
    if prop_type == "url":
        return prop.get("url")
    if prop_type == "files":
        return prop.get("files", [])
    return None


def resolve_property_name(properties: dict[str, Any], *names: str) -> str | None:
    if not properties:
        return None
    lowered = {key.lower(): key for key in properties}
    for name in names:
        if name in properties:
            return name
        key = lowered.get(name.lower())
        if key:
            return key
    return None


def lookup_property(properties: dict[str, Any], *names: str) -> Any:
    key = resolve_property_name(properties, *names)
    if key is None:
        return None
    return get_property_value(properties, key)


def published_status_filter(database_properties: dict[str, Any]) -> dict[str, Any]:
    status_name = resolve_property_name(database_properties, "Status")
    if not status_name:
        available = ", ".join(sorted(database_properties)) or "(none)"
        print(
            f"ERROR: Blog database has no Status property. Available properties: {available}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    status_type = database_properties[status_name].get("type")
    if status_type == "select":
        return {"property": status_name, "select": {"equals": PUBLISHED_STATUS}}
    if status_type == "status":
        return {"property": status_name, "status": {"equals": PUBLISHED_STATUS}}
    print(
        f"ERROR: Status property {status_name!r} has unsupported type {status_type!r}; "
        "expected select or status.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def page_log_line(page: dict[str, Any]) -> str:
    properties = page.get("properties", {})
    title = lookup_property(properties, "Name") or "(untitled)"
    slug = lookup_property(properties, "Slug") or "(missing slug)"
    post_date = lookup_property(properties, "Date") or "(missing date)"
    return f"{page.get('id', 'unknown')} | {title} | slug={slug} | date={post_date}"


def require_complete_export(
    published_count: int,
    written_count: int,
    failures: list[str],
) -> None:
    if failures:
        print(
            "ERROR: Failed to export Published page(s):\n  " + "\n  ".join(failures),
            file=sys.stderr,
        )
    if written_count != published_count or failures:
        print(
            f"ERROR: Published count ({published_count}) does not match written posts ({written_count}).",
            file=sys.stderr,
        )
        raise SystemExit(1)


def parse_post_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()


def asset_subdir(notion_id: str) -> Path:
    short_id = notion_id.replace("-", "")[:12]
    return ASSETS_DIR / short_id


def extension_from_url(url: str, fallback: str = ".bin") -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix and len(suffix) <= 8:
        return suffix
    return fallback


def download_asset(
    session: requests.Session,
    url: str,
    destination: Path,
    notion_token: str,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    headers = {"Authorization": f"Bearer {notion_token}", "Notion-Version": "2022-06-28"}
    response = session.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    destination.write_bytes(response.content)
    return destination


def resolve_file_url(file_obj: dict[str, Any]) -> str | None:
    if file_obj.get("type") == "external":
        return file_obj.get("external", {}).get("url")
    if file_obj.get("type") == "file":
        return file_obj.get("file", {}).get("url")
    return None


def download_cover_image(
    session: requests.Session,
    notion_token: str,
    notion_id: str,
    files: list[dict[str, Any]],
) -> str | None:
    if not files:
        return None
    file_obj = files[0]
    url = resolve_file_url(file_obj)
    if not url:
        return None
    name = file_obj.get("name") or f"cover{extension_from_url(url, '.jpg')}"
    safe_name = re.sub(r"[^\w.\-]+", "-", name).strip("-") or "cover.jpg"
    destination = asset_subdir(notion_id) / safe_name
    download_asset(session, url, destination, notion_token)
    return f"/blog/assets/{destination.relative_to(ASSETS_DIR).as_posix()}"


class BlockConverter:
    def __init__(self, session: requests.Session, notion_token: str, notion_id: str) -> None:
        self.session = session
        self.notion_token = notion_token
        self.notion_id = notion_id
        self.asset_dir = asset_subdir(notion_id)
        self.downloaded_urls: dict[str, str] = {}

    def convert_blocks(self, client: Client, block_id: str) -> str:
        blocks = self._fetch_blocks(client, block_id)
        return self._render_blocks(client, blocks).strip()

    def _fetch_blocks(self, client: Client, block_id: str) -> list[dict[str, Any]]:
        blocks: list[dict[str, Any]] = []
        cursor: str | None = None
        while True:
            response = client.blocks.children.list(block_id=block_id, start_cursor=cursor)
            blocks.extend(response.get("results", []))
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
        return blocks

    def _render_blocks(self, client: Client, blocks: list[dict[str, Any]], indent: int = 0) -> str:
        chunks: list[str] = []
        pending_list: list[str] = []
        list_counter = 0
        prefix = "  " * indent

        def flush_list() -> None:
            nonlocal list_counter
            if pending_list:
                chunks.append("\n".join(pending_list))
                pending_list.clear()
            list_counter = 0

        def emit_block(text: str) -> None:
            if not text.strip():
                return
            flush_list()
            chunks.append(text)

        def append_list_line(line: str) -> None:
            pending_list.append(line)

        for block in blocks:
            block_type = block.get("type")
            if not block_type:
                continue
            payload = block.get(block_type, {})

            if block_type == "paragraph":
                rich_text = payload.get("rich_text", [])
                text = rich_text_to_markdown(rich_text)
                if text and is_layer_heading_paragraph(rich_text):
                    emit_block(f"{prefix}### {text}")
                else:
                    emit_block(f"{prefix}{text}" if text else "")
            elif block_type in {"heading_1", "heading_2", "heading_3"}:
                level = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}[block_type]
                text = rich_text_to_markdown(payload.get("rich_text", []), strip_bold=True)
                emit_block(f"{prefix}{level} {text}".rstrip())
            elif block_type == "bulleted_list_item":
                text = rich_text_to_markdown(payload.get("rich_text", []))
                append_list_line(f"{prefix}- {text}")
                if block.get("has_children"):
                    children = self._fetch_blocks(client, block["id"])
                    child_md = self._render_blocks(client, children, indent + 1)
                    if child_md:
                        append_list_line(child_md)
            elif block_type == "numbered_list_item":
                list_counter += 1
                text = rich_text_to_markdown(payload.get("rich_text", []))
                append_list_line(f"{prefix}{list_counter}. {text}")
                if block.get("has_children"):
                    children = self._fetch_blocks(client, block["id"])
                    child_md = self._render_blocks(client, children, indent + 1)
                    if child_md:
                        append_list_line(child_md)
            elif block_type == "to_do":
                checked = payload.get("checked", False)
                mark = "x" if checked else " "
                text = rich_text_to_markdown(payload.get("rich_text", []))
                append_list_line(f"{prefix}- [{mark}] {text}")
            elif block_type == "quote":
                text = rich_text_to_markdown(payload.get("rich_text", []))
                quote_lines = [f"{prefix}> {quote_line}" for quote_line in text.splitlines() or [""]]
                emit_block("\n".join(quote_lines))
            elif block_type == "callout":
                text = rich_text_to_markdown(payload.get("rich_text", []))
                emit_block(f"{prefix}> {text}")
            elif block_type == "code":
                language = payload.get("language", "")
                code_text = normalize_smart_quotes(
                    "".join(part.get("plain_text", "") for part in payload.get("rich_text", []))
                )
                code_lines = [f"```{language}".rstrip(), *code_text.splitlines(), "```"]
                emit_block("\n".join(code_lines))
            elif block_type == "divider":
                emit_block(f"{prefix}---")
            elif block_type == "image":
                image_url = self._image_url(payload)
                if image_url:
                    local_path = self._download_image(image_url, "image")
                    caption = rich_text_to_markdown(payload.get("caption", []))
                    alt = caption or Path(local_path).stem
                    emit_block(f"{prefix}![{alt}]({local_path})")
            elif block_type == "bookmark":
                url = payload.get("url")
                caption = rich_text_to_markdown(payload.get("caption", [])) or url
                if url:
                    emit_block(f"{prefix}[{caption}]({url})")
            elif block_type == "embed":
                url = payload.get("url")
                if url:
                    emit_block(f"{prefix}[Embedded content]({url})")
            elif block_type == "video":
                url = self._file_url(payload)
                if url:
                    emit_block(f"{prefix}[Video]({url})")
            elif block_type == "file":
                url = self._file_url(payload)
                caption = rich_text_to_markdown(payload.get("caption", [])) or "Download file"
                if url:
                    emit_block(f"{prefix}[{caption}]({url})")
            elif block_type == "table":
                table_rows = self._fetch_blocks(client, block["id"])
                emit_block(self._render_table(table_rows))
            elif block_type == "column_list":
                column_chunks: list[str] = []
                for column in self._fetch_blocks(client, block["id"]):
                    child_blocks = self._fetch_blocks(client, column["id"])
                    column_md = self._render_blocks(client, child_blocks)
                    if column_md:
                        column_chunks.append(column_md)
                emit_block("\n\n".join(column_chunks))
            elif block_type == "toggle":
                text = rich_text_to_markdown(payload.get("rich_text", []))
                toggle_lines = [f"{prefix}<details><summary>{text}</summary>"]
                if block.get("has_children"):
                    children = self._fetch_blocks(client, block["id"])
                    toggle_lines.append(self._render_blocks(client, children, indent))
                toggle_lines.append(f"{prefix}</details>")
                emit_block("\n".join(toggle_lines))
            else:
                text = rich_text_to_markdown(payload.get("rich_text", []))
                if text:
                    emit_block(f"{prefix}{text}")

        flush_list()
        return "\n\n".join(chunks).strip()

    def _render_table(self, rows: list[dict[str, Any]]) -> str:
        table_lines: list[str] = []
        column_count = 0
        for row in rows:
            if row.get("type") != "table_row":
                continue
            cells = row.get("table_row", {}).get("cells", [])
            cell_text = [rich_text_to_markdown(cell) for cell in cells]
            column_count = max(column_count, len(cell_text))
            table_lines.append("| " + " | ".join(cell_text) + " |")
        if not table_lines:
            return ""
        separator = "| " + " | ".join(["---"] * column_count) + " |"
        table_lines.insert(1, separator)
        return "\n".join(table_lines)

    def _image_url(self, payload: dict[str, Any]) -> str | None:
        image_type = payload.get("type")
        if image_type == "external":
            return payload.get("external", {}).get("url")
        if image_type == "file":
            return payload.get("file", {}).get("url")
        return None

    def _file_url(self, payload: dict[str, Any]) -> str | None:
        file_type = payload.get("type")
        if file_type == "external":
            return payload.get("external", {}).get("url")
        if file_type == "file":
            return payload.get("file", {}).get("url")
        return None

    def _download_image(self, url: str, prefix: str) -> str:
        if url in self.downloaded_urls:
            return self.downloaded_urls[url]
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
        extension = extension_from_url(url, ".jpg")
        destination = self.asset_dir / f"{prefix}-{digest}{extension}"
        download_asset(self.session, url, destination, self.notion_token)
        local_path = f"/blog/assets/{destination.relative_to(ASSETS_DIR).as_posix()}"
        self.downloaded_urls[url] = local_path
        return local_path


def build_post(
    client: Client,
    session: requests.Session,
    notion_token: str,
    page: dict[str, Any],
) -> PostData:
    properties = page.get("properties", {})
    notion_id = page["id"]
    title = lookup_property(properties, "Name") or "Untitled"
    slug_value = lookup_property(properties, "Slug")
    slug = slugify(slug_value or title)
    post_date = parse_post_date(lookup_property(properties, "Date"))
    author = lookup_property(properties, "Author") or "Rivex Team"
    description = lookup_property(properties, "Description") or title
    canonical = lookup_property(properties, "Canonical url", "Canonical")
    tags = lookup_property(properties, "Tags") or []
    cover_files = lookup_property(properties, "Cover") or []
    image = download_cover_image(session, notion_token, notion_id, cover_files)
    converter = BlockConverter(session, notion_token, notion_id)
    body = converter.convert_blocks(client, notion_id)
    post = PostData(
        notion_id=notion_id,
        title=title,
        slug=slug,
        post_date=post_date,
        author=author,
        description=description,
        image=image,
        canonical=canonical,
        tags=tags,
        body=body,
    )
    if not post.canonical:
        post.canonical = canonical_permalink(post)
    return post


def canonical_permalink(post: PostData) -> str:
    return (
        f"{SITE_URL}/blog/{post.post_date.year:04d}/"
        f"{post.post_date.month:02d}/{post.post_date.day:02d}/{post.slug}/"
    )


def render_front_matter(post: PostData) -> str:
    data: dict[str, Any] = {
        "title": post.title,
        "date": post.post_date.isoformat(),
        "author": post.author,
        "description": post.description,
        NOTION_ID_KEY: post.notion_id,
    }
    if post.image:
        data["image"] = post.image
    data["canonical"] = post.canonical or canonical_permalink(post)
    if post.tags:
        data["tags"] = post.tags
    return yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    ).strip()


def post_filename(post: PostData) -> str:
    return f"{post.post_date.isoformat()}-{post.slug}.md"


def write_post(post: PostData) -> Path:
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    path = POSTS_DIR / post_filename(post)
    content = f"---\n{render_front_matter(post)}\n---\n\n{post.body}\n"
    path.write_text(content, encoding="utf-8")
    return path


def load_existing_notion_posts() -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    if not POSTS_DIR.exists():
        return mapping
    for path in POSTS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        front_matter = yaml.safe_load(parts[1]) or {}
        notion_id = front_matter.get(NOTION_ID_KEY)
        if notion_id:
            mapping[str(notion_id)] = path
    return mapping


def remove_stale_posts(published_ids: set[str], existing: dict[str, Path]) -> list[Path]:
    removed: list[Path] = []
    for notion_id, path in existing.items():
        if notion_id not in published_ids:
            path.unlink(missing_ok=True)
            removed.append(path)
    return removed


def retrieve_database_properties(client: Client, database_id: str) -> dict[str, Any]:
    database = client.databases.retrieve(database_id=database_id)
    return database.get("properties", {})


def query_published_pages(
    client: Client,
    database_id: str,
    query_filter: dict[str, Any],
) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        response = client.databases.query(
            database_id=database_id,
            start_cursor=cursor,
            filter=query_filter,
        )
        pages.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return pages


def sync_posts() -> int:
    notion_token = require_env("NOTION_TOKEN")
    database_id = require_env("NOTION_BLOG_DATABASE_ID")
    client = Client(auth=notion_token)
    session = requests.Session()

    try:
        database_properties = retrieve_database_properties(client, database_id)
        query_filter = published_status_filter(database_properties)
        pages = query_published_pages(client, database_id, query_filter)
    except APIResponseError as exc:
        print(f"ERROR: Notion API request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Published pages in Notion: {len(pages)}")
    for page in pages:
        print(f"  {page_log_line(page)}")

    existing = load_existing_notion_posts()
    published_ids = {page["id"] for page in pages}
    removed = remove_stale_posts(published_ids, existing)
    written: list[Path] = []
    failures: list[str] = []

    for page in pages:
        try:
            post = build_post(client, session, notion_token, page)
            previous_path = existing.get(post.notion_id)
            target = write_post(post)
            if previous_path and previous_path.resolve() != target.resolve() and previous_path.exists():
                previous_path.unlink(missing_ok=True)
                removed.append(previous_path)
            written.append(target)
            existing[post.notion_id] = target
            print(
                f"  wrote {target.relative_to(REPO_ROOT)} "
                f"[{post.notion_id}] {post.title}"
            )
        except Exception as exc:  # noqa: BLE001 - fail the job after logging every page
            failures.append(f"{page_log_line(page)} :: {exc}")
            print(f"ERROR: Failed to export page: {page_log_line(page)}: {exc}", file=sys.stderr)

    print(f"Posts written/updated: {len(written)}")
    print(f"Posts removed: {len(removed)}")
    for path in removed:
        print(f"  removed {path.relative_to(REPO_ROOT)}")
    require_complete_export(len(pages), len(written), failures)
    return len(written) + len(removed)


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    changes = sync_posts()
    if changes == 0:
        print("No post changes detected.")
    sys.exit(0)


if __name__ == "__main__":
    main()
