# -*- coding: utf-8 -*-
"""
Cerebro del canal HISTORIA (Capsulas de Historia).
Gemini ELIGE el tema libre cada dia (dentro del canal). Para que no se repita ni
derive, se le pasa una PISTA rotatoria distinta cada dia (un area/epoca), ademas
de formato, gancho y cierre (todo por rotacion determinista).
Devuelve el mismo dict que usa generate.py.
"""
import os, sys, json, datetime, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("GEMINI_MODEL", "").strip()
_MODEL_CANDIDATES = [
    "gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash",
    "gemini-2.5-flash-lite", "gemini-2.0-flash-001", "gemini-1.5-flash",
]

CANAL_NOMBRE = "HISTORIA"
HASHTAGS_BASE = ("historia", "curiosidades", "sabiasque", "datoscuriosos")
TEMA_GENERICO = "la historia"
TITULO_FALLBACK = "3 datos de {base} que no vas a creer"
BG_DEFAULT = "orange"
BROLL_FALLBACK = "ancient stone ruins at golden hour, dramatic sky, cinematic, film grain"
BROLL_EJEMPLOS = ("ej: 'roman gladiators fighting in the colosseum arena, roaring crowd', "
                  "'julius caesar in the roman senate, torchlight', "
                  "'a roman legion marching through a burning city at dusk'")
TONO = ("divulgacion cercana, con chispa y ritmo, un punto de asombro. Espanol de Espana. "
        "Historia REAL, nunca inventes datos. Frases cortas y en presente. NO academico ni aburrido.")
REGLA_EXTRA = ("- Todo VERAZ: historia real, nada inventado.\n"
               "- Escenas SEGURAS para YouTube: dramaticas y con fuerza, pero SIN sangre, visceras, "
               "heridas, torturas explicitas, cadaveres ni desnudos. Sugiere el horror con atmosfera "
               "(sombras, gestos, reacciones), NO de forma explicita.\n"
               "- Personajes historicos como escena de epoca; nunca la cara de una persona real actual.")
MASTER_FALLBACK = "Eres un divulgador de historia experto en Shorts virales en espanol de Espana."

# PISTAS: areas/epocas AMPLIAS (no temas cerrados). Cada dia rota una para
# empujar variedad; Gemini elige el tema y el angulo exactos dentro de esa zona.
PISTAS = [
    ("las civilizaciones antiguas (Egipto, Roma, Grecia)", "ancient egypt pharaoh temple, cinematic"),
    ("imperios y su caida", "fall of an ancient empire, ruins and smoke at dusk"),
    ("la Edad Media, los castillos y los caballeros", "medieval knight before a stone castle at dawn"),
    ("guerras y grandes batallas de la historia", "historic battle formation on a misty field, banners"),
    ("vikingos, samurais y guerreros legendarios", "viking warriors on a longship at grey dawn"),
    ("exploradores, piratas y descubrimientos", "pirate ship on rough seas, golden age, dramatic light"),
    ("inventos y ciencia a lo largo de la historia", "old workshop with an early invention, candlelight"),
    ("misterios y civilizaciones perdidas", "lost ancient ruins swallowed by jungle, mist"),
    ("reyes, reinas y personajes poderosos", "royal throne room, portrait style, dramatic shadow"),
    ("la vida cotidiana del pasado (comida, higiene, costumbres)", "medieval market street, everyday life, warm light"),
    ("castigos, leyes y justicia antigua", "medieval stone dungeon, shadows, single torch"),
    ("plagas, medicina y supervivencia", "plague doctor silhouette in a foggy medieval street"),
    ("el siglo XX: guerras mundiales y guerra fria", "1940s historical photo style, city under grey sky"),
    ("la carrera espacial y grandes hitos", "1969 apollo rocket launch, vintage film look"),
    ("el Salvaje Oeste y otras fronteras", "wild west dusty town street at high noon, 1800s"),
    ("religiones, mitos y creencias antiguas", "ancient temple interior with statues, shafts of light"),
    ("catastrofes historicas (Titanic, Pompeya, incendios)", "titanic ship at sea, 1912, cold dramatic light"),
    ("revoluciones que cambiaron el mundo", "french revolution crowd with torches, painting style"),
]

FORMATOS = [
    "LISTA DE 3: tres datos historicos alucinantes y poco conocidos sobre el tema, del mas normal al mas fuerte.",
    "LISTA DE 4: cuatro datos rapidos y sorprendentes sobre el tema, ritmo agil.",
    "UN DATO BRUTAL: un solo hecho historico impactante sobre el tema, contado como una mini-historia con giro.",
    "LO QUE NO TE ENSENARON: 3 cosas que pasaban de verdad y que en el colegio no te contaron sobre el tema.",
    "COSTUMBRES INCREIBLES: 3 costumbres o practicas reales del tema que hoy nos parecerian una locura.",
]

