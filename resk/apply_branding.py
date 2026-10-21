"""Apply Resk Remote branding to a RustDesk checkout.

Idempotent: every edit checks for its upstream text and is skipped once applied.
Run from the repo root after merging upstream: python3 resk/apply_branding.py
Icons/logos are regenerated separately by resk/gen_assets.py. The server
address and key live in the hbb_common fork (preplink/resk-remote-hbb-common).

Palette (Resk design tokens):
  ink #151513, paper #F5F3EE, sheet #FFFEFC, edges #DEDAD2/#CBC6BC/#B3ADA2,
  orange-600 #D64E24 (accent: white text on it clears 4:1, the #EE6439 logo
  dot does not), dark sheet #140F0C, dark tiles #1D1612/#251C17.
"""
import re
import sys
from pathlib import Path

ACCENT = "0xFFD64E24"
failures = []


def edit(path, pairs, regex=False):
    p = Path(path)
    s = p.read_text()
    for old, new in pairs:
        if regex:
            s2 = re.sub(old, new, s)
            if s2 == s and not re.search(new.replace("\\", ""), s):
                failures.append(f"{path}: pattern not found {old!r}")
            s = s2
        elif old in s:
            s = s.replace(old, new)
        elif new not in s:
            failures.append(f"{path}: not found {old!r}")
    p.write_text(s)


# --- Theme -----------------------------------------------------------------
edit("flutter/lib/common.dart", [
    # MyTheme
    ("grayBg = Color(0xFFEFEFF2)", "grayBg = Color(0xFFF5F3EE)"),
    ("accent = Color(0xFF0071FF)", f"accent = Color({ACCENT})"),
    ("accent50 = Color(0x770071FF)", "accent50 = Color(0x77D64E24)"),
    ("accent80 = Color(0xAA0071FF)", "accent80 = Color(0xAAD64E24)"),
    ("canvasColor = Color(0xFF212121)", "canvasColor = Color(0xFF151513)"),
    ("border = Color(0xFFCCCCCC);", "border = Color(0xFFDEDAD2);"),
    ("idColor = Color(0xFF00B6F0)", f"idColor = Color({ACCENT})"),
    ("button = Color(0xFF2C8CFF)", f"button = Color({ACCENT})"),
    ("hoverBorder = Color(0xFF999999)", "hoverBorder = Color(0xFFB3ADA2)"),
    # Light extension
    ("border: Color(0xFFCCCCCC),\n    border2: Color(0xFFBBBBBB),",
     "border: Color(0xFFDEDAD2),\n    border2: Color(0xFFCBC6BC),"),
    ("highlight: Color(0xFFE5E5E5),", "highlight: Color(0xFFECE9E3),"),
    # Dark extension
    ("border: Color(0xFF555555),", "border: Color(0xFF3A2A22),"),
    ("highlight: Color(0xFF3F3F3F),", "highlight: Color(0xFF251C17),"),
    # Light theme
    ("hoverColor: Color.fromARGB(255, 224, 224, 224),\n    scaffoldBackgroundColor: Colors.white,\n    dialogBackgroundColor: Colors.white,",
     "hoverColor: Color(0xFFECE9E3),\n    scaffoldBackgroundColor: Color(0xFFFFFEFC),\n    dialogBackgroundColor: Color(0xFFFFFEFC),"),
    ("primary: Colors.blue, secondary: accent, background: grayBg)",
     "primary: accent, secondary: accent, background: grayBg)"),
    ("? Color(0xFFECECEC)", "? Color(0xFFECE9E3)"),
    # Dark theme
    ("scaffoldBackgroundColor: Color(0xFF18191E),\n    dialogBackgroundColor: Color(0xFF18191E),",
     "scaffoldBackgroundColor: Color(0xFF140F0C),\n    dialogBackgroundColor: Color(0xFF140F0C),"),
    ("MaterialStatePropertyAll(Color(0xFF121212))", "MaterialStatePropertyAll(Color(0xFF0D0806))"),
    ("      primary: Colors.blue,\n      secondary: accent,", "      primary: accent,\n      secondary: accent,"),
    # Links in dialogs, default peer avatar
    ("style: const TextStyle(\n        color: Colors.blue,\n        decoration: TextDecoration.underline,",
     "style: const TextStyle(\n        color: MyTheme.accent,\n        decoration: TextDecoration.underline,"),
    ("  return Color(0xFF2C8CFF);", f"  return Color({ACCENT});"),
])
s = Path("flutter/lib/common.dart").read_text()
n = s.count("Color(0xFF24252B)")
Path("flutter/lib/common.dart").write_text(s.replace("Color(0xFF24252B)", "Color(0xFF1D1612)"))
if n == 0 and "Color(0xFF1D1612)" not in s:
    failures.append("common.dart: dark tile 0xFF24252B not found")

