# -*- coding: utf-8 -*-
"""
Cerebro del canal HISTORIA (formato viral basado en datos reales de lo que
mas visitas consigue en Shorts de historia/curiosidades):
  - Titulo con NUMERO + palabra potente ("3 datos alucinantes", "que no creeras").
  - Gancho fuerte en la primera linea (primeros 2 segundos).
  - Lista de 3-4 datos historicos impactantes.
  - Cebo de comentarios al final (dispara el algoritmo).
Cada dia se ASIGNA un tema/epoca y un formato distinto (rotacion determinista),
para que nunca se repita. Devuelve el mismo dict que usa generate.py.
"""
import os, sys, json, datetime, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("GEMINI_MODEL", "").strip()
_MODEL_CANDIDATES = [
    "gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash",
    "gemini-2.5-flash-lite", "gemini-2.0-flash-001", "gemini-1.5-flash",
]
BGS = ["blue", "green", "orange", "purple", "teal", "red"]

# Temas/epocas concretas y con imagen potente (rotan por dia). El 2o valor es
# una pista EN INGLES para buscar imagenes reales de archivo.
TEMAS = [
    ("el Antiguo Egipto y los faraones", "ancient egypt pharaoh"),
    ("la Antigua Roma y los gladiadores", "ancient rome gladiator colosseum"),
    ("la Antigua Grecia", "ancient greece parthenon"),
    ("la Segunda Guerra Mundial", "world war 2 historical photo"),
    ("la Edad Media", "medieval knight castle"),
    ("los vikingos", "viking warrior ship"),
    ("el Antiguo Japon y los samurais", "samurai ancient japan"),
    ("la Peste Negra", "black death plague medieval"),
    ("el Imperio Azteca", "aztec empire temple"),
    ("los mayas", "maya civilization pyramid"),
    ("el Imperio Mongol y Gengis Kan", "mongol empire genghis khan"),
    ("la Revolucion Francesa", "french revolution painting"),
    ("el hundimiento del Titanic", "titanic ship 1912"),
    ("la Guerra Fria", "cold war 1960s"),
    ("el Salvaje Oeste americano", "wild west cowboy 1800s"),
    ("los piratas", "pirate ship golden age"),
    ("la Inquisicion", "inquisition medieval"),
    ("las momias y el mas alla", "egyptian mummy tomb"),
    ("los castigos y ejecuciones antiguas", "medieval punishment history"),
    ("la medicina antigua", "ancient medicine history"),
    ("los grandes inventos de la historia", "historic invention old"),
    ("las batallas mas legendarias", "historic battle painting"),
    ("reyes y reinas polemicos", "royal king queen portrait history"),
    ("la carrera espacial", "space race 1969 apollo"),
    ("las civilizaciones perdidas", "lost ancient civilization ruins"),
    ("los faraones y sus tesoros", "tutankhamun treasure gold"),
    ("la comida a lo largo de la historia", "historic food banquet painting"),
    ("los castillos y fortalezas", "medieval castle fortress"),
    ("Napoleon y su imperio", "napoleon bonaparte painting"),
    ("el Imperio Romano en su caida", "fall of rome ruins"),
]

# Formatos ganadores (rotan). Cada uno define como se estructura el guion.
FORMATOS = [
    "LISTA DE 3: tres datos historicos alucinantes y poco conocidos sobre el tema, del mas normal al mas fuerte.",
    "LISTA DE 4: cuatro datos rapidos y sorprendentes sobre el tema, ritmo agil.",
    "UN DATO BRUTAL: un solo hecho historico impactante sobre el tema, contado como una mini-historia con giro.",
    "LO QUE NO TE ENSENARON: 3 cosas que pasaban de verdad y que en el colegio no te contaron sobre el tema.",
    "COSTUMBRES INCREIBLES: 3 costumbres o practicas reales del tema que hoy nos parecerian una locura.",
]

GANCHOS = [
    "El noventa por ciento de la gente no sabe esto.",
    "Esto que hacian te va a dejar sin palabras.",
    "Prepara la cabeza, porque esto es real.",
    "Nadie te conto esto en el colegio.",
    "El ultimo dato te va a explotar la cabeza.",
    "Esto de verdad paso, aunque no lo parezca.",
    "Agarrate, que esto es historia real.",
]

CTAS = [
    "Cual te ha sorprendido mas? Dimelo en los comentarios.",
    "Sabias alguno? Comenta el numero.",
    "Cual no te esperabas? Te leo abajo.",
    "Comenta si quieres la parte dos.",
    "Guarda esto para no olvidarlo y sigue para mas historia.",
]

