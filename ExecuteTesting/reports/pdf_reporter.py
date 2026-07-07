from pathlib import Path

from utilities.logger import get_logger

log = get_logger(test="PDFReporter")


def generate_pdf(html_path: str, output_folder: str) -> str:
    Path(output_folder).mkdir(parents=True, exist_ok=True)
    pdf_path = str(Path(html_path).with_suffix(".pdf"))

    try:
        from weasyprint import HTML
        HTML(filename=html_path).write_pdf(pdf_path)
        log.info(f"PDF report: {pdf_path}")
    except ImportError:
        log.warning("WeasyPrint not available. Install with: pip install weasyprint")
        _fallback_pdf(html_path, pdf_path)
    except Exception as e:
        log.error(f"PDF generation failed: {e}")
        pdf_path = ""

    return pdf_path


def _fallback_pdf(html_path: str, pdf_path: str) -> None:
    """Minimal fallback: copy HTML with .pdf extension and note the limitation."""
    import shutil
    shutil.copy(html_path, pdf_path.replace(".pdf", "_report.html"))
    log.info("Fallback: saved HTML copy. Install WeasyPrint for true PDF.")
