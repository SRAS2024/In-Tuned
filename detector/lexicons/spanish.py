# detector/lexicons/spanish.py
"""
Comprehensive Spanish Emotion Lexicon

Includes:
- Core emotion vocabulary
- Regional variations (Mexico, Spain, Argentina, Colombia, etc.)
- Internet slang and modern expressions
- Conjugations and verb forms
- Idiomatic expressions
"""

from typing import Dict, List


def _build_lexicon() -> Dict[str, Dict[str, float]]:
    """Build the complete Spanish lexicon."""
    lex: Dict[str, Dict[str, float]] = {}

    def add(emotion: str, words: List[str], weight: float) -> None:
        for w in words:
            w_norm = w.lower().replace(" ", "_").replace("-", "")
            if w_norm not in lex:
                lex[w_norm] = {}
            lex[w_norm][emotion] = lex[w_norm].get(emotion, 0.0) + weight

    # =========================================================================
    # IRA / ANGER
    # =========================================================================

    # Core anger - all conjugations
    add("anger", [
        # Adjectives
        "enojado", "enojada", "enojados", "enojadas",
        "furioso", "furiosa", "furiosos", "furiosas",
        "molesto", "molesta", "molestos", "molestas",
        "irritado", "irritada", "irritados", "irritadas",
        "frustrado", "frustrada", "frustrados", "frustradas",
        "indignado", "indignada", "indignados", "indignadas",
        "enfadado", "enfadada", "enfadados", "enfadadas",  # Spain
        "rabioso", "rabiosa", "rabiosos", "rabiosas",
        "colérico", "colérica", "coléricos", "coléricas",
    ], 2.2)

    # Anger nouns
    add("anger", [
        "rabia", "ira", "furia", "enojo", "coraje", "cólera",
        "enfado", "bronca", "berrinche", "arrebato",
    ], 2.3)

    # Anger verbs - all conjugations
    add("anger", [
        # Odiar (hate)
        "odio", "odias", "odia", "odiamos", "odiáis", "odian",
        "odiaba", "odiabas", "odiábamos", "odiaban",
        "odié", "odiaste", "odió", "odiamos", "odiaron",
        # Detestar (detest)
        "detesto", "detestas", "detesta", "detestamos", "detestan",
        # Aborrecer (loathe)
        "aborrezco", "aborreces", "aborrece", "aborrecemos", "aborrecen",
    ], 2.4)

    # Regional slang - Mexico
    add("anger", [
        "encabronado", "encabronada", "encabronados",
        "emputado", "emputada", "emputados",
        "enchilado", "enchilada", "enchilados",
        "chingado", "chingada", "chingados",
        "pinche", "pinches",
        "maldito", "maldita", "malditos", "malditas",
        "me caga", "me cagas", "me cae mal",
    ], 2.0)

    # Regional slang - Spain
    add("anger", [
        "cabreado", "cabreada", "cabreados",
        "mosqueado", "mosqueada", "mosqueados",
        "tocado", "tocada",
        "flipado", "flipada",
        "hasta las narices", "hasta los huevos",
        "joder", "hostia", "coño", "mierda",
    ], 2.0)

    # Regional slang - Argentina
    add("anger", [
        "caliente", "recaliente", "calentón",
        "hinchado", "hinchada", "hinchapelotas",
        "podrido", "podrida",
        "sacado", "sacada",
        "me tiene podrido", "me tiene harto",
        "la concha de", "que mierda",
    ], 2.0)

    # Regional slang - Colombia/Venezuela
    add("anger", [
        "arrecho", "arrecha", "arrechos",
        "emberracado", "emberracada",
        "emputecido", "emputecida",
        "berraco", "berraca",
    ], 2.0)

    # Internet anger
    add("anger", [
        "asco", "me da asco", "qué asco",
        "wtf", "ptm", "alv", "nmms", "nmm",
        "qué pedo", "no mames", "no manches",
        "me tiene harto", "me tiene harta",
        "estoy hasta la madre",
    ], 1.8)

    # =========================================================================
    # ASCO / DISGUST
    # =========================================================================

    add("disgust", [
        # Core
        "asqueado", "asqueada", "asqueados", "asqueadas",
        "repugnante", "repugnantes",
        "asqueroso", "asquerosa", "asquerosos", "asquerosas",
        "nauseabundo", "nauseabunda",
        "repulsivo", "repulsiva",
        "vomitivo", "vomitiva",
        # Nouns
        "asco", "repugnancia", "náusea", "náuseas",
        # Expressions
        "me da asco", "qué asco", "guácala", "guácatela",
        "puaj", "fuchi", "fúchila", "iugh", "iug",
    ], 2.2)

    # Modern slang
    add("disgust", [
        "cringe", "cringy", "cringey",
        "patético", "patética", "patéticos",
        "penoso", "penosa", "penosos",
        "vergonzoso", "vergonzosa",
        "turbio", "turbia", "turbios",
        "raro", "rara", "raros", "raras",
        "incómodo", "incómoda",
    ], 1.8)

    # =========================================================================
    # MIEDO / FEAR
    # =========================================================================

    add("fear", [
        # Core adjectives - all forms
        "asustado", "asustada", "asustados", "asustadas",
        "aterrado", "aterrada", "aterrados", "aterradas",
        "atemorizado", "atemorizada",
        "espantado", "espantada",
        "horrorizado", "horrorizada",
        "aterrorizado", "aterrorizada",
        "temeroso", "temerosa",
        "miedoso", "miedosa",
    ], 2.3)

    # Anxiety
    add("fear", [
        "ansioso", "ansiosa", "ansiosos", "ansiosas",
        "preocupado", "preocupada", "preocupados", "preocupadas",
        "nervioso", "nerviosa", "nerviosos", "nerviosas",
        "inquieto", "inquieta", "inquietos", "inquietas",
        "intranquilo", "intranquila",
        "tenso", "tensa", "tensos", "tensas",
        "estresado", "estresada", "estresados", "estresadas",
        "agobiado", "agobiada",
        "abrumado", "abrumada",
        "angustiado", "angustiada",
    ], 2.2)

    # Nouns
    add("fear", [
        "miedo", "temor", "terror", "pánico", "pavor", "espanto",
        "ansiedad", "preocupación", "nervios", "estrés",
        "angustia", "inquietud", "zozobra",
    ], 2.1)

    # Expressions
    add("fear", [
        "tengo miedo", "me da miedo", "qué miedo",
        "estoy cagado", "estoy cagada", "cagado de miedo",
        "me muero de miedo", "me cago de miedo",
        "no puedo respirar", "me falta el aire",
        "me está dando ansiedad", "me pone nervioso",
    ], 2.0)

    # =========================================================================
    # ALEGRÍA / JOY
    # =========================================================================

    add("joy", [
        # Core
        "feliz", "felices",
        "contento", "contenta", "contentos", "contentas",
        "alegre", "alegres",
        "dichoso", "dichosa",
        "encantado", "encantada", "encantados",
        "emocionado", "emocionada", "emocionados",
        "entusiasmado", "entusiasmada",
        "ilusionado", "ilusionada",
        "satisfecho", "satisfecha",
        "orgulloso", "orgullosa",
    ], 2.2)

    # Nouns
    add("joy", [
        "felicidad", "alegría", "dicha", "gozo", "júbilo",
        "entusiasmo", "emoción", "ilusión", "euforia",
    ], 2.1)

    # Laughter
    add("joy", [
        "jaja", "jajaja", "jajajaja", "jajajajaja",
        "jeje", "jejeje", "jiji", "jijiji",
        "xd", "xdd", "xddd", "lol", "lmao",
        "juas", "muajaja",
    ], 1.8)

    # Regional - Mexico
    add("joy", [
        "chido", "chida", "chidos", "chidas",
        "chingón", "chingona", "chingones",
        "padre", "padrisimo", "padrisima",
        "genial", "geniales",
        "a toda madre", "que chido", "que padre",
        "está con madre", "rifado", "rifada",
    ], 1.9)

    # Regional - Spain
    add("joy", [
        "guay", "mola", "molón", "molona",
        "flipante", "flipar",
        "de puta madre", "cojonudo", "cojonuda",
        "estupendo", "estupenda",
        "genial", "brutal", "bestial",
    ], 1.9)

    # Regional - Argentina
    add("joy", [
        "copado", "copada", "copados",
        "mortal", "mortales",
        "zarpado", "zarpada",
        "re loco", "re copado",
        "re bien", "re bueno",
        "piola", "piolas",
        "de una", "joya", "fenómeno",
    ], 1.9)

    # Regional - Colombia/Caribbean
    add("joy", [
        "chévere", "chevere",
        "bacano", "bacana", "bacanos",
        "qué nota", "qué chimba",
        "parce", "parcero",
    ], 1.9)

    # Internet/modern
    add("joy", [
        "me encanta", "te amo", "amo esto",
        "lo mejor", "increíble", "espectacular",
        "buenísimo", "buenisimo", "buenaza", "buezo",
        "que buena onda", "que onda",
    ], 1.8)

    # Small affirmations
    add("joy", [
        "bien", "bueno", "ok", "vale", "dale",
        "sí", "si", "claro", "obvio",
    ], 0.9)

    # =========================================================================
    # TRISTEZA / SADNESS
    # =========================================================================

    add("sadness", [
        # Core adjectives
        "triste", "tristes",
        "deprimido", "deprimida", "deprimidos", "deprimidas",
        "desanimado", "desanimada",
        "decaído", "decaída",
        "abatido", "abatida",
        "desconsolado", "desconsolada",
        "afligido", "afligida",
        "acongojado", "acongojada",
        "melancólico", "melancólica",
        "nostálgico", "nostálgica",
    ], 2.3)

    # Despair/hopelessness
    add("sadness", [
        "desesperado", "desesperada", "desesperanzado",
        "desolado", "desolada",
        "devastado", "devastada",
        "destrozado", "destrozada",
        "destruido", "destruida",
        "roto", "rota", "rotos", "rotas",
        "vacío", "vacía", "vacio", "vacia",
        "hueco", "hueca",
    ], 2.4)

    # Loneliness
    add("sadness", [
        "solo", "sola", "solos", "solas",
        "aislado", "aislada",
        "abandonado", "abandonada",
        "rechazado", "rechazada",
        "ignorado", "ignorada",
    ], 2.1)

    # Nouns
    add("sadness", [
        "tristeza", "pena", "dolor", "sufrimiento",
        "melancolía", "nostalgia", "soledad", "vacío",
        "desesperación", "angustia", "depresión", "depre",
    ], 2.2)

    # Verbs/expressions
    add("sadness", [
        "llorando", "llorar", "lloro", "lloras", "llora",
        "lloré", "lloraste", "lloró",
        "sufrir", "sufro", "sufres", "sufre",
        "extraño", "extrañas", "extraña", "extrañamos",
        "echo de menos", "te extraño", "te echo de menos",
    ], 2.0)

    # Modern expressions
    add("sadness", [
        "estoy mal", "me siento mal",
        "no estoy bien", "estoy muy mal",
        "no aguanto más", "no puedo más",
        "bajoneado", "bajoneada", "bajón",
        "en mi peor momento", "pasándola mal",
        "la estoy pasando mal", "todo está mal",
        "me quiero morir",  # Note: this is also a safety concern
    ], 2.0)

    # =========================================================================
    # PASIÓN / PASSION
    # =========================================================================

    add("passion", [
        # Love verbs - all conjugations
        "amo", "amas", "ama", "amamos", "amáis", "aman",
        "amaba", "amabas", "amábamos", "amaban",
        "amé", "amaste", "amó", "amamos", "amaron",
        "quiero", "quieres", "quiere", "queremos", "quieren",
        "quería", "querías", "queríamos", "querían",
        # Adjectives
        "enamorado", "enamorada", "enamorados", "enamoradas",
        "apasionado", "apasionada",
        "obsesionado", "obsesionada",
        "loco por", "loca por",
    ], 2.3)

    # Love nouns
    add("passion", [
        "amor", "pasión", "cariño", "afecto", "ternura",
        "deseo", "atracción", "adoración",
    ], 2.2)

    # Expressions
    add("passion", [
        "te quiero", "te amo", "te adoro",
        "mi amor", "mi vida", "mi cielo", "mi corazón",
        "cariño", "mi cariño", "tesoro",
        "estoy enamorado", "estoy enamorada",
        "me gustas", "me encantas", "me fascinas",
        "me vuelves loco", "me vuelves loca",
    ], 2.4)

    # Modern slang
    add("passion", [
        "crush", "mi crush", "tengo un crush",
        "shipeo", "shipeando", "otp",
        "bae", "bb", "bby",
        "hermoso", "hermosa", "precioso", "preciosa",
        "guapo", "guapa", "guapísimo", "guapísima",
        "belleza", "bello", "bella",
    ], 1.9)

    # =========================================================================
    # SORPRESA / SURPRISE
    # =========================================================================

    add("surprise", [
        # Adjectives
        "sorprendido", "sorprendida", "sorprendidos",
        "impactado", "impactada",
        "asombrado", "asombrada",
        "atónito", "atónita",
        "estupefacto", "estupefacta",
        "perplejo", "perpleja",
        "desconcertado", "desconcertada",
    ], 2.2)

    # Nouns
    add("surprise", [
        "sorpresa", "asombro", "estupefacción",
    ], 2.0)

    # Exclamations
    add("surprise", [
        "wow", "guau", "órale", "orale",
        "¡qué!", "que", "qué onda",
        "no puede ser", "no lo puedo creer",
        "increíble", "increible", "impresionante",
        "omg", "dios mío", "madre mía",
        "ay", "híjole", "hijole", "órale",
    ], 1.9)

    # Regional
    add("surprise", [
        # Mexico
        "no manches", "no mames", "qué pedo",
        "neta", "a poco", "en serio",
        # Spain
        "¡ostras!", "¡hostia!", "flipando",
        "alucino", "alucinante",
        # Argentina
        "boludo no", "qué flash", "flasheaste",
    ], 1.8)

    return lex


