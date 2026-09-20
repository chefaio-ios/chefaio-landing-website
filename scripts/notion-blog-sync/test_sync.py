#!/usr/bin/env python3
"""Regression tests for Notion → Jekyll markdown conversion."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from sync import (
    BlockConverter,
    is_layer_heading_paragraph,
    lookup_property,
    normalize_smart_quotes,
    page_log_line,
    published_status_filter,
    require_complete_export,
    resolve_property_name,
    rich_text_to_markdown,
)

COMMIT_SCRIPT = Path(__file__).resolve().parent / "commit_synced_posts.sh"


def rt(
    text: str,
    *,
    bold: bool = False,
    code: bool = False,
    italic: bool = False,
    href: str | None = None,
) -> dict[str, Any]:
    return {
        "plain_text": text,
        "annotations": {
            "bold": bold,
            "code": code,
            "italic": italic,
            "strikethrough": False,
            "underline": False,
        },
        "href": href,
    }


class FakeChildrenList:
    def __init__(self, children_map: dict[str, list[dict[str, Any]]]) -> None:
        self.children_map = children_map

    def list(self, block_id: str, start_cursor: str | None = None) -> dict[str, Any]:
        return {"results": self.children_map.get(block_id, []), "has_more": False}


class FakeBlocks:
    def __init__(self, children_map: dict[str, list[dict[str, Any]]]) -> None:
        self.children = FakeChildrenList(children_map)


class FakeClient:
    def __init__(self, children_map: dict[str, list[dict[str, Any]]]) -> None:
        self.blocks = FakeBlocks(children_map)


class RichTextTests(unittest.TestCase):
    def test_normalize_smart_quotes(self) -> None:
        self.assertEqual(
            normalize_smart_quotes('tuist = “4.48.2”'),
            'tuist = "4.48.2"',
        )

    def test_mixed_bold_and_code_drops_bold_markers(self) -> None:
        rich_text = [
            rt("Layer 1 — pinned tools (", bold=True),
            rt("mise.toml", code=True),
            rt(" → ", bold=True),
            rt("[tools]", code=True),
            rt(")", bold=True),
        ]
        self.assertEqual(
            rich_text_to_markdown(rich_text),
            "Layer 1 — pinned tools (`mise.toml` → `[tools]`)",
        )

    def test_headings_strip_bold(self) -> None:
        rich_text = [rt("What ", bold=True), rt("mise install", code=True), rt(" actually does", bold=True)]
        self.assertEqual(
            rich_text_to_markdown(rich_text, strip_bold=True),
            "What `mise install` actually does",
        )

    def test_layer_heading_paragraph_detection(self) -> None:
        layer = [
            rt("Layer 2 — postinstall hook (", bold=True),
            rt("mise.toml", code=True),
            rt(" → ", bold=True),
            rt("[hooks]", code=True),
            rt(")", bold=True),
        ]
        self.assertTrue(is_layer_heading_paragraph(layer))
        self.assertFalse(
            is_layer_heading_paragraph([rt("Expected:", bold=True), rt(" mise downloads tools.")]),
        )


class BlockConverterTests(unittest.TestCase):
    def _converter(self, children_map: dict[str, list[dict[str, Any]]]) -> BlockConverter:
        session = MagicMock()
        return BlockConverter(session, "token", "page-id"), FakeClient(children_map)

    def test_table_renders_as_gfm_with_blank_line_separation(self) -> None:
        converter, client = self._converter(
            {
                "table-1": [
                    {
                        "type": "table_row",
                        "table_row": {
                            "cells": [[rt("Input")], [rt("Output")]],
                        },
                    },
                    {
                        "type": "table_row",
                        "table_row": {
                            "cells": [[rt("`mise trust`")], [rt("Repo config is allowed")]],
                        },
                    },
                ]
            }
        )
        markdown = converter._render_blocks(
            client,
            [
                {"type": "heading_2", "heading_2": {"rich_text": [rt("Principles", bold=True)]}},
                {"type": "table", "id": "table-1"},
                {
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [rt("One entry point beats a wiki.", bold=True)]},
                },
            ],
        )
        self.assertIn("| Input | Output |", markdown)
        self.assertIn("| --- | --- |", markdown)
        self.assertIn("## Principles\n\n| Input | Output |", markdown)
        self.assertIn(
            "| `mise trust` | Repo config is allowed |\n\n- **One entry point beats a wiki.**",
            markdown,
        )

    def test_code_fence_stays_intact_with_straight_quotes(self) -> None:
        converter, client = self._converter({})
        markdown = converter._render_blocks(
            client,
            [
                {
                    "type": "paragraph",
                    "paragraph": {"rich_text": [rt("A typical iOS mise.toml example:")]},
                },
                {
                    "type": "code",
                    "code": {
                        "language": "toml",
                        "rich_text": [rt('[tools]\ntuist = “4.48.2”\nswiftlint = “0.57.0”')],
                    },
                },
            ],
        )
        self.assertIn(
            '```toml\n[tools]\ntuist = "4.48.2"\nswiftlint = "0.57.0"\n```',
            markdown,
        )
        self.assertNotIn("“", markdown)
        self.assertNotIn("”", markdown)

    def test_numbered_list_closes_before_next_heading(self) -> None:
        converter, client = self._converter({})
        markdown = converter._render_blocks(
            client,
            [
                {"type": "heading_2", "heading_2": {"rich_text": [rt("What bit us", bold=True)]}},
                {
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [rt("Order matters.", bold=True)]},
                },
                {
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [rt("Postinstall is not free.", bold=True)]},
                },
                {"type": "heading_2", "heading_2": {"rich_text": [rt("Principles", bold=True)]}},
                {
                    "type": "paragraph",
                    "paragraph": {"rich_text": [rt("Next up in this series.")]},
                },
            ],
        )
        self.assertIn(
            "- **Postinstall is not free.**\n\n## Principles",
            markdown,
        )
        self.assertIn("## Principles\n\nNext up in this series.", markdown)

    def test_layer_paragraph_promoted_to_h3(self) -> None:
        converter, client = self._converter({})
        markdown = converter._render_blocks(
            client,
            [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            rt("Layer 1 — pinned tools (", bold=True),
                            rt("mise.toml", code=True),
                            rt(" → ", bold=True),
                            rt("[tools]", code=True),
                            rt(")", bold=True),
                        ],
                    },
                },
                {
                    "type": "paragraph",
                    "paragraph": {"rich_text": [rt("A typical iOS mise.toml example:")]},
                },
            ],
        )
        self.assertIn(
            "### Layer 1 — pinned tools (`mise.toml` → `[tools]`)\n\nA typical iOS mise.toml example:",
            markdown,
        )
        self.assertNotIn("**Layer 1", markdown)

    def test_expected_label_stays_bold_paragraph(self) -> None:
        converter, client = self._converter({})
        markdown = converter._render_blocks(
            client,
            [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            rt("Expected:", bold=True),
                            rt(" mise downloads and activates the pinned tools."),
                        ],
                    },
                },
            ],
        )
        self.assertEqual(markdown, "**Expected:** mise downloads and activates the pinned tools.")

    def test_numbered_list_closes_before_paragraph(self) -> None:
        converter, client = self._converter({})
        markdown = converter._render_blocks(
            client,
            [
                {
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [rt("Pin tools first", bold=True)]},
                },
                {
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [rt("Then run side effects", bold=True)]},
                },
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [rt("Tuist recommends mise for exactly this split.")],
                    },
                },
            ],
        )
        self.assertIn(
            "2. **Then run side effects**\n\nTuist recommends mise for exactly this split.",
            markdown,
        )


    def test_onboarding_post_snippet_regression(self) -> None:
        from fixtures.onboarding_post_blocks import TABLE_ROWS, onboarding_snippet_blocks

        converter, client = self._converter({"principles-table": TABLE_ROWS})
        markdown = converter._render_blocks(client, onboarding_snippet_blocks())

        self.assertIn("## What `mise install` actually does", markdown)
        self.assertIn("### Layer 1 — pinned tools (`mise.toml` → `[tools]`)", markdown)
        self.assertNotIn("****", markdown)
        self.assertIn('tuist = "4.48.2"', markdown)
        self.assertIn('swiftlint = "0.57.0"', markdown)
        self.assertIn("\n```toml\n[settings]", markdown)
        self.assertIn('swiftformat = "0.54.5"\n```\n\n1. **Bootstrap shared env**', markdown)
        self.assertIn("1. **Bootstrap shared env**\n\nTuist runs in steps", markdown)
        self.assertIn("- **Postinstall is not free.**\n\n## Principles we'd steal", markdown)
        self.assertIn("## Principles we'd steal\n\n| Input | Output |", markdown)
        self.assertIn("| `mise trust` | Repo config is allowed", markdown)
        self.assertIn(
            "| Repo config is allowed to run on your machine |\n\n- **One entry point beats a wiki.**",
            markdown,
        )
        self.assertIn(
            "- **One entry point beats a wiki.**\n\nNext up in this series:",
            markdown,
        )
        self.assertIn("try Rivex on the App Store](https://apps.apple.com/app/rivex/id6752362984)", markdown)


def _title(text: str) -> dict[str, Any]:
    return {"type": "title", "title": [rt(text)]}


def _rich(text: str) -> dict[str, Any]:
    return {"type": "rich_text", "rich_text": [rt(text)]}


def _date(start: str) -> dict[str, Any]:
    return {"type": "date", "date": {"start": start}}


class PropertyLookupTests(unittest.TestCase):
    def test_resolve_property_name_is_case_insensitive(self) -> None:
        properties = {"Slug": _rich("abc"), "Canonical": {"type": "url", "url": "https://x"}}
        self.assertEqual(resolve_property_name(properties, "slug"), "Slug")
        self.assertEqual(
            resolve_property_name(properties, "Canonical url", "Canonical"),
            "Canonical",
        )

    def test_lookup_property_reads_url_and_rich_text(self) -> None:
        properties = {
            "Canonical": {"type": "url", "url": "https://rivexapp.com/blog/x/"},
            "Slug": _rich("why-rivex-uses-mise-build"),
        }
        self.assertEqual(
            lookup_property(properties, "Canonical url", "Canonical"),
            "https://rivexapp.com/blog/x/",
        )
        self.assertEqual(lookup_property(properties, "slug"), "why-rivex-uses-mise-build")

    def test_published_status_filter_supports_select_and_status(self) -> None:
        self.assertEqual(
            published_status_filter({"Status": {"type": "select"}}),
            {"property": "Status", "select": {"equals": "Published"}},
        )
        self.assertEqual(
            published_status_filter({"status": {"type": "status"}}),
            {"property": "status", "status": {"equals": "Published"}},
        )

    def test_published_status_filter_fails_when_missing(self) -> None:
        with self.assertRaises(SystemExit):
            published_status_filter({"Name": {"type": "title"}})

    def test_page_log_line_includes_id_title_slug_date(self) -> None:
        page = {
            "id": "3e122cfb-2af8-8154-8bb6-e36812d77ef9",
            "properties": {
                "Name": _title("Why Rivex uses mise"),
                "Slug": _rich("why-rivex-uses-mise-build"),
                "Date": _date("2026-09-20"),
            },
        }
        line = page_log_line(page)
        self.assertIn("3e122cfb-2af8-8154-8bb6-e36812d77ef9", line)
        self.assertIn("Why Rivex uses mise", line)
        self.assertIn("slug=why-rivex-uses-mise-build", line)
        self.assertIn("date=2026-09-20", line)

    def test_require_complete_export_passes_when_counts_match(self) -> None:
        require_complete_export(2, 2, [])

    def test_require_complete_export_fails_on_mismatch_or_errors(self) -> None:
        with self.assertRaises(SystemExit):
            require_complete_export(2, 1, [])
        with self.assertRaises(SystemExit):
            require_complete_export(1, 1, ["page-1 boom"])


class CommitSyncedPostsTests(unittest.TestCase):
    def _git(self, repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            text=True,
            capture_output=True,
        )

    def _init_repo(self, repo: Path) -> None:
        self._git(repo, "init")
        self._git(repo, "config", "user.name", "Test Bot")
        self._git(repo, "config", "user.email", "bot@example.com")
        (repo / "README").write_text("seed\n", encoding="utf-8")
        self._git(repo, "add", "README")
        self._git(repo, "commit", "-m", "seed")

    def test_git_diff_misses_untracked_new_posts_until_add(self) -> None:
        """Reproduce the Actions bug: new _posts files are invisible to git diff."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            posts = repo / "_posts"
            posts.mkdir()
            new_post = posts / (
                "2026-09-20-why-rivex-uses-mise-build-and-mise-test-instead-of-raw-xcodebuild.md"
            )
            new_post.write_text("---\ntitle: Topic 2\n---\n\nbody\n", encoding="utf-8")

            unstaged = subprocess.run(
                ["git", "diff", "--quiet"],
                cwd=repo,
                check=False,
            )
            cached = subprocess.run(
                ["git", "diff", "--cached", "--quiet"],
                cwd=repo,
                check=False,
            )
            self.assertEqual(unstaged.returncode, 0)
            self.assertEqual(cached.returncode, 0)

    def test_commit_script_commits_new_untracked_post(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            posts = repo / "_posts"
            posts.mkdir()
            new_post = posts / (
                "2026-09-20-why-rivex-uses-mise-build-and-mise-test-instead-of-raw-xcodebuild.md"
            )
            new_post.write_text("---\ntitle: Topic 2\n---\n\nbody\n", encoding="utf-8")
            script = repo / "commit_synced_posts.sh"
            script.write_text(COMMIT_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
            os.chmod(script, 0o755)

            result = subprocess.run(
                ["bash", str(script)],
                cwd=repo,
                check=True,
                text=True,
                capture_output=True,
            )
            log = self._git(repo, "log", "-1", "--name-only", "--pretty=%s")
            self.assertIn("chore(blog): sync Published posts from Notion", log.stdout)
            self.assertIn(new_post.name, log.stdout)
            self.assertNotIn("No changes to commit.", result.stdout)

    def test_commit_script_noops_when_already_synced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            posts = repo / "_posts"
            posts.mkdir()
            existing = posts / "2026-09-16-how-we-onboard-rivex-with-one-mise-install.md"
            existing.write_text("---\ntitle: Topic 1\n---\n\nbody\n", encoding="utf-8")
            self._git(repo, "add", "_posts")
            self._git(repo, "commit", "-m", "existing post")
            script = repo / "commit_synced_posts.sh"
            script.write_text(COMMIT_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
            os.chmod(script, 0o755)

            result = subprocess.run(
                ["bash", str(script)],
                cwd=repo,
                check=True,
                text=True,
                capture_output=True,
            )
            self.assertIn("No changes to commit.", result.stdout)
            log = self._git(repo, "log", "-1", "--pretty=%s")
            self.assertEqual(log.stdout.strip(), "existing post")


if __name__ == "__main__":
    unittest.main()
