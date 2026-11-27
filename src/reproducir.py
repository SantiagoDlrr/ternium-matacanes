"""Un solo comando regenera todas las figuras y tablas del artículo final.

    python -m src.reproducir            # notebooks 07–10 + sincroniza articulo/
    python -m src.reproducir --todo     # además 01–06 (Entrega I)
    python -m src.reproducir --pdf      # además compila articulo/main.pdf (requiere LaTeX)
    python -m src.reproducir --solo-articulo   # solo sincroniza y compila, sin re-ejecutar notebooks

Pasos:
1. Ejecuta los notebooks en orden, en su lugar (las salidas agregadas quedan guardadas).
2. Convierte ``outputs/tablas/cifras.json`` en macros LaTeX (``articulo/generado/cifras.tex``):
   cada número del texto sale del código, no se copia a mano.
3. Copia las figuras (PDF) y las tablas LaTeX a ``articulo/`` para que la carpeta sea
   autocontenida (se puede subir tal cual a Overleaf).
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

from .config import FIGURAS_DIR, REPO_ROOT, TABLAS_DIR

NB_DIR = REPO_ROOT / "notebooks"
ARTICULO = REPO_ROOT / "articulo"
NB_ENTREGA1 = ["01_carga_y_auditoria", "02_diccionario_y_poblacion", "03_fenomeno1_etiquetas_de_calidad",
               "04_fenomeno2_asignacion_de_consignas", "05_fenomeno6_calidad_del_dato", "06_pregunta_y_evidencia"]
NB_FINAL = ["07_union_mc4_skinpass", "08_soporte_y_resultado_principal", "09_validacion_y_robustez",
            "10_modelo_predictivo"]


def ejecutar(nombre: str) -> None:
    print(f"→ ejecutando {nombre}.ipynb", flush=True)
    subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
                    "--ExecutePreprocessor.timeout=3600", f"{nombre}.ipynb"], check=True, cwd=NB_DIR)


def _escapar(v: str) -> str:
    return (v.replace("\\", r"\textbackslash{}").replace("%", r"\%").replace("&", r"\&")
            .replace("#", r"\#").replace("_", r"\_"))


def macros() -> None:
    cifras = json.loads((TABLAS_DIR / "cifras.json").read_text())
    lineas = ["% Generado por python -m src.reproducir a partir de outputs/tablas/cifras.json. No editar a mano."]
    for k, v in sorted(cifras.items()):
        lineas.append(f"\\newcommand{{\\{k}}}{{{_escapar(v)}}}")
    destino = ARTICULO / "generado" / "cifras.tex"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(lineas) + "\n")
    print(f"→ {len(cifras)} macros en {destino.relative_to(REPO_ROOT)}")


def sincronizar() -> None:
    (ARTICULO / "figuras").mkdir(parents=True, exist_ok=True)
    (ARTICULO / "generado").mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted((FIGURAS_DIR / "articulo").glob("*.pdf")):
        shutil.copy2(f, ARTICULO / "figuras" / f.name)
        n += 1
    for f in sorted(TABLAS_DIR.glob("tabla_*.tex")):
        shutil.copy2(f, ARTICULO / "generado" / f.name)
        n += 1
    print(f"→ {n} figuras y tablas copiadas a articulo/")


def compilar() -> None:
    print("→ compilando articulo/main.tex", flush=True)
    subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                   check=True, cwd=ARTICULO, stdout=subprocess.DEVNULL)
    print(f"→ {ARTICULO / 'main.pdf'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--todo", action="store_true", help="incluye los notebooks 01–06 de la Entrega I")
    ap.add_argument("--pdf", action="store_true", help="compila el artículo con latexmk")
    ap.add_argument("--solo-articulo", action="store_true", help="no re-ejecuta notebooks")
    args = ap.parse_args()
    if not args.solo_articulo:
        cifras = TABLAS_DIR / "cifras.json"
        if cifras.exists():
            cifras.unlink()  # se regenera completo: ninguna cifra vieja sobrevive
        for nb in (NB_ENTREGA1 if args.todo else []) + NB_FINAL:
            ejecutar(nb)
    macros()
    sincronizar()
    if args.pdf:
        compilar()


if __name__ == "__main__":
    main()