SPANISH_LEXICON = _build_lexicon()


# =========================================================================
# PHRASE LEXICON
# =========================================================================

def _vec(**kw: float) -> Dict[str, float]:
    v = {"anger": 0.0, "disgust": 0.0, "fear": 0.0, "joy": 0.0,
         "sadness": 0.0, "passion": 0.0, "surprise": 0.0}
    v.update(kw)
    return v


SPANISH_PHRASES: Dict[str, Dict[str, float]] = {
    # Joy
    "estar en las nubes": _vec(joy=2.8),
    "en la gloria": _vec(joy=2.8),
    "de maravilla": _vec(joy=2.5),
    "pasándola genial": _vec(joy=2.5),
    "la estoy pasando bien": _vec(joy=2.3),
    "que alegría": _vec(joy=2.5),
    "me hace feliz": _vec(joy=2.5),
    "estoy muy feliz": _vec(joy=2.6),
    "no cabe de la felicidad": _vec(joy=2.8),
    "super contento": _vec(joy=2.4),
    "super contenta": _vec(joy=2.4),
    "me encanta esto": _vec(joy=2.3),
    "lo mejor del mundo": _vec(joy=2.5),

    # Anger
    "me tiene harto": _vec(anger=2.5),
    "me tiene harta": _vec(anger=2.5),
    "estoy hasta la madre": _vec(anger=2.8),
    "estoy hasta el gorro": _vec(anger=2.3),
    "estoy hasta las narices": _vec(anger=2.5),
    "me caga": _vec(anger=2.5),
    "me emputa": _vec(anger=2.6),
    "me da rabia": _vec(anger=2.4),
    "me hierve la sangre": _vec(anger=2.7),
    "qué coraje": _vec(anger=2.3),
    "me saca de quicio": _vec(anger=2.4),
    "perdí la paciencia": _vec(anger=2.3),
    "no lo soporto": _vec(anger=2.4),
    "ya no aguanto": _vec(anger=2.3, sadness=1.0),

    # Sadness
    "corazón roto": _vec(sadness=3.0),
    "me duele el corazón": _vec(sadness=2.8),
    "estoy pasando por mucho": _vec(sadness=2.5),
    "la estoy pasando mal": _vec(sadness=2.6),
    "me siento vacío": _vec(sadness=2.7),
    "me siento vacía": _vec(sadness=2.7),
    "no tengo ganas de nada": _vec(sadness=2.5),
    "no me importa nada": _vec(sadness=2.4),
    "todo me sale mal": _vec(sadness=2.4),
    "estoy en mi peor momento": _vec(sadness=2.6),
    "no puedo más": _vec(sadness=2.8, fear=1.0),
    "ya no aguanto más": _vec(sadness=2.8, anger=1.0),
    "me quiero morir": _vec(sadness=3.0),  # Also safety
    "no tiene sentido": _vec(sadness=2.3),

    # Fear
    "me da mucho miedo": _vec(fear=2.6),
    "estoy cagado de miedo": _vec(fear=2.8),
    "estoy cagada de miedo": _vec(fear=2.8),
    "me muero de miedo": _vec(fear=2.7),
    "me está dando ansiedad": _vec(fear=2.5),
    "tengo un ataque de pánico": _vec(fear=3.0),
    "no puedo respirar": _vec(fear=2.8),
    "estoy muy nervioso": _vec(fear=2.4),
    "estoy muy nerviosa": _vec(fear=2.4),
    "me preocupa mucho": _vec(fear=2.3),
    "no puedo dejar de pensar": _vec(fear=2.2),

    # Disgust
    "me da asco": _vec(disgust=2.5),
    "qué asco": _vec(disgust=2.4),
    "me da náuseas": _vec(disgust=2.6),
    "quiero vomitar": _vec(disgust=2.5),
    "es repugnante": _vec(disgust=2.5),
    "no lo soporto": _vec(disgust=2.0, anger=1.5),
    "qué patético": _vec(disgust=2.2),
    "da vergüenza ajena": _vec(disgust=2.3),
    "qué cringe": _vec(disgust=2.0),

    # Passion
    "estoy enamorado": _vec(passion=2.8),
    "estoy enamorada": _vec(passion=2.8),
    "te amo con todo mi corazón": _vec(passion=3.0),
    "eres mi vida": _vec(passion=2.9),
    "no puedo vivir sin ti": _vec(passion=2.8),
    "me vuelves loco": _vec(passion=2.6),
    "me vuelves loca": _vec(passion=2.6),
    "loco por ti": _vec(passion=2.7),
    "loca por ti": _vec(passion=2.7),
    "muero por ti": _vec(passion=2.8),
    "mi media naranja": _vec(passion=2.5),
    "amor de mi vida": _vec(passion=2.9),

    # Surprise
    "no lo puedo creer": _vec(surprise=2.5),
    "no puede ser": _vec(surprise=2.4),
    "me dejó sin palabras": _vec(surprise=2.5),
    "estoy en shock": _vec(surprise=2.6),
    "qué locura": _vec(surprise=2.2),
    "esto es increíble": _vec(surprise=2.3),
    "de verdad": _vec(surprise=1.5),
    "en serio": _vec(surprise=1.5),
    "no me jodas": _vec(surprise=2.2, anger=1.0),
}


# =========================================================================
# INTENSIFIERS
# =========================================================================

SPANISH_INTENSIFIERS: Dict[str, float] = {
    # Strong
    "muy": 1.4,
    "mucho": 1.4,
    "muchísimo": 1.8,
    "extremadamente": 1.8,
    "increíblemente": 1.7,
    "totalmente": 1.6,
    "completamente": 1.6,
    "absolutamente": 1.7,
    "demasiado": 1.5,
    "súper": 1.5,
    "super": 1.5,
    "hiper": 1.5,
    "mega": 1.5,
    "ultra": 1.5,
    "re": 1.4,  # Argentina

    # Moderate
    "bastante": 1.3,
    "bien": 1.2,
    "algo": 1.1,

    # Diminishers
    "un poco": 0.7,
    "un poquito": 0.6,
    "apenas": 0.6,
    "casi": 0.7,
    "medio": 0.8,

    # Regional
    "bien": 1.3,  # Mexico: "bien chido"
    "re": 1.5,  # Argentina: "re copado"
    "recontra": 1.7,  # Argentina
}
