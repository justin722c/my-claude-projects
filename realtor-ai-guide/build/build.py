#!/usr/bin/env python3
"""Build branded PDFs for Team Smith Homes.

Usage: python3 build/build.py            (builds both PDFs into output/)
Needs: pip install markdown pypdf ; Chromium (PLAYWRIGHT_BROWSERS_PATH or CHROME env var)
"""
import glob, html, os, re, subprocess, sys
import markdown
from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "output")
CHROME = os.environ.get("CHROME") or (glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome") or ["chromium"])[0]

CSS = open(os.path.join(BUILD, "style.css")).read()
FONTS = """
@font-face{font-family:'Playfair Display';font-weight:500;font-style:normal;src:url('../assets/fonts/PlayfairDisplay-500-normal.woff2') format('woff2');}
@font-face{font-family:'Playfair Display';font-weight:500;font-style:italic;src:url('../assets/fonts/PlayfairDisplay-500-italic.woff2') format('woff2');}
@font-face{font-family:'Playfair Display';font-weight:700;font-style:normal;src:url('../assets/fonts/PlayfairDisplay-700-normal.woff2') format('woff2');}
@font-face{font-family:'IBM Plex Mono';font-weight:400;src:url('../assets/fonts/IBMPlexMono-400-normal.woff2') format('woff2');}
@font-face{font-family:'IBM Plex Mono';font-weight:500;src:url('../assets/fonts/IBMPlexMono-500-normal.woff2') format('woff2');}
"""

def md_to_html(text):
    h = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    # placeholders inside prompts
    def ph(m):
        return re.sub(r"\[([^\]\n]+)\]", r'<span class="ph">[\1]</span>', m.group(0))
    h = re.sub(r"<pre><code[^>]*>.*?</code></pre>", ph, h, flags=re.S)
    # checkbox list items
    h = re.sub(r"<li>\[ \] ", '<li class="check">', h)
    h = re.sub(r"<li>\[x\] ", '<li class="check done">', h)
    return h

def chapterize(h, guide):
    """Wrap each h2 in a section; chapters get a kicker + page break."""
    parts = re.split(r"(<h2>.*?</h2>)", h, flags=re.S)
    out, toc = [parts[0]], []
    for i in range(1, len(parts), 2):
        title, body = re.sub(r"</?h2>", "", parts[i]), parts[i + 1]
        m = re.match(r"Chapter (\d+) — (.*)", title)
        if guide and m:
            kicker, name, cls = f"CHAPTER {m.group(1)}", m.group(2), "chapter"
        elif guide:
            kicker, name, cls = "SOURCES &amp; CREDITS", re.sub(r"^Credits &amp; Sources$", "Credits &amp; Sources", title), "chapter"
        else:
            kicker, name, cls = "", title, "phase"
        toc.append((kicker, name))
        k = f'<div class="kicker">{kicker}</div>' if kicker else ""
        out.append(f'<section class="{cls}">{k}<h2>{name}</h2>{body}</section>')
    return "".join(out), toc

def cover(logo, kicker, title, subtitle, note):
    return f"""<section class="cover"><div class="cover-inner">
<img class="cover-logo" src="../assets/{logo}">
<div class="gold-rule"></div>
<div class="cover-kicker">{kicker}</div>
<h1>{title}</h1><p class="cover-sub">{subtitle}</p></div>
<div class="cover-foot">{note}</div></section>"""

def back(logo):
    return f"""<section class="back"><img src="../assets/{logo}">
<p class="thanks">Thank you for building with us.</p>
<p class="small">&copy; 2026 Team Smith Homes. All rights reserved.<br>For personal use by the purchaser. Please do not copy or redistribute.</p></section>"""

def render(htmlpath, pdfpath):
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdfpath}", "file://" + htmlpath], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def page_of(pdf, needle):
    for i, p in enumerate(PdfReader(pdf).pages):
        if i < 2: continue  # skip cover + contents
        if needle in " ".join((p.extract_text() or "").split()): return i + 1
    return None

def build(src, name, cfg, guide):
    text = open(os.path.join(ROOT, src)).read()
    text = re.sub(r"^\*©.*$", "", text, flags=re.M)
    notice = ""
    if guide:
        text = text.split("\n---\n", 2)  # [title block, disclaimer, rest]
        notice = md_to_html(text[1])
        text = text[2]
    else:
        text = re.sub(r"^# .*\n", "", text, count=1)  # title lives on the cover
    h, toc = chapterize(md_to_html(text), guide)
    h = h.replace("<hr />", "") if not guide else h.replace("<hr />", "")
    def toc_html(pages):
        rows = []
        for (k, n), pg in zip(toc, pages):
            num = k.title().replace("&Amp;", "&amp;") if k else ""
            rows.append(f'<li><span class="tn">{num}</span><span class="tt">{n}</span><span class="tp">{pg or ""}</span></li>')
        return '<section class="toc"><h2 class="toc-h">Contents</h2><ul>' + "".join(rows) + "</ul>" + (f'<div class="notice">{notice}</div>' if notice else "") + "</section>"
    def doc(pages):
        return (f'<!doctype html><html><head><meta charset="utf-8"><title>{cfg["title"]}</title>'
                f"<style>{FONTS}{CSS}</style></head><body class=\"{cfg['cls']}\">"
                + cover(cfg["logo"], cfg["kicker"], cfg["title"], cfg["subtitle"], cfg["note"])
                + toc_html(pages) + h + back("logo-white.png") + "</body></html>")
    hp = os.path.join(BUILD, name + ".html"); pdf = os.path.join(OUT, name + ".pdf")
    open(hp, "w").write(doc([None] * len(toc))); render(hp, pdf)
    pages = []
    for k, n in toc:
        needle = (k.replace("&amp;", "&") + " " if k else "") + html.unescape(re.sub("<[^>]+>", "", n))
        pages.append(page_of(pdf, needle) or page_of(pdf, html.unescape(re.sub("<[^>]+>", "", n))))
    open(hp, "w").write(doc(pages)); render(hp, pdf)
    print(name, "->", pdf, "pages:", len(PdfReader(pdf).pages), "toc:", pages)

os.makedirs(OUT, exist_ok=True)
build("01-the-15-minute-agent.md", "The-15-Minute-Agent_Team-Smith-Homes", dict(
    title="The 15-Minute Agent", subtitle="AI Prompts &amp; Workflows for Realtors",
    kicker="A TEAM SMITH HOMES GUIDE", logo="logo-white.png", cls="guide",
    note="Copy. Paste. Get your afternoon back. &nbsp;&middot;&nbsp; 2026 Edition"), True)
build("03-marketing-plan.md", "Launch-Playbook_Team-Smith-Homes_INTERNAL", dict(
    title="Launch Playbook", subtitle="A 60-day, step-by-step marketing plan for<br>&ldquo;The 15-Minute Agent&rdquo;",
    kicker="TEAM SMITH HOMES &middot; INTERNAL", logo="logo-white.png", cls="plan",
    note="Internal planning document &mdash; not for sale or distribution"), False)
