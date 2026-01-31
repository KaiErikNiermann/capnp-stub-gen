set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

# List recipes
default:
  @just --list

# Bump version, commit, tag, push, and create GitHub release
release bump="patch":
  @bump="{{bump}}"; \
    if [[ "$bump" == bump=* ]]; then bump="${bump#bump=}"; fi; \
    poetry version "$bump"
  @version=$(poetry version --short); \
    just _release "$version"

# Use an explicit version
release-version version:
  @version="{{version}}"; \
    if [[ "$version" == version=* ]]; then version="${version#version=}"; fi; \
    poetry version "$version"; \
    just _release "$version"

# Re-trigger publish for an existing version by re-tagging HEAD
rerun version:
  @version="{{version}}"; \
    if [[ "$version" == version=* ]]; then version="${version#version=}"; fi; \
    git push; \
    git tag -d v"$version" || true; \
    git push --delete origin v"$version" || true; \
    git tag v"$version"; \
    git push origin v"$version"

# Delete and recreate the GitHub release + retag HEAD at the same version
rerelease version:
  @version="{{version}}"; \
    if [[ "$version" == version=* ]]; then version="${version#version=}"; fi; \
    gh release delete v"$version" -y || true; \
    just rerun "$version"; \
    gh release create v"$version" --title "v$version" --generate-notes

# Internal helper
_release version:
  @version="{{version}}"; \
    if [[ "$version" == version=* ]]; then version="${version#version=}"; fi; \
    git add pyproject.toml; \
    git add -f poetry.lock; \
    git commit -m "chore(release): v$version"; \
    git push; \
    git tag v"$version"; \
    git push origin v"$version"; \
    gh release create v"$version" --title "v$version" --generate-notes
