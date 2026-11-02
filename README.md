# Swipe Life

Android game built with Godot 4.7.2 (Mobile renderer, portrait 720×1280).

## Develop
Open `project.godot` in Godot 4.7.2. To run on a device over USB, install the export templates and set the
Android SDK and JDK 17 paths in Editor Settings → Export → Android.

## Builds
- **CI** (every PR and push to `main`): GDScript lint + format check, headless import.
- **Android build** (manual run, or push a `v*` tag): debug APK always; signed release AAB once the keystore
  secrets are set. Tags also publish a GitHub Release with the files.

### Release signing (one-time)
```bash
keytool -genkeypair -v -keystore swipe-life-release.keystore -alias swipelife -keyalg RSA -keysize 2048 -validity 10000
```
Keep the keystore out of the repo and backed up (losing it means you can't update the Play listing). Add repo
secrets `ANDROID_KEYSTORE_BASE64` (`base64 -w0 swipe-life-release.keystore`), `ANDROID_KEYSTORE_ALIAS`,
`ANDROID_KEYSTORE_PASSWORD`.

## License
All rights reserved. The source is publicly visible but not licensed for reuse.
