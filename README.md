# Rajiv's blog

An independent Quarto website with a plain theme, About page and useful links.
Author posts in Markdown (`.qmd`), with equations, highlighted code, figures and
local JavaScript. Each rendered page embeds its styles, scripts and supported
assets in one HTML file. Equations use native MathML. No frontend framework or
Bazel build is needed for this repository.

## Setup and preview

Install conda, then run from this directory:

```sh
python3 scripts/site.py setup
python3 scripts/site.py preview
```

Preview opens at <http://localhost:8765>. Stop it with Ctrl-C. Change the port with
`--port 8766`. Set `CONDA_EXE` if conda is not on your PATH.

Quarto 1.9.38 and Python 3.12.15 come from conda-forge. `environment.yml` pins the
requested tools; `env/osx-arm64.lock` and `env/linux-64.lock` pin every package
artifact with SHA-256. The wrapper hashes the specification, platform lock and
setup script to choose an immutable prefix under `.envs/`. It resolves Quarto's
tools from that prefix and checks the installed package records before rendering.
No environment activation is needed. Changes to setup inputs create a new prefix.

## Authoring

The detailed four-post plan is in [docs/series-plan.md](docs/series-plan.md).
The public overview is `series.qmd`. `AGENTS.md` records prose and theme conventions.

Copy `posts/_template.qmd` to a descriptive filename, update its metadata and
remove `draft: true` when ready to publish. Add a link on `index.qmd`. The template
and `docs/` are excluded from the website render list. Use `draft: true` for
unfinished posts; render them individually for review.

Keep content scripts scoped to their widget's element. Embed local scripts using
raw HTML blocks or Quarto includes; include exported data inline rather than
fetching it from another service. Keep controls keyboard accessible, with a
useful initial view before interaction. Keep animations out of the site shell.

Research execution belongs in the separate code repository. Copy results into
`data/` and record their source commit, environment identity, target and hashes
in provenance records. Rendering never executes research code.

## Build and publish

```sh
python3 scripts/check_article_models.py
python3 scripts/site.py build
python3 scripts/site.py fixture
```

The model check validates the first two posts’ teaching math and embedded
MPFR dataset. Draft details are in [docs/first-two-posts.md](docs/first-two-posts.md).

`build` renders the site to `dist/` and checks local links, anchors and embedded
resources. `fixture` renders a private code/math/interaction preview to `.preview/`
and checks its packaging. Neither editorial notes nor this fixture are published.
`python3 scripts/site.py check` checks an existing `dist/` without rendering.
Custom widgets that dynamically load assets should be checked in the browser too.

Each post is `dist/posts/<name>.html`; its embedded assets travel with the file.
Navigation links still refer to other pages of the blog. `dist/` is the complete
GitHub Pages artifact. Relative links support both repository and root sites.

Push this directory as its own repository with a `main` branch. In GitHub's
**Settings → Pages → Build and deployment**, choose **GitHub Actions**. The
included workflow builds and checks pull requests, and publishes pushes to main.
It uses commit-pinned actions and the Linux package lock. Deployment runs from
the `github-pages` environment. No GitHub remote or site has been created here.

Edit the title/navigation/footer in `_quarto.yml`, colors and typography in
`assets/theme.scss`, and layout details in `assets/style.css`. Add author-provided
profile and repository URLs to `links.qmd` or the navigation when available.
