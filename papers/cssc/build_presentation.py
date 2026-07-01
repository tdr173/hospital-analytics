"""
Pipeline: HospitAI_presentation.tex -> PDF -> PPTX
  Step 1 - subprocess runs pdflatex twice (for correct footline page counts)
  Step 2 - pdf2image converts each PDF page to a high-DPI PNG (Poppler backend)
  Step 3 - python-pptx assembles a PPTX with each image as a full-bleed slide
LaTeX formulas are preserved exactly as rendered by pdflatex.
"""

import subprocess
import sys
import io
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────────────
HERE        = Path(__file__).parent.resolve()
TEX_FILE    = HERE / "HospitAI_presentation.tex"
PDF_FILE    = HERE / "HospitAI_presentation.pdf"
PPTX_FILE   = HERE / "HospitAI_presentation.pptx"

PDFLATEX    = Path(r"C:\Users\rczxc\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe")
POPPLER_BIN = Path(r"C:\Users\rczxc\AppData\Local\Microsoft\WinGet\Packages"
                   r"\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe"
                   r"\poppler-25.07.0\Library\bin")

DPI = 220   # 220 dpi → ~2413×1357 px for a 16:9 slide; crisp on any monitor


# ── Step 1: LaTeX → PDF ──────────────────────────────────────────────────────
def latex_to_pdf() -> None:
    print("=== Step 1: LaTeX -> PDF ===")
    cmd = [
        str(PDFLATEX),
        "-interaction=nonstopmode",
        "-output-directory", str(HERE),
        str(TEX_FILE),
    ]
    for run in range(1, 3):
        print(f"  pdflatex pass {run}/2 …")
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(HERE))
        if result.returncode != 0:
            # Print last 30 lines of stdout so the user can diagnose
            lines = result.stdout.splitlines()
            print("\n".join(lines[-30:]))
            sys.exit(f"pdflatex pass {run} failed (exit {result.returncode})")
    if not PDF_FILE.exists():
        sys.exit("PDF was not produced — check the .log file for errors.")
    print(f"  PDF written: {PDF_FILE}")


# ── Step 2: PDF → images ─────────────────────────────────────────────────────
def pdf_to_images(dpi: int = DPI) -> list:
    from pdf2image import convert_from_path
    print(f"\n=== Step 2: PDF -> images ({dpi} DPI) ===")
    pages = convert_from_path(
        str(PDF_FILE),
        dpi=dpi,
        poppler_path=str(POPPLER_BIN),
        fmt="png",
        thread_count=4,
    )
    print(f"  {len(pages)} page(s) converted")
    return pages


# ── Step 3: images → PPTX ───────────────────────────────────────────────────
def images_to_pptx(pages: list) -> None:
    from pptx import Presentation
    from pptx.util import Emu

    print(f"\n=== Step 3: images -> PPTX ===")

    prs = Presentation()

    # Derive slide dimensions from the first image's pixel size and the DPI
    # so the aspect ratio is exactly 16:9 (matching the Beamer aspectratio=169).
    first = pages[0]
    px_w, px_h = first.size                        # pixels
    emu_per_px  = int(914400 / DPI)               # 914400 EMU = 1 inch
    slide_w     = Emu(px_w * emu_per_px)
    slide_h     = Emu(px_h * emu_per_px)
    prs.slide_width  = slide_w
    prs.slide_height = slide_h

    blank_layout = prs.slide_layouts[6]            # fully blank layout

    for i, img in enumerate(pages, start=1):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        slide = prs.slides.add_slide(blank_layout)
        slide.shapes.add_picture(
            buf,
            left=Emu(0), top=Emu(0),
            width=slide_w, height=slide_h,
        )
        print(f"  Slide {i}/{len(pages)}")

    prs.save(str(PPTX_FILE))
    print(f"\n  PPTX written: {PPTX_FILE}")


# ── main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    latex_to_pdf()
    pages = pdf_to_images()
    images_to_pptx(pages)
    print("\nDone.")
