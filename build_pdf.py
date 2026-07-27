"""Build a print-ready HTML from the ETAI markdown doc (renders Mermaid diagrams)."""
from pathlib import Path
import html

ROOT = Path(__file__).parent
md_path = ROOT / "ETAI_Project_Document.md"
html_path = ROOT / "ETAI_Project_Document.html"

markdown_text = md_path.read_text(encoding="utf-8")

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>ETAI — AI Intelligence Platform for Data Centre EPC Project Delivery</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
  :root {{ --accent:#1f4e79; --accent2:#2e7d32; --ink:#1a1a1a; --muted:#555; --line:#d0d7de; }}
  * {{ box-sizing:border-box; }}
  body {{
    font-family:"Segoe UI", Calibri, Arial, sans-serif;
    color:var(--ink); line-height:1.55; font-size:11.5pt;
    max-width:900px; margin:0 auto; padding:24px 32px;
  }}
  h1 {{ color:var(--accent); font-size:26pt; border-bottom:3px solid var(--accent); padding-bottom:8px; }}
  h2 {{ color:var(--accent); font-size:17pt; margin-top:1.6em; border-bottom:1px solid var(--line); padding-bottom:4px; }}
  h3 {{ color:var(--accent2); font-size:13pt; margin-top:1.3em; }}
  h4 {{ color:var(--muted); font-size:11.5pt; }}
  blockquote {{
    border-left:4px solid var(--accent); background:#f4f8fc; margin:1em 0;
    padding:10px 16px; color:#243b53; font-style:italic;
  }}
  code {{ background:#f0f3f6; padding:1px 5px; border-radius:4px; font-family:Consolas,"Courier New",monospace; font-size:9.5pt; }}
  pre {{ background:#f6f8fa; border:1px solid var(--line); border-radius:6px; padding:12px; overflow:auto; }}
  pre code {{ background:none; padding:0; font-size:9pt; line-height:1.4; }}
  table {{ border-collapse:collapse; width:100%; margin:1em 0; font-size:10pt; }}
  th, td {{ border:1px solid var(--line); padding:6px 10px; text-align:left; vertical-align:top; }}
  th {{ background:var(--accent); color:#fff; }}
  tr:nth-child(even) td {{ background:#f6f8fa; }}
  a {{ color:var(--accent); text-decoration:none; }}
  hr {{ border:none; border-top:1px solid var(--line); margin:2em 0; }}
  img {{ max-width:100%; height:auto; display:block; margin:1.2em auto; border:1px solid var(--line); border-radius:6px; }}
  .mermaid {{ text-align:center; margin:1.4em 0; }}
  h1,h2,h3 {{ page-break-after:avoid; }}
  table, pre, .mermaid {{ page-break-inside:avoid; }}
</style>
</head>
<body>
<div id="content"></div>
<script type="text/markdown" id="src">
{markdown}
</script>
<script>
  const raw = document.getElementById('src').textContent;
  document.getElementById('content').innerHTML = marked.parse(raw);
  document.querySelectorAll('code.language-mermaid').forEach(function(c) {{
    const div = document.createElement('div');
    div.className = 'mermaid';
    div.textContent = c.textContent;
    c.closest('pre').replaceWith(div);
  }});
  mermaid.initialize({{ startOnLoad:false, theme:'default', securityLevel:'loose' }});
  window.__ready = false;
  mermaid.run().then(function() {{ window.__ready = true; document.title = 'READY_' + document.title; }});
</script>
</body>
</html>
"""

html_out = TEMPLATE.format(markdown=markdown_text)
html_path.write_text(html_out, encoding="utf-8")
print(f"Wrote {html_path}")


def build_pdf():
    """Render the HTML with Playwright (Edge) and print to PDF with a centered page-number footer."""
    from playwright.sync_api import sync_playwright

    pdf_path = ROOT / "ETAI_Project_Document.pdf"
    footer = (
        '<div style="width:100%; text-align:center; font-family:Segoe UI, Arial, sans-serif; '
        'font-size:9px; color:#555;"><span class="pageNumber"></span></div>'
    )
    empty = '<div></div>'

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page()
        page.goto(html_path.as_uri(), wait_until="networkidle")
        try:
            page.wait_for_function("window.__ready === true", timeout=30000)
        except Exception:
            pass  # proceed even if the readiness flag never flips
        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=empty,
            footer_template=footer,
            margin={"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
        )
        browser.close()
    print(f"Wrote {pdf_path} ({pdf_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build_pdf()
