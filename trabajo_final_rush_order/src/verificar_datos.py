# -*- coding: utf-8 -*-
"""Verificacion de la transcripcion de datos: compara DATA (scheduler_ga.py) contra
las Tablas 5 y 6 extraidas directamente del PDF del paper base (auditoria E7).

Uso: python verificar_datos.py   (requiere pypdf y el PDF en la raiz del repositorio)
"""
import os
import re

from pypdf import PdfReader
from scheduler_ga import DATA

try:
    _here = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _here = os.getcwd()
PDF = os.path.normpath(os.path.join(_here, "..", "..", "sustainability-14-05340-v2.pdf"))


def parse(block):
    rows = {}
    for line in block.splitlines():
        m = re.match(r"\s*J(\d)\s", line)
        if m:
            rows[int(m.group(1))] = [
                [int(x) for x in g.split(",")] for g in re.findall(r"\[([\d,]+)\]", line)]
    return rows


def main():
    txt = PdfReader(PDF).pages[12].extract_text()
    maqs = parse(txt.split("Table 5.")[1].split("Table 6.")[0])
    tiempos = parse(txt.split("Table 6.")[1].split("Table 7.")[0])
    errores = 0
    for j in range(1, 9):
        assert len(maqs[j]) == 5 and len(tiempos[j]) == 5, f"J{j}: faltan operaciones"
        for h in range(1, 6):
            esperado = sorted(zip(maqs[j][h - 1], tiempos[j][h - 1]))
            if esperado != sorted(DATA[(j, h)]):
                errores += 1
                print(f"DISCREPANCIA J{j} O{h}: PDF={esperado} DATA={sorted(DATA[(j, h)])}")
    print("pares verificados:", sum(len(v) for v in DATA.values()))
    assert errores == 0, f"{errores} discrepancias con el paper"
    print("OK: transcripcion identica a las Tablas 5 y 6 del paper")


if __name__ == "__main__":
    main()
