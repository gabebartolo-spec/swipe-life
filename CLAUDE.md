# Swipe Life

Godot 4.7.2 Android game. Portrait, Mobile renderer, touch input (mouse emulates touch in editor).

**Read `docs/GDD.md` before any gameplay, content, UI or art work.** It wins over your own ideas; if a task
conflicts with it or it does not cover something, stop and ask the director. Only the director changes its decisions.

**`docs/ROADMAP.md`** sets the milestone order: stage 1 to the first playable (birth to 18), stage 2 to death.

- Scripts in `scripts/`, scenes in `scenes/`, assets in `assets/` (binary assets go through Git LFS).
- Before pushing: `gdlint scripts tests && gdformat --check scripts tests`, then `godot --headless --script res://tests/run_tests.gd`.
- `main` is protected: branch, open a PR, CI (`lint`, `import`) must pass, squash merge.
- Never commit keystores or `export_credentials.cfg`.