# Remaining stock Material blues in widgets -> the accent.
for f in [
    "flutter/lib/desktop/widgets/update_progress.dart",
    "flutter/lib/desktop/widgets/remote_toolbar.dart",
    "flutter/lib/common/widgets/toolbar.dart",
    "flutter/lib/common/widgets/custom_password.dart",
    "flutter/lib/mobile/pages/terminal_page.dart",
    "flutter/lib/mobile/pages/server_page.dart",
    "flutter/lib/mobile/widgets/floating_mouse.dart",
    "flutter/lib/mobile/widgets/floating_mouse_widgets.dart",
]:
    p = Path(f)
    s = p.read_text()
    # Code only: skip `// ...` comment lines.
    out = [l if l.lstrip().startswith("//") else re.sub(r"Colors\.blue(Accent)?\b", "MyTheme.accent", l)
           for l in s.split("\n")]
    p.write_text("\n".join(out))

# Flat buttons: no Material drop shadow under the filled accent button.
s = Path("flutter/lib/common.dart").read_text()
old = """      style: ElevatedButton.styleFrom(
        backgroundColor: MyTheme.accent,"""
new = """      style: ElevatedButton.styleFrom(
        elevation: 0,
        shadowColor: Colors.transparent,
        backgroundColor: MyTheme.accent,"""
if s.count(old) == 2:
    s = s.replace(old, new)
elif s.count(new) != 2:
    failures.append("common.dart: elevatedButtonTheme blocks not found")
Path("flutter/lib/common.dart").write_text(s)

# ID / password boards: drop the coloured side bars (keep the 2px slot so the
# text stays where upstream lays it out).
edit("flutter/lib/desktop/pages/desktop_home_page.dart", [
    ("decoration: const BoxDecoration(color: MyTheme.accent),\n          ).marginOnly(top: 5),",
     "decoration: const BoxDecoration(color: Colors.transparent),\n          ).marginOnly(top: 5),"),
    ("height: 52,\n            decoration: BoxDecoration(color: MyTheme.accent),",
     "height: 52,\n            decoration: BoxDecoration(color: Colors.transparent),"),
])

# "Public server" here means "no custom server set". Our default IS our own
# server, so never treat it as RustDesk's public one (hides the "set up your
# own server" upsell and the public-server feature limits).
edit("src/common.rs", [(
    'pub fn using_public_server() -> bool {\n    crate::get_custom_rendezvous_server(get_option("custom-rendezvous-server")).is_empty()\n}',
    'pub fn using_public_server() -> bool {\n    false // Resk Remote: the built-in default is rustdesk.resk.ai\n}',
)])

# The small "Powered by RustDesk" link above the logo. RustDesk stays credited
# in About and in this AGPL source; the home screen carries the Resk wordmark.
edit("flutter/lib/common.dart", [(
    'Widget loadPowered(BuildContext context) {\n  if (bind.mainGetBuildinOption(key: "hide-powered-by-me") == \'Y\') {',
    'Widget loadPowered(BuildContext context) {\n  if (true || bind.mainGetBuildinOption(key: "hide-powered-by-me") == \'Y\') {',
)])

# --- Names -----------------------------------------------------------------
edit("flutter/windows/runner/Runner.rc", [
    ('"FileDescription", "RustDesk Remote Desktop"', '"FileDescription", "Resk Remote"'),
    ('"ProductName", "RustDesk"', '"ProductName", "Resk Remote"'),
])
edit("flutter/windows/runner/main.cpp", [('app_name = L"RustDesk";', 'app_name = L"ReskRemote";')])
edit("flutter/android/app/src/main/res/values/strings.xml", [
    ('<string name="app_name">RustDesk</string>', '<string name="app_name">Resk Remote</string>'),
    ("when RustDesk screen sharing", "when Resk Remote screen sharing"),
    ("Keeps the RustDesk remote desktop host", "Keeps the Resk Remote host"),
])
edit("flutter/android/app/src/main/AndroidManifest.xml", [
    ('android:label="RustDesk"', 'android:label="Resk Remote"'),
    ('android:label="RustDesk Input"', 'android:label="Resk Remote Input"'),
])
# Own package id so it installs beside (not over) stock RustDesk. The Kotlin
# namespace stays com.carriez.flutter_hbb because the JNI symbols depend on it.
edit("flutter/android/app/build.gradle", [
    ('applicationId "com.carriez.flutter_hbb"', 'applicationId "ai.resk.remote"'),
])

if failures:
    print("BRANDING INCOMPLETE:\n  " + "\n  ".join(failures))
    sys.exit(1)
print("branding applied")
