#!/usr/bin/env python3
"""Regression tests for Notion → Jekyll markdown conversion."""

from __future__ import annotations

import unittest
from typing import Any
from unittest.mock import MagicMock

from sync import (
    BlockConverter,
    normalize_smart_quotes,
    rich_text_to_markdown,
)


def rt(
    text: str,
    *,
    bold: bool = False,
    code: bool = False,
    italic: bool = False,
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
        "href": None,
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
        self.assertIn("Layer 1 — pinned tools (`mise.toml` → `[tools]`)", markdown)
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


if __name__ == "__main__":
    unittest.main()