GANCHOS = [
    "suelta de golpe el dato mas asqueroso, raro o brutal del tema, en presente y concreto, y remata con un bucle tipo 'y no es ni lo peor'",
    "abre con una imagen concreta y chocante (alguien haciendo algo increible) como si lo estuvieras viendo ahora mismo",
    "abre con una pregunta que cree un vacio de curiosidad imposible de ignorar sobre el tema",
    "empieza desmontando algo que casi todos creen ('lo que te contaron sobre esto es mentira') y promete la verdad",
    "abre con una cifra o una comparacion demoledora con el mundo de hoy",
]

CTAS = [
    "¿Cuál de estos te ha revuelto más? Te leo abajo.",
    "¿Cuál no te esperabas? Comenta el número.",
    "¿Vivirías en esa época? Dímelo en comentarios.",
    "Cuéntame cuál te ha dejado peor cuerpo.",
    "Sígueme, que mañana va otro que flipas.",
]

POWER = ("alucinante", "increible", "no creeras", "no vas a creer", "brutal",
         "impactante", "jamas", "nadie sabe", "prohibid", "oscuro", "escalofriante",
         "que cambio la historia", "que no te ensenaron", "sorprendente")

BGS = ["blue", "green", "orange", "purple", "teal", "red"]


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


# Red de seguridad: si el modelo escribe sin enes ni tildes, se restauran las
# palabras mas comunes (el subtitulo salia como "MANANA" en vez de "MANANA" con ene).
_ORTO = {
    "manana": "mañana", "ano": "año", "anos": "años", "nino": "niño", "ninos": "niños",
    "nina": "niña", "ninas": "niñas", "senor": "señor", "senora": "señora",
    "espanol": "español", "espanola": "española", "Espana": "España", "espana": "España",
    "pequeno": "pequeño", "pequena": "pequeña", "sueno": "sueño", "suenos": "sueños",
    "bano": "baño", "banos": "baños", "compania": "compañía", "montana": "montaña",
    "manana,": "mañana,", "ensenar": "enseñar", "ensena": "enseña", "diseno": "diseño",
    "extrano": "extraño", "dano": "daño", "danos": "daños", "puno": "puño",
    "canon": "cañón", "otono": "otoño", "sueno.": "sueño.", "duena": "dueña",
    "dueno": "dueño", "acompanar": "acompañar", "manana.": "mañana.",
}

def _fix_orto(txt):
    if not isinstance(txt, str) or not txt:
        return txt
    out = []
    for w in txt.split(" "):
        low = w.lower()
        rep = _ORTO.get(low) or _ORTO.get(w)
        if rep:
            if w[:1].isupper():
                rep = rep[:1].upper() + rep[1:]
            out.append(rep)
        else:
            out.append(w)
    return " ".join(out)


def _validate(s, tema="", cta="", broll_en=""):
    assert isinstance(s.get("lines"), list) and 4 <= len(s["lines"]) <= 12, "lineas fuera de rango"
    for ln in s["lines"]:
        assert ln.get("voice"), "linea sin voz"
        ln.setdefault("cap", "")
        ln["voice"] = _fix_orto(ln["voice"])
        ln["cap"] = _fix_orto(ln["cap"])
    s.setdefault("bg", BG_DEFAULT)
    if s["bg"] not in BGS:
        s["bg"] = BG_DEFAULT
    hs = [h.lstrip("#") for h in s.get("hashtags", []) if h.strip()]
    if not hs or hs[0].lower() != "shorts":
        hs = ["Shorts"] + [h for h in hs if h.lower() != "shorts"]
    s["hashtags"] = (hs + list(HASHTAGS_BASE))[:6]

    # TITULO: obliga a que lleve un numero o una palabra potente
    t = _fix_orto((s.get("title") or "").strip())
    low = t.lower()
    tiene_num = any(c.isdigit() for c in t) or any(w in low for w in
        ("tres", "cuatro", "cinco", "dos"))
    tiene_power = any(p in low for p in POWER)
    if not t:
        base = (tema or TEMA_GENERICO).strip()
        t = TITULO_FALLBACK.format(base=base)
    if "#short" not in low:
        t = t + " #shorts"
    s["title"] = t

    # CTA obligatorio como ultima linea (cebo de comentarios)
    if cta:
        last = (s["lines"][-1].get("voice", "") or "").lower()
        if "coment" not in last and "abajo" not in last and "sigue" not in last and "guarda" not in last:
            s["lines"].append({"voice": cta, "cap": "comenta abajo"})

    if not (s.get("description") or "").strip():
        s["description"] = (t.replace(" #shorts", "") + ". " + (cta or "")).strip()
    s["description"] = _fix_orto(s["description"]).rstrip()

    # BROLL como pista de imagen
    bl = s.get("broll_list")
    if not isinstance(bl, list) or not bl:
        bl = [broll_en] if broll_en else []
    bl = [b.strip() for b in bl if isinstance(b, str) and b.strip()][:12]
    if bl:
        s["broll_list"] = bl
        s["broll"] = bl[0]
    elif broll_en:
        s["broll_list"] = [broll_en]; s["broll"] = broll_en

    try:
        s["video_idx"] = int(s.get("video_idx", -1))
    except (TypeError, ValueError):
        s["video_idx"] = -1
    s["ai_disclosure"] = False
    s["id"] = "ia-" + datetime.date.today().isoformat()
    s.pop("chart", None)
    return s


