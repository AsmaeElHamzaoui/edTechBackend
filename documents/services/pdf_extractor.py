import pymupdf
import pytesseract
from pdf2image import convert_from_path
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path):
    """
    Extrait le texte d'un PDF page par page.
    Retourne une liste de tuples : [(page_number, text), ...]
    Utilise OCR si le texte natif est insuffisant.
    """
    document = pymupdf.open(file_path)
    pages = []

    for page_num, page in enumerate(document, start=1):
        text = page.get_text()
        pages.append((page_num, text))

    document.close()

    # Vérifier si le texte global est exploitable
    total_text = "".join(t for _, t in pages)

    if len(total_text.strip()) < 50:
        logger.info("Text extraction yielded little text. Attempting OCR...")
        pages = []
        try:
            images = convert_from_path(file_path)
            for page_num, image in enumerate(images, start=1):
                text = pytesseract.image_to_string(image, lang='fra+eng')
                pages.append((page_num, text))
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise ValueError(f"Échec de l'OCR: {e}")

    total_text = "".join(t for _, t in pages)
    if len(total_text.strip()) == 0:
        raise ValueError("Le document ne contient aucun texte lisible ou l'OCR a échoué.")

    return pages


def extract_text_flat(file_path):
    """Retourne le texte complet aplati (pour rétrocompatibilité)."""
    pages = extract_text_from_pdf(file_path)
    return "\n".join(text for _, text in pages)