POWER = ("alucinante", "increible", "no creeras", "no vas a creer", "brutal",
         "impactante", "jamas", "nadie sabe", "prohibid", "oscuro", "escalofriante",
         "que cambio la historia", "que no te ensenaron", "sorprendente")


def _run_seed():
    try:
        return int(os.environ.get("GITHUB_RUN_NUMBER", "0"))
    except ValueError:
        return 0

def _daykey():
    return datetime.date.today().toordinal() + _run_seed()

def _rot(lst, stride):
    return lst[(_daykey() * stride) % len(lst)]


def _list_models(key):
    try:
        url = ("https://generativelanguage.googleapis.com/v1beta/models"
               f"?key={key}&pageSize=200")
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read().decode())
        return [m.get("name", "").replace("models/", "") for m in data.get("models", [])
                if "generateContent" in (m.get("supportedGenerationMethods") or [])]
    except Exception:
        return []

def _model_order(key):
    order = []
    if MODEL:
        order.append(MODEL)
    for m in _MODEL_CANDIDATES:
        if m not in order:
            order.append(m)
    disc = _list_models(key)
    # Prioriza Gemini 'flash', luego otros Gemini, luego el resto.
    # Los 'gemma' (no dan JSON fiable) van al final.
    for m in disc:
        if "gemini" in m and "flash" in m and m not in order:
            order.append(m)
    for m in disc:
        if "gemini" in m and m not in order:
            order.append(m)
    for m in disc:
        if "gemma" not in m and m not in order:
            order.append(m)
    for m in disc:
        if m not in order:
            order.append(m)
    return order

def _post_generate(model, prompt, key):
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={key}")
    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 1.0, "responseMimeType": "application/json"},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode())
    return data["candidates"][0]["content"]["parts"][0]["text"]

def _extract_json(txt):
    """Saca un JSON valido aunque el modelo lo envuelva en ```json ... ``` o texto."""
    if not txt:
        return None
    t = txt.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t[:4].lower() == "json":
            t = t[4:]
    i, j = t.find("{"), t.rfind("}")
    if i != -1 and j != -1 and j > i:
        t = t[i:j + 1]
    try:
        return json.loads(t)
    except Exception:
        return None

def _gen_json(prompt, key):
    """Prueba modelos hasta obtener un JSON valido. Salta los que fallen o
    devuelvan basura (p.ej. gemma con respuesta vacia). None si ninguno lo da."""
    last = None
    for model in _model_order(key):
        try:
            txt = _post_generate(model, prompt, key)
        except Exception as e:
            last = e
            continue
        obj = _extract_json(txt)
        if isinstance(obj, dict) and obj.get("lines"):
            sys.stderr.write(f"[ai] modelo usado: {model}\n")
            return obj
        sys.stderr.write(f"[ai] {model} no dio JSON valido; pruebo otro.\n")
    if last:
        sys.stderr.write(f"[ai] ultimo error: {last}\n")
    return None


def _validate(s, tema="", cta="", broll_en=""):
    assert isinstance(s.get("lines"), list) and 4 <= len(s["lines"]) <= 12, "lineas fuera de rango"
    for ln in s["lines"]:
        assert ln.get("voice"), "linea sin voz"
        ln.setdefault("cap", "")
    s.setdefault("bg", "orange")
    if s["bg"] not in BGS:
        s["bg"] = "orange"
    hs = [h.lstrip("#") for h in s.get("hashtags", []) if h.strip()]
    if not hs or hs[0].lower() != "shorts":
        hs = ["Shorts"] + [h for h in hs if h.lower() != "shorts"]
    s["hashtags"] = (hs + ["historia", "curiosidades", "sabiasque", "datoscuriosos"])[:6]

    # TITULO: obliga a que lleve un numero o una palabra potente
    t = (s.get("title") or "").strip()
    low = t.lower()
    tiene_num = any(c.isdigit() for c in t) or any(w in low for w in
        ("tres", "cuatro", "cinco", "dos"))
    tiene_power = any(p in low for p in POWER)
    if not t or not (tiene_num or tiene_power):
        base = (tema or "la historia").strip()
        t = f"3 datos de {base} que no vas a creer"
    if "#short" not in low:
        t = t + " #shorts"
    s["title"] = t

    # CTA obligatorio como ultima linea (cebo de comentarios)
    if cta:
        last = (s["lines"][-1].get("voice", "") or "").lower()
        if "coment" not in last and "abajo" not in last and "sigue" not in last:
            s["lines"].append({"voice": cta, "cap": "comenta abajo"})

    if not (s.get("description") or "").strip():
        s["description"] = (t.replace(" #shorts", "") + ". " + (cta or "")).strip()
    s["description"] = s["description"].rstrip()

    # BROLL como pista de imagen
    bl = s.get("broll_list")
    if not isinstance(bl, list) or not bl:
        bl = [broll_en] if broll_en else []
    bl = [b.strip() for b in bl if isinstance(b, str) and b.strip()][:6]
    if bl:
        s["broll_list"] = bl
        s["broll"] = bl[0]
    elif broll_en:
        s["broll_list"] = [broll_en]; s["broll"] = broll_en

    s["ai_disclosure"] = False
    s["id"] = "ia-" + datetime.date.today().isoformat()
    s.pop("chart", None)
    return s


