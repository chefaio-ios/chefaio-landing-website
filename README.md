# Rivex marketing site (GitHub Pages)

Public marketing site for [Rivex](https://rivexapp.com/), plus a [Jekyll](https://jekyllrb.com/) blog. Marketing pages are plain HTML/CSS with a small mobile-nav script; Jekyll builds `/blog/` from `_posts/`.

**Live**

- Site: [https://rivexapp.com](https://rivexapp.com)
- Blog: [https://rivexapp.com/blog/](https://rivexapp.com/blog/)

The GitHub Pages project URL ([https://chefaio-ios.github.io/chefaio-landing-website/](https://chefaio-ios.github.io/chefaio-landing-website/)) redirects to the custom domain.

## GitHub Pages

The production site is already published from this repository. Pages is configured as:

- **Source:** Deploy from a branch
- **Branch:** `main`
- **Folder:** `/ (root)`

GitHub Pages runs Jekyll automatically. Existing static pages (`index.html`, `privacy/`, `tos/`) are copied through unchanged; blog posts are built from `_posts/`.

To inspect or re-apply that setup: **Settings → Pages → Build and deployment**.

### Custom domain (`rivexapp.com`)

This repo includes a `CNAME` file set to `rivexapp.com`. In **Settings → Pages**, the custom domain is `rivexapp.com` and **Enforce HTTPS** is enabled.

DNS for the custom domain is already pointed at GitHub Pages. Keep registrar record changes out of this public README; use GitHub’s [custom domain docs](https://docs.github.com/pages/configuring-a-custom-domain-for-your-github-pages-site) if you need the current procedure.

## Blog

- **Live URL:** https://rivexapp.com/blog/
- **Tech Writer guide:** [blog/README.md](blog/README.md)
- **Add posts:** create Markdown in `_posts/`, images in `blog/assets/`
- **Local preview:** `bundle install` then `mise run jekyll-serve` → http://localhost:4000/

See [blog/README.md](blog/README.md) for front matter fields, URL patterns, and syndication (`canonical` + Open Graph).

## Local development (mise)

This repo uses [mise](https://mise.jdx.dev/) for pinned tools and common tasks — similar to the Rivex iOS app workflow.

1. **Install mise** (once per machine): see [mise.jdx.dev/getting-started.html](https://mise.jdx.dev/getting-started.html)
2. **Trust this repo's config** (first time in this directory):

   ```bash
   mise trust
   ```

3. **Install tools and verify setup:**

   ```bash
   mise install
   # or: mise run setup
   ```

4. **Preview the site locally:**

   ```bash
   mise run serve
   ```

   Open [http://localhost:8080/](http://localhost:8080/).

### mise tasks

| Task | Command | Purpose |
|------|---------|---------|
| setup | `mise run setup` | First-time install + checks |
| install | `mise run install` | Install pinned Python and Ruby |
| serve | `mise run serve` | Static-only preview on port 8080 |
| preview | `mise run preview` | Alias for `serve` |
| jekyll-build | `mise run jekyll-build` | Build marketing site + blog to `_site/` |
| jekyll-serve | `mise run jekyll-serve` | Jekyll preview on port 4000 (includes `/blog`) |
| blog | `mise run blog` | Alias for `jekyll-serve` |
| doctor | `mise run doctor` | Verify site files and toolchain |

Pinned **Python** powers quick static preview (`serve`). **Ruby** + Bundler power the Jekyll blog (`jekyll-serve`). Run `bundle install` once after cloning.

### Without mise

Open `index.html` in a browser, or from this directory:

```bash
python3 -m http.server 8080
```

Then visit `http://localhost:8080/`. For the blog, install Jekyll gems and run `bundle exec jekyll serve`.

## Structure

```
index.html          Landing page
privacy/index.html  Privacy Policy (full legal text)
tos/index.html      Terms of Service (full legal text)
blog/               Blog index + assets (Jekyll)
_posts/             Markdown blog posts (Jekyll)
_layouts/           Jekyll layouts (shared chrome)
_includes/          Jekyll partials (head, nav, footer)
_config.yml         Jekyll + site config
assets/             Local images (no wixstatic hotlinks)
css/styles.css
CNAME               rivexapp.com
README.md
blog/README.md      Tech Writer guide
```

App Store link used everywhere: https://apps.apple.com/app/rivex/id6752362984
