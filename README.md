# Rajiv's blog

A static Quarto blog about numerical methods, programming, and hardware design.

## Local preview

With conda installed, run:

```sh
python3 scripts/site.py setup
python3 scripts/site.py preview
```

Open <http://localhost:8765>. Stop the preview with Ctrl-C.

## Editing

Articles live in `posts/`. Copy `posts/_template.qmd` for a new article and add
it to `index.qmd`. Site settings are in `_quarto.yml`; styles are in `assets/`.

## Build and publish

```sh
python3 scripts/check_article_models.py
python3 scripts/site.py build
python3 scripts/site.py fixture
```

The built website is in `dist/`. GitHub Actions checks pull requests and
publishes pushes to `main`. In the repository's **Settings → Pages**, select
**GitHub Actions** as the publishing source.
