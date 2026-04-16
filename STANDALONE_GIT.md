# Using Alex as its own Git repository

## Initialize (first time)

From this directory (`alex/`):

```bash
git init
git branch -M main
```

Add a remote on GitHub (create an empty repo first, no README if you prefer):

```bash
git remote add origin https://github.com/<you>/<alex-repo>.git
```

Stage and commit (respect `.gitignore` — do not add `.env` or `terraform.tfvars`):

```bash
git add .
git status   # verify no secrets
git commit -m "Initial commit: Alex financial advisor"
git push -u origin main
```

## Fresh re-init

If you already have a `.git` folder here and want a **clean history** (destructive):

```bash
rm -rf .git
git init
git branch -M main
# then add remote and commit as above
```

## GitHub Actions

After pushing, enable **Actions** in the GitHub repo settings. Workflows are under **`.github/workflows/`** in this repo.

## Same folder inside a monorepo

If this tree also lives under a parent repo (e.g. `production/`), Git does not allow a nested `.git` to be committed as a normal folder. Typical options:

- **Submodule**: parent repo references this Alex repo as a submodule; or  
- **Single remote**: only use the standalone Alex repo and remove the nested copy from the parent, or  
- **No nested `.git`**: keep Alex only inside the monorepo and use parent’s `alex-*.yml` workflows.

Choose one model so you do not run duplicate pipelines on the same code.
