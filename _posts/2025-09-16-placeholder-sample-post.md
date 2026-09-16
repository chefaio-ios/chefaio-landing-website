---
title: "Placeholder sample post (for Tech Writers)"
date: 2025-09-16
author: "Rivex Tech Writing"
description: >-
  Sample Markdown post demonstrating headings, images, blockquotes, code blocks,
  and lists. Replace this file before publishing real content.
image: /blog/assets/sample-hero.svg
canonical: https://rivexapp.com/blog/2025/09/16/placeholder-sample-post/
tags:
  - sample
  - placeholder
categories:
  - meta
---
> **Placeholder only.** This post exists to show Tech Writers how Markdown renders on the Rivex blog. Delete or replace it when publishing real articles.

## Section heading

Use `##` for section headings and `###` for subsections. Body copy supports **bold**, *italic*, and [links](https://rivexapp.com).

### Sample image

Images live in `blog/assets/` and are referenced from the post body or front matter `image` field:

![Sample placeholder graphic for blog posts](/blog/assets/sample-hero.svg)

### Blockquote

> Automation should feel invisible: set up a task once, run it whenever you need it, and stay in control from the Rivex app.

### Fenced code block

```javascript
// Example: a tiny helper Tech Writers might quote in a tutorial
function greet(name) {
  return `Hello, ${name}!`;
}

console.log(greet("Rivex"));
```

### Unordered list

- Create a Markdown file in `_posts/` with the required front matter
- Add images to `blog/assets/` when needed
- Run `mise run jekyll-serve` to preview locally before opening a PR
