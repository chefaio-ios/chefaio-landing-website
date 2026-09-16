# Rivex marketing site (GitHub Pages)

Static recreation of [rivexapp.com](https://www.rivexapp.com/) for hosting on GitHub Pages. Plain HTML/CSS (tiny mobile-nav JS). No build step.

## Enable GitHub Pages

1. Push this repo to GitHub (parent agent handles push).
2. Open **Settings → Pages**.
3. Under **Build and deployment**, set:
   - **Source:** Deploy from a branch
   - **Branch:** `main`
   - **Folder:** `/ (root)`
4. Click **Save**.

### Preview URL

After Pages is enabled, the site is available at:

**https://chefaio-ios.github.io/chefaio-landing-website/**

Keep the live Wix site up until this preview looks correct.

## Custom domain (`rivexapp.com`)

This repo already includes a `CNAME` file with:

```
rivexapp.com
```

1. In **Settings → Pages → Custom domain**, add `rivexapp.com`.
2. After DNS verifies, enable **Enforce HTTPS**.

## Wix DNS cutover

Point DNS away from Wix only after the github.io preview looks good.

### Apex (`rivexapp.com`) — A records

| Type | Host | Value |
|------|------|-------|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |

### Apex — AAAA records (IPv6)

| Type | Host | Value |
|------|------|-------|
| AAAA | `@` | `2606:50c0:8000::153` |
| AAAA | `@` | `2606:50c0:8001::153` |
| AAAA | `@` | `2606:50c0:8002::153` |
| AAAA | `@` | `2606:50c0:8003::153` |

### `www` — CNAME

| Type | Host | Value |
|------|------|-------|
| CNAME | `www` | `chefaio-ios.github.io` |

Remove or replace existing Wix A/CNAME records that conflict. DNS propagation can take from a few minutes up to 48 hours.

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
| serve | `mise run serve` | Local static preview on port 8080 |
| preview | `mise run preview` | Alias for `serve` |
| doctor | `mise run doctor` | Verify site files and toolchain |

Pinned **Python** powers local preview today. **Ruby** is pinned now so we can add a Jekyll blog later without reworking the toolchain.

### Without mise

Open `index.html` in a browser, or from this directory:

```bash
python3 -m http.server 8080
```

Then visit `http://localhost:8080/`.

## Structure

```
index.html          Landing page
privacy/index.html  Privacy Policy (full legal text)
tos/index.html      Terms of Service (full legal text)
assets/             Local images (no wixstatic hotlinks)
css/styles.css
CNAME               rivexapp.com
README.md
```

App Store link used everywhere: https://apps.apple.com/app/rivex/id6752362984