def _schema(broll_en, formato, gancho, cta, pista):
    hs = '", "'.join(["Shorts"] + list(HASHTAGS_BASE))
    return f"""
Devuelve UNICAMENTE un JSON valido (sin texto alrededor) con esta forma exacta:
{{
  "title": "titulo IMPACTANTE con un NUMERO y/o una palabra potente. Sobre el tema de HOY. Max 80 caracteres, 1 emoji opcional, incluye #shorts.",
  "description": "1-2 frases con gancho + hashtags. Termina invitando a comentar.",
  "hashtags": ["{hs}"],
  "bg": "uno de: orange, red, purple, teal",
  "broll": "{broll_en}",
  "broll_list": ["una ESCENA para RECREAR con IA por CADA linea, EN INGLES, concreta, con ACCION, lugar y luz ({BROLL_EJEMPLOS}). En el MISMO orden que 'lines'. UNA escena por CADA linea (mismo numero de escenas que de lineas), y cada escena debe mostrar EXACTAMENTE lo que se narra en esa linea. Describe una imagen VIVA, como un plano de cine."],
  "ai_disclosure": false,
  "video_idx": "indice 0-based de la ESCENA de broll_list que MAS ganaria con MOVIMIENTO de video real (la mas dinamica). Devuelve -1 si ninguna lo necesita. Como MUCHO una.",
  "lines": [
    {{"voice": "frase que se narra (numeros en palabras)", "cap": "subtitulo corto en pantalla (2-4 palabras)"}}
  ]
}}
GUION DE HOY (canal de {CANAL_NOMBRE}, formato viral, DISTINTO a cualquier dia anterior):
- ELIGE TU EL TEMA DE HOY: libre, dentro del canal de {CANAL_NOMBRE}. Concreto y con gancho. Que sea DISTINTO a lo mas tipico y a lo de dias anteriores; NO te repitas ni tires siempre por lo mismo.
- PISTA PARA VARIAR HOY (orientate hacia esta zona para no caer siempre en lo mismo, pero TU decides el tema y el enfoque exactos, y puedes afinar dentro de ella): {pista}.
- FORMATO DE HOY: {formato}
- LINEA 1 = GANCHO (primer segundo). Tecnica de hoy: {gancho}. PROHIBIDO usar frases-comodin genericas ("el noventa por ciento no sabe esto", "prepara la cabeza", "esto te va a explotar la mente", "agarrate"): NO enganchan, suenan a bot. El gancho debe ser CONCRETO, especifico y util, sacado de lo MAS fuerte del tema de hoy, y ABRIR UN BUCLE (promete algo aun mejor que todavia no cuentas). Nada de empezar con "En [tema]...".
- Luego el contenido, cada parte concreta y VERAZ (nada inventado). De menos a mas: lo mejor al final.
- Encadena con TENSION ("pero lo siguiente es mejor", "y aun hay mas"), NO con "primero, segundo, tercero" a secas.
- ORTOGRAFIA: espanol de Espana IMPECABLE, con TILDES y con la letra ENE (mañana, año, España, sueño, pequeño). NUNCA sustituyas la ñ por n. Cuidado con articulos y concordancia. Frases cortas y en presente.
- ULTIMA LINEA = CIERRE que invita a participar: algo tipo "{cta}".
- Entre 5 y 8 lineas en total. Frases cortas y con energia (ritmo de Short, 30-45 s).
- Tono: {TONO}
- 'cap' sin emojis. 'voice' escribe los numeros con letras.
- SEGURIDAD (obligatorio): las escenas deben ser APTAS PARA YOUTUBE Y PUBLICIDAD. Con fuerza, pero SIN sangre, heridas, cuerpos mutilados, desnudos ni violencia explicita. Nada de caras de personas reales famosas.
{REGLA_EXTRA}
- CRITICO: cada escena de 'broll_list' debe MOSTRAR EXACTAMENTE lo que se narra en esa parte, EN EL MISMO ORDEN. NADA generico ni palabras sueltas: escena de cine con accion + lugar + luz, EN INGLES.
"""


def generate():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    try:
        master = open(os.path.join(BASE, "PROMPT-MAESTRO.md"), encoding="utf-8").read()
    except Exception:
        master = MASTER_FALLBACK

    pista, broll_en = _rot(PISTAS, 1)
    tema = ""  # el tema lo ELIGE Gemini; 'pista' solo orienta para no repetir
    formato = _rot(FORMATOS, 3)
    gancho = _rot(GANCHOS, 5)
    cta = _rot(CTAS, 7)
    hoy = datetime.date.today().isoformat()

    prompt = (master
              + f"\n\n---\nTAREA DE HOY ({hoy}):\n"
              + f"Crea un Short de {CANAL_NOMBRE} con el formato viral de abajo. ELIGE tu el tema (libre, del canal, sin repetir), "
                "y sigue EXACTAMENTE el formato, el gancho y el cierre que se te asignan. Todo debe ser VERAZ.\n"
              + _schema(broll_en, formato, gancho, cta, pista))
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
