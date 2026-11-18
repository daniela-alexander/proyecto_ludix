import os
import json
import time
import ssl
import urllib.request
import urllib.parse
import polib

ssl._create_default_https_context = ssl._create_unverified_context

ARCHIVOS_JSON = []
for raiz, carpetas, archivos in os.walk('.'):
    carpetas[:] = [c for c in carpetas if not c.startswith('.') and c not in ('venv', 'env', 'node_modules')]
    for archivo in archivos:
        if archivo.endswith('.json') and archivo not in ('package.json', 'package-lock.json'):
            ARCHIVOS_JSON.append(os.path.join(raiz, archivo))

CAMPOS_A_TRADUCIR = [
    'categoria', 'subcategoria', 'pais_procedencia',
    'numero_jugadores', 'tiempo_estimado', 'descripcion',
    'instrucciones', 'creador'
]

IDIOMAS = {'en': 'en', 'it': 'it', 'ca': 'ca'}

def traducir_google_directo(texto, idioma_destino):
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=es&tl={idioma_destino}&dt=t&q={urllib.parse.quote(texto)}"
    )
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return "".join(parte[0] for parte in data[0] if parte[0])

textos_unicos = set()
for archivo in ARCHIVOS_JSON:
    with open(archivo, 'r', encoding='utf-8') as f:
        datos = json.load(f)
        if isinstance(datos, list):
            for item in datos:
                if isinstance(item, dict):
                    for campo in CAMPOS_A_TRADUCIR:
                        valor = item.get(campo)
                        if valor and isinstance(valor, str) and valor.strip():
                            textos_unicos.add(valor.strip())

with open('locale/json_strings.py', 'w', encoding='utf-8') as f:
    f.write("from django.utils.translation import gettext_lazy as _\n\n")
    for texto in sorted(textos_unicos):
        f.write(f"_({repr(texto)})\n")

print(f"Total de textos únicos: {len(textos_unicos)}")

SEPARADOR = "\n|||\n"

for carpeta, codigo in IDIOMAS.items():
    ruta_po = f'locale/{carpeta}/LC_MESSAGES/django.po'
    po = polib.pofile(ruta_po)
    existentes = {entry.msgid: entry for entry in po}

    pendientes = [t for t in textos_unicos if not (t in existentes and existentes[t].msgstr)]
    print(f"\n[{carpeta}] Faltan {len(pendientes)} textos por traducir...")

    lote_actual = []
    caracteres_actuales = 0
    procesados = 0

    for idx, texto in enumerate(pendientes):
        lote_actual.append(texto)
        caracteres_actuales += len(texto) + len(SEPARADOR)

        es_ultimo = (idx == len(pendientes) - 1)
        if caracteres_actuales >= 2500 or es_ultimo:
            bloque_unido = SEPARADOR.join(lote_actual)
            try:
                resultado_unido = traducir_google_directo(bloque_unido, codigo)
                traducciones = [t.strip() for t in resultado_unido.split("|||")]

                if len(traducciones) == len(lote_actual):
                    for orig, trad in zip(lote_actual, traducciones):
                        if orig in existentes:
                            existentes[orig].msgstr = trad
                        else:
                            po.append(polib.POEntry(msgid=orig, msgstr=trad))
                else:
                    for orig in lote_actual:
                        trad = traducir_google_directo(orig, codigo)
                        if orig in existentes:
                            existentes[orig].msgstr = trad
                        else:
                            po.append(polib.POEntry(msgid=orig, msgstr=trad))
                        time.sleep(0.4)

                po.save(ruta_po)
                procesados += len(lote_actual)
                print(f"[{carpeta}] Guardados {procesados}/{len(pendientes)}")

                lote_actual = []
                caracteres_actuales = 0
                time.sleep(1.5)

            except Exception as e:
                print(f"❌ Error detenido: {e}")
                break

print("\n🎉 ¡Proceso finalizado!")