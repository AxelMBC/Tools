#!/usr/bin/env python3
"""
pdf2kindle.py - Convierte un PDF "de clase" (texto principal + columna lateral,
encabezados y pies de pagina) en un MOBI limpio para Kindle.

Que hace:
  1. Se queda solo con la columna principal (descarta lo que esta a la izquierda).
  2. Tira encabezados y pies de pagina.
  3. Quita superindices (numeritos de notas al pie).
  4. Une los renglones en parrafos reales y repara parrafos cortados entre paginas.
  5. Genera HTML y lo convierte a MOBI con Calibre.

Requisitos:
  pip install pymupdf
  Calibre instalado (trae el comando ebook-convert). En Windows suele estar en
  "C:\\Program Files\\Calibre2\\ebook-convert.exe".

Uso:
    python pdf2kindle.py archivo.pdf "Titulo" "Autor"
    python pdf2kindle.py archivo.pdf "Titulo" "Autor" --cover portada.jpg
    python pdf2kindle.py archivo.pdf "Titulo" "Autor" --cover portada.jpg --azw3

  --cover   imagen JPG o PNG para la portada (idealmente vertical, 1600x2560)
  --azw3    genera AZW3 en vez de MOBI

Ejemplo:
    python pdf2kindle.py la-casa-de-asterion-borges.pdf "La casa de Asterión" "Jorge Luis Borges" --cover LaCasaDeAsterionPortada.jpg

    Si se cuela basura o se corta texto, ajusta MIN_X (que tan a la izquierda empieza
la columna principal, como fraccion del ancho) y MARGIN (encabezado/pie).
"""
import re
import shutil
import statistics
import argparse
import subprocess
import sys
from html import escape
from pathlib import Path

import pymupdf as fitz

MIN_X = 0.20    # texto que empieza antes del 20% del ancho = columna lateral
MARGIN = 0.07   # 7% arriba y abajo = zona de encabezado / pie de pagina
END_PUNCT = re.compile(r'[.!?»"”:;)]$')
PRINTABLE = re.compile(r"[\x00-\x1f]")


def collect_lines(doc, body_size):
    """Devuelve renglones visuales de la columna principal: (pagina, y, x0, x1, texto)."""
    out = []
    for pn, page in enumerate(doc):
        W, H = page.rect.width, page.rect.height
        spans = []
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    t = s["text"]
                    x0, y0, x1, y1 = s["bbox"]
                    if not t.strip() or PRINTABLE.search(t):
                        continue                      # vacios o glifos basura
                    # superindice (notas al pie)
                    if s["flags"] & 1:
                        continue
                    if s["size"] < body_size * 0.9:   # encabezados, pies, notas
                        continue
                    if x0 < W * MIN_X or y0 < H * MARGIN or y1 > H * (1 - MARGIN):
                        continue
                    spans.append((y1, x0, x1, t))
        # Agrupa spans que comparten renglon (misma linea base, +-2 pt)
        spans.sort()
        line = []
        for sp in spans:
            if line and abs(sp[0] - line[0][0]) > 2:
                out.append(_mk(pn, line, W))
                line = []
            line.append(sp)
        if line:
            out.append(_mk(pn, line, W))
    return out


def _mk(pn, spans, W):
    spans.sort(key=lambda s: s[1])
    text = re.sub(r"\s+", " ", "".join(s[3] for s in spans)).strip()
    return pn, spans[0][0], spans[0][1] / W, max(s[2] for s in spans) / W, text


def extract_paragraphs(pdf_path):
    doc = fitz.open(pdf_path)
    sizes = [s["size"] for p in doc for b in p.get_text("dict")["blocks"]
             for l in b.get("lines", []) for s in l["spans"]
             if s["text"].strip() and not PRINTABLE.search(s["text"])]
    body_size = statistics.median(sizes)

    lines = collect_lines(doc, body_size)
    if not lines:
        return []
    left = min(l[2] for l in lines)
    right = max(l[3] for l in lines)
    pitches = [b[1] - a[1]
               for a, b in zip(lines, lines[1:]) if a[0] == b[0] and b[1] > a[1]]
    pitch = statistics.median(pitches) if pitches else body_size * 1.5

    paras, prev = [], None
    for ln in lines:
        pn, y, x0, x1, text = ln
        new_para = prev is None
        if prev:
            same_page = pn == prev[0]
            if not same_page and not END_PUNCT.search(prev[4]):
                new_para = False                      # parrafo partido entre paginas
            elif same_page and y - prev[1] > pitch * 1.4:
                new_para = True                       # hueco vertical = parrafo nuevo
            elif x0 > left + 0.04:
                new_para = True                       # sangria o texto alineado a la derecha
            elif prev[3] < right - 0.12:
                new_para = True                       # renglon anterior corto = fin de parrafo
        if new_para:
            paras.append(text)
        elif paras[-1].endswith("-") and not paras[-1].endswith(" -"):
            # palabra partida con guion
            paras[-1] = paras[-1][:-1] + text
        else:
            paras[-1] += " " + text
        prev = ln
    return paras


def find_ebook_convert():
    exe = shutil.which("ebook-convert")
    if exe:
        return exe
    for c in [r"C:\Program Files\Calibre2\ebook-convert.exe",
              r"C:\Program Files (x86)\Calibre2\ebook-convert.exe",
              "/Applications/calibre.app/Contents/MacOS/ebook-convert"]:
        if Path(c).exists():
            return c
    sys.exit("No encontre ebook-convert. Instala Calibre: https://calibre-ebook.com")


def main():
    ap = argparse.ArgumentParser(
        description="PDF de clase -> MOBI/AZW3 limpio para Kindle")
    ap.add_argument("pdf", help="PDF de entrada")
    ap.add_argument("title", help="Titulo del libro")
    ap.add_argument("author", help="Autor")
    ap.add_argument("--cover", help="Imagen de portada (JPG o PNG)")
    ap.add_argument("--azw3", action="store_true",
                    help="Generar AZW3 en vez de MOBI")
    args = ap.parse_args()

    if args.cover and not Path(args.cover).is_file():
        sys.exit(f"No encontre la portada: {args.cover}")
    ext = ".azw3" if args.azw3 else ".mobi"

    paras = extract_paragraphs(args.pdf)
    body = "\n".join(f"<p>{escape(p)}</p>" for p in paras)
    html_doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>{escape(args.title)}</title></head>
<body><h1>{escape(args.title)}</h1>
{body}
</body></html>"""

    out_html = Path(args.pdf).with_suffix(".clean.html")
    out_html.write_text(html_doc, encoding="utf-8")
    out_book = Path(args.pdf).with_suffix(ext)

    cmd = [find_ebook_convert(), str(out_html), str(out_book),
           "--title", args.title, "--authors", args.author, "--language", "es"]
    if args.cover:
        cmd += ["--cover", str(Path(args.cover).resolve())]
    if ext == ".mobi":
        # Marca el archivo como libro (EBOK) en vez de documento personal (PDOC),
        # para que el Kindle muestre la portada en la pantalla de bloqueo.
        cmd.append("--share-not-sync")
    subprocess.run(cmd, check=True)
    print(f"\nListo: {out_book}  ({len(paras)} parrafos)")
    print("Revisa el .clean.html si algo se ve raro; puedes editarlo y volver a correr.")


if __name__ == "__main__":
    main()
