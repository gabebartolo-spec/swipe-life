# Swipe Life

Godot 4.7.2 Android game. Portrait, Mobile renderer, touch input (mouse emulates touch in editor).

**Read `docs/GDD.md` before any gameplay, content, UI or art work.** It wins over your own ideas; if a task
conflicts with it or it does not cover something, stop and ask the director. Only the director changes its decisions.

- Scripts in `scripts/`, scenes in `scenes/`, assets in `assets/` (binary assets go through Git LFS).
- Before pushing: `gdlint scripts && gdformat --check scripts`.
- `main` is protected: branch, open a PR, CI (`lint`, `import`) must pass, squash merge.
- Never commit keystores or `export_credentials.cfg`.
