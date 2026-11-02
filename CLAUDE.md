# Swipe Life

Godot 4.7.2 Android game. Portrait, Mobile renderer, touch input (mouse emulates touch in editor).

- Scripts in `scripts/`, scenes in `scenes/`, assets in `assets/` (binary assets go through Git LFS).
- Before pushing: `gdlint scripts && gdformat --check scripts`.
- `main` is protected: branch, open a PR, CI (`lint`, `import`) must pass, squash merge.
- Never commit keystores or `export_credentials.cfg`.
