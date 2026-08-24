#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בונה את גרסת הווב לקובץ HTML יחיד ועצמאי.

    python3 web/build.py            # יוצר web/index.html
"""
import os
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
JS_PARTS = ["data.js", "engine.js", "story.js", "game.js", "graphics.js", "scenes.js", "ui.js"]

HEAD = """<title>קריירה</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700&family=Karantina:wght@700&display=swap">
<style>
%(css)s
</style>
<div id="app"></div>
<script>
%(js)s
</script>
"""


def read(name: str) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


def build() -> str:
    css = read("style.css")
    js = "\n".join(read(part) for part in JS_PARTS)
    return HEAD % {"css": css, "js": js}


def check_bundle() -> None:
    """מוודא שכל קבצי ה-JS יחד מתפרשים — קובץ תקין לבדו עדיין יכול להתנגש בשכן."""
    js = "\n".join(read(part) for part in JS_PARTS)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(js)
        path = fh.name
    try:
        result = subprocess.run(["node", "--check", path],
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit("החבילה לא מתפרשת:\n" + result.stderr.strip())
    except FileNotFoundError:
        pass          # אין node בסביבה — מדלגים על הבדיקה
    finally:
        os.unlink(path)


def main() -> None:
    check_bundle()
    out = os.path.join(HERE, "index.html")
    html = build()
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"נבנה: {out} ({len(html.encode('utf-8')) / 1024:.0f}KB)")


if __name__ == "__main__":
    main()
