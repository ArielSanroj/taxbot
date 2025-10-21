from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

try:
    import ollama  # type: ignore
except ImportError:  # pragma: no cover
    ollama = None


BASE_URL = "https://cijuf.org.co"
LIST_URL = "https://cijuf.org.co/normatividad/conceptos-y-oficios-dian/2025"

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "conceptos_dian.csv"
LOG_PATH = DATA_DIR / "dian_pipeline.log"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
EMAIL_SENDER = os.getenv("DIAN_EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("DIAN_EMAIL_PASSWORD")
EMAIL_RECIPIENTS = [addr.strip() for addr in os.getenv("DIAN_EMAIL_RECIPIENTS", "").split(",") if addr.strip()]


def configure_logging() -> None:
    if logging.getLogger().handlers:
        return
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[file_handler, stream_handler])


configure_logging()
session = requests.Session()
session.headers.update({"User-Agent": "taxbot/1.0"})


@dataclass
class Concept:
    title: str
    date: datetime
    theme: str
    descriptor: str
    link: str
    full_text: str
    summary: Optional[str] = None
    analysis: Optional[str] = None

    def to_record(self) -> dict[str, str]:
        return {
            "title": self.title,
            "date": self.date.strftime("%Y-%m-%d"),
            "theme": self.theme,
            "descriptor": self.descriptor,
            "link": self.link,
            "summary": self.summary or "",
            "analysis": self.analysis or "",
        }


def clean_text(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())


def fetch_soup(url: str) -> BeautifulSoup:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def discover_month_links() -> List[str]:
    try:
        soup = fetch_soup(LIST_URL)
    except Exception as exc:  # pragma: no cover
        logging.error("No se pudo obtener el índice %s: %s", LIST_URL, exc)
        return []
    anchors = soup.select("div.view-content a.btn")
    if not anchors:
        return [LIST_URL]
    links = []
    for anchor in anchors:
        href = anchor.get("href")
        if not href:
            continue
        links.append(urljoin(BASE_URL, href))
    return links


def parse_month(url: str) -> List[Concept]:
    try:
        soup = fetch_soup(url)
    except Exception as exc:
        logging.error("No se pudo procesar el mes %s: %s", url, exc)
        return []
    rows = soup.select("table.table tbody tr")
    concepts: List[Concept] = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        anchor = cells[0].find("a")
        if not anchor or not anchor.get("href"):
            continue
        title = clean_text(anchor.get_text(strip=True))
        link = urljoin(BASE_URL, anchor["href"])
        date_text = clean_text(cells[0].find("time").get_text()) if cells[0].find("time") else ""
        date = parse_date(date_text) or datetime.utcnow()
        theme, descriptor = extract_theme_descriptor(cells[1])
        full_text = fetch_full_text(link)
        concepts.append(Concept(title=title, date=date, theme=theme, descriptor=descriptor, link=link, full_text=full_text))
    return concepts


def parse_date(value: str) -> Optional[datetime]:
    formats = ("%d/%m/%Y", "%Y-%m-%d")
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def extract_theme_descriptor(cell: BeautifulSoup) -> tuple[str, str]:
    paragraphs = [clean_text(p.get_text(" ", strip=True)) for p in cell.find_all("p") if p.get_text(strip=True)]
    theme = "Sin tema"
    descriptor_parts: List[str] = []
    for text in paragraphs:
        lower = text.lower()
        if "tema" in lower:
            candidate = strip_label(text, "tema")
            if candidate:
                theme = candidate
        elif "descriptor" in lower:
            candidate = strip_label(text, "descriptor")
            if candidate:
                descriptor_parts.append(candidate)
        else:
            descriptor_parts.append(text)
    descriptor = " ".join(part for part in descriptor_parts if part).strip()
    return theme, descriptor


def strip_label(text: str, label: str) -> str:
    lower = text.lower()
    idx = lower.find(label)
    if idx == -1:
        return clean_text(text)
    remaining = text[idx + len(label) :]
    remaining = remaining.lstrip(": ")
    return clean_text(remaining)


def fetch_full_text(url: str) -> str:
    try:
        soup = fetch_soup(url)
    except Exception as exc:
        logging.error("No se pudo obtener el detalle %s: %s", url, exc)
        return ""
    container = soup.select_one("div.field--name-body") or soup.select_one("div.region-content")
    if not container:
        return ""
    return clean_text(container.get_text(" ", strip=True))


