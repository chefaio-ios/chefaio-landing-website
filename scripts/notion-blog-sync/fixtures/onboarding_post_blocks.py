"""Representative Notion blocks from the Rivex onboarding post."""

from __future__ import annotations

from typing import Any

from test_sync import rt


def onboarding_snippet_blocks() -> list[dict[str, Any]]:
    return [
        {
            "type": "heading_2",
            "heading_2": {
                "rich_text": [
                    rt("What ", bold=True),
                    rt("mise install", code=True),
                    rt(" actually does", bold=True),
                ],
            },
        },
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
            "paragraph": {"rich_text": [rt("A typical iOS mise.toml might look like this (illustrative):")]},
        },
        {
            "type": "code",
            "code": {
                "language": "toml",
                "rich_text": [
                    rt(
                        "[settings]\n"
                        "pin = true\n\n"
                        "[tools]\n"
                        'tuist = “4.48.2”\n'
                        'swiftlint = “0.57.0”\n'
                        'swiftformat = “0.54.5”'
                    ),
                ],
            },
        },
        {
            "type": "numbered_list_item",
            "numbered_list_item": {"rich_text": [rt("Bootstrap shared env", bold=True)]},
        },
        {
            "type": "paragraph",
            "paragraph": {"rich_text": [rt("Tuist runs in steps 1–2 directly in the hook.")]},
        },
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [rt("What bit us", bold=True)]},
        },
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [rt("Postinstall is not free.", bold=True)]},
        },
        {
            "type": "heading_2",
            "heading_2": {"rich_text": [rt("Principles we'd steal", bold=True)]},
        },
        {
            "type": "table",
            "id": "principles-table",
        },
        {
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [rt("One entry point beats a wiki.", bold=True)]},
        },
    ]


TABLE_ROWS = [
    {
        "type": "table_row",
        "table_row": {"cells": [[rt("Input")], [rt("Output")]]},
    },
    {
        "type": "table_row",
        "table_row": {"cells": [[rt("`mise trust`")], [rt("Repo config is allowed to run on your machine")]]},
    },
]