def _schema(tema, broll_en, formato, gancho, cta):
    return f"""
Devuelve UNICAMENTE un JSON valido (sin texto alrededor) con esta forma exacta:
{{
  "title": "titulo IMPACTANTE con un NUMERO y/o palabra potente (alucinante, no vas a creer, jamas, que no te ensenaron...). Sobre el tema de HOY. Max 80 caracteres, 1 emoji opcional, incluye #shorts.",
  "description": "1-2 frases con gancho + hashtags. Termina invitando a comentar.",
  "hashtags": ["Shorts", "historia", "curiosidades", "sabiasque", "datoscuriosos"],
  "bg": "uno de: orange, red, purple, teal",
  "broll": "{broll_en}",
  "broll_list": ["una ESCENA para RECREAR con IA por CADA dato, EN INGLES, concreta, con ACCION y lugar y epoca (ej: 'roman gladiators fighting in the colosseum arena, roaring crowd', 'julius caesar assassinated in the roman senate', 'a roman legion marching through a burning city at dusk'). En orden. Devuelve SIEMPRE EXACTAMENTE 4 escenas distintas (una por dato/momento). Describe una imagen VIVA, como un plano de cine."],
  "ai_disclosure": false,
  "lines": [
    {{"voice": "frase que se narra (numeros en palabras)", "cap": "subtitulo corto en pantalla (2-4 palabras)"}}
  ]
}}
GUION DE HOY (canal de HISTORIA, formato viral, DISTINTO a cualquier dia anterior):
- TEMA DE HOY (obligatorio, no elijas otro): {tema}.
- FORMATO DE HOY: {formato}
- LINEA 1 = GANCHO POTENTE (primeros 2 segundos). Empieza con algo tipo: "{gancho}" y promete el premio sin darlo aun.
- Luego los datos, uno por linea o dos, CADA UNO sorprendente, concreto y VERAZ (nada inventado; historia real). Del mas flojo al mas fuerte.
- ULTIMA LINEA = CEBO DE COMENTARIOS: algo tipo "{cta}".
- Entre 5 y 8 lineas en total. Frases cortas y con energia (ritmo rapido de Short, 30-45 s).
- Tono: divulgacion cercana, con chispa, que engancha. Espanol de Espana. NO academico ni aburrido.
- 'cap' sin emojis. 'voice' escribe los numeros con letras.
- IMPORTANTE: cada 'broll_list' describe una ESCENA cinematografica a RECREAR con IA (accion + lugar + epoca), como un plano de una pelicula historica. Nada de palabras sueltas.
"""


def generate():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    try:
        master = open(os.path.join(BASE, "PROMPT-MAESTRO.md"), encoding="utf-8").read()
    except Exception:
        master = "Eres un divulgador de historia experto en Shorts virales en espanol de Espana."

    tema, broll_en = _rot(TEMAS, 1)
    formato = _rot(FORMATOS, 3)
    gancho = _rot(GANCHOS, 5)
    cta = _rot(CTAS, 7)
    hoy = datetime.date.today().isoformat()

    prompt = (master
              + f"\n\n---\nTAREA DE HOY ({hoy}):\n"
              + "Crea un Short de historia con el formato viral de abajo. Sigue EXACTAMENTE el tema, "
                "el formato, el gancho y el cierre que se te asignan. Todo debe ser historia REAL.\n"
              + _schema(tema, broll_en, formato, gancho, cta))
    try:
        s = _gen_json(prompt, key)
        if not s:
            raise RuntimeError("ningun modelo dio JSON valido")
        s = _validate(s, tema=tema, cta=cta, broll_en=broll_en)
        return s
    except Exception as e:
        sys.stderr.write(f"[ai] no se pudo generar con IA ({e}); se usara el banco.\n")
        return None


if __name__ == "__main__":
    import json as _j
    s = generate()
    print(_j.dumps(s, ensure_ascii=False, indent=2) if s else "None (sin GEMINI_API_KEY o error)")