def summarize_text(text: str) -> str:
    if not text:
        return "No hay contenido para resumir."
    if ollama is None:
        logging.warning("Ollama no está disponible.")
        return "Resumen no disponible: Ollama no configurado."
    prompt = (
        "Eres un abogado tributarista. Resume el siguiente concepto de la DIAN en un máximo de 6 frases, "
        "destacando implicaciones prácticas, cambios normativos, obligaciones y recomendaciones para clientes. "
        "Texto: " + text
    )
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        return clean_text(response["message"]["content"])
    except Exception as exc:  # pragma: no cover
        logging.error("Error al resumir con Ollama: %s", exc)
        return "Resumen no disponible por error en Ollama."


def complementary_analysis(summary: str, concept: Concept) -> str:
    if not summary:
        return "Análisis no disponible."
    if ollama is None:
        return "Análisis no disponible: Ollama no configurado."
    prompt = (
        "Actúa como consultor tributario sénior. Con base en el siguiente resumen y la información del concepto, "
        "identifica riesgos, oportunidades, acciones sugeridas y normas relacionadas. \nResumen: "
        + summary
        + "\nTema: "
        + concept.theme
        + "\nDescriptor: "
        + concept.descriptor
    )
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
        return clean_text(response["message"]["content"])
    except Exception as exc:  # pragma: no cover
        logging.error("Error en análisis complementario: %s", exc)
        return "Análisis no disponible por error en Ollama."


def process_concepts(concepts: Iterable[Concept]) -> List[Concept]:
    processed: List[Concept] = []
    for concept in concepts:
        concept.summary = summarize_text(concept.full_text[:12000])
        concept.analysis = complementary_analysis(concept.summary, concept)
        processed.append(concept)
    return processed


def load_existing_records() -> pd.DataFrame:
    if not CSV_PATH.exists():
        return pd.DataFrame(columns=["title", "date", "theme", "descriptor", "link", "summary", "analysis"])
    try:
        return pd.read_csv(CSV_PATH)
    except Exception as exc:
        logging.error("No se pudo leer %s: %s", CSV_PATH, exc)
        return pd.DataFrame(columns=["title", "date", "theme", "descriptor", "link", "summary", "analysis"])


def merge_records(existing: pd.DataFrame, new_records: List[Concept]) -> pd.DataFrame:
    new_df = pd.DataFrame([concept.to_record() for concept in new_records])
    if existing.empty:
        combined = new_df
    else:
        combined = pd.concat([existing, new_df], ignore_index=True)
    combined.drop_duplicates(subset=["link"], keep="last", inplace=True)
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce")
    combined.sort_values(["theme", "date"], ascending=[True, False], inplace=True)
    combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")
    combined.fillna("", inplace=True)
    return combined


def send_email(csv_path: Path, new_concepts: List[Concept]) -> None:
    if not new_concepts:
        logging.info("Sin conceptos nuevos, no se envía correo.")
        return
    if not (EMAIL_SENDER and EMAIL_PASSWORD and EMAIL_RECIPIENTS):
        logging.warning("Configuración de correo incompleta, se omite el envío.")
        return
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECIPIENTS)
    msg["Subject"] = f"Conceptos DIAN actualizados - {datetime.utcnow().strftime('%Y-%m-%d')}"
    lines = [
        "Resumen de nuevos conceptos DIAN:",
        *(
            f"- {concept.date.strftime('%Y-%m-%d')} | {concept.theme} | {concept.title}"
            for concept in new_concepts
        ),
        "",
        "Se adjunta archivo con detalles, resúmenes y análisis.",
    ]
    msg.attach(MIMEText("\n".join(lines), "plain"))
    with open(csv_path, "rb") as handle:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(handle.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={csv_path.name}")
        msg.attach(part)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())
        logging.info("Correo enviado a %s", EMAIL_RECIPIENTS)
    except Exception as exc:  # pragma: no cover
        logging.error("No se pudo enviar el correo: %s", exc)


def collect_concepts() -> List[Concept]:
    months = discover_month_links()
    if not months:
        logging.info("No se encontraron enlaces de meses para procesar.")
        return []
    concepts: List[Concept] = []
    seen_links: set[str] = set()
    for month_url in months:
        for concept in parse_month(month_url):
            if concept.link in seen_links:
                continue
            seen_links.add(concept.link)
            concepts.append(concept)
    return concepts


def main() -> None:
    scraped = collect_concepts()
    if not scraped:
        logging.info("No se encontraron conceptos para procesar.")
        return
    existing = load_existing_records()
    existing_links = set(existing["link"].dropna()) if not existing.empty else set()
    fresh = [concept for concept in scraped if concept.link not in existing_links]
    if not fresh:
        logging.info("No hay conceptos nuevos.")
        return
    processed = process_concepts(fresh)
    combined = merge_records(existing, processed)
    combined.to_csv(CSV_PATH, index=False)
    logging.info("Archivo actualizado en %s con %s registros.", CSV_PATH, len(combined))
    send_email(CSV_PATH, processed)


if __name__ == "__main__":
    main()
