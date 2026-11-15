#!/usr/bin/env bash
# Build Kamus Mandarin Offline APK (WebView wrapper) without Gradle, on this VM.
# Pipeline: javac -> d8 -> aapt2 -> zip assets -> zipalign -> apksigner
# Pola disalin dari bhs-jawa-offline/apk/scripts/01_build_apk.sh (versi VM, tanpa phone).
set -euo pipefail

VERSION_CODE=1
VERSION_NAME="1.0.0"
APK_NAME="KamusMandarin-Offline-v${VERSION_NAME}.apk"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_WEB="$ROOT/.."
SDK="$HOME/workspace/android-sdk"
JDK="$HOME/workspace/jdk/jdk-17.0.20.1+1"
BT="$SDK/build-tools/34.0.0"
PLAT="$SDK/platforms/android-34/android.jar"
APP="$ROOT/app"
TMP="$ROOT/tmp"
DIST="$ROOT/dist"

export JAVA_HOME="$JDK"
export PATH="$JDK/bin:$PATH"
command -v java javac keytool zip python3 >/dev/null || { echo "missing build tools"; exit 1; }
[ -f "$PLAT" ] || { echo "SDK not found at $PLAT"; exit 1; }

rm -rf "$TMP" "$DIST"
mkdir -p "$TMP/classes" "$TMP/dex" "$TMP/assets" "$DIST"

echo "==> 0. assets: index.html + kamus_data.js (offline, tanpa internet)"
cp "$SRC_WEB/index.html" "$APP/assets/index.html"
cp "$SRC_WEB/data/kamus_data.js" "$APP/assets/kamus_data.js"
ls -la "$APP/assets/"

echo "==> 1. icon"
python3 "$ROOT/scripts/make_icon.py" --out "$APP/res/drawable/ic_launcher.png"

echo "==> 2. javac"
mapfile -d '' JAVA_SRC < <(find "$APP/src" -name '*.java' -print0 | sort -z)
javac -source 1.8 -target 1.8 -nowarn -Xlint:-options \
      -bootclasspath "$PLAT" \
      -d "$TMP/classes" "${JAVA_SRC[@]}"

echo "==> 3. d8 (dex)"
mapfile -t DEX_CLS < <(find "$TMP/classes" -name '*.class' | sort)
"$BT/d8" --release --lib "$PLAT" --min-api 24 \
    --output "$TMP/dex" "${DEX_CLS[@]}"
ls -la "$TMP/dex/classes.dex"

echo "==> 4. aapt2 (resources)"
"$BT/aapt2" compile --dir "$APP/res" -o "$TMP/res.zip"
"$BT/aapt2" link -o "$TMP/base.apk" -I "$PLAT" \
    --manifest "$APP/AndroidManifest.xml" \
    -R "$TMP/res.zip" \
    --min-sdk-version 24 --target-sdk-version 34 \
    --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" \
    --auto-add-overlay

echo "==> 5. assemble (dex + assets into apk)"
cp "$TMP/base.apk" "$TMP/app.unsigned.apk"
cp "$TMP/dex/classes.dex" "$TMP/classes.dex"
cp "$APP/assets/"* "$TMP/assets/"
( cd "$TMP" && zip -0 -q app.unsigned.apk classes.dex $(ls assets/* | sort) )

echo "==> 6. zipalign"
"$BT/zipalign" -f -p 4 "$TMP/app.unsigned.apk" "$TMP/app.aligned.apk"

echo "==> 7. keystore + sign"
KS="$ROOT/keystore.jks"
if [ ! -f "$KS" ]; then
    keytool -genkeypair -keystore "$KS" -alias kamusmandarin \
        -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass mandarin123 -keypass mandarin123 \
        -dname "CN=Kamus Mandarin Offline, OU=Offline, O=kamusmandarin-web, L=Salatiga, ST=Jawa Tengah, C=ID" 2>/dev/null
fi
"$BT/apksigner" sign --ks "$KS" --ks-key-alias kamusmandarin \
    --ks-pass pass:mandarin123 --key-pass pass:mandarin123 \
    --out "$DIST/$APK_NAME" "$TMP/app.aligned.apk"

echo "==> 8. verify"
"$BT/apksigner" verify --print-certs "$DIST/$APK_NAME" | head -6
"$BT/aapt2" dump badging "$DIST/$APK_NAME" | grep -E "^package|^application-label:|^sdkVersion|^targetSdkVersion|launchable-activity"
ls -la "$DIST/$APK_NAME"
echo "BUILD_OK"
du -h "$DIST/$APK_NAME"
