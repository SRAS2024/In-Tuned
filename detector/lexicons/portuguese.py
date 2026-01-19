# detector/lexicons/portuguese.py
"""
Comprehensive Portuguese Emotion Lexicon

Includes:
- Core emotion vocabulary
- Brazilian Portuguese (PT-BR) variations
- European Portuguese (PT-PT) variations
- Internet slang and modern expressions
- Conjugations and verb forms
- Idiomatic expressions
"""

from typing import Dict, List


def _build_lexicon() -> Dict[str, Dict[str, float]]:
    """Build the complete Portuguese lexicon."""
    lex: Dict[str, Dict[str, float]] = {}

    def add(emotion: str, words: List[str], weight: float) -> None:
        for w in words:
            w_norm = w.lower().replace(" ", "_").replace("-", "")
            if w_norm not in lex:
                lex[w_norm] = {}
            lex[w_norm][emotion] = lex[w_norm].get(emotion, 0.0) + weight

    # =========================================================================
    # RAIVA / ANGER
    # =========================================================================

    # Core anger adjectives
    add("anger", [
        # Raiva/anger
        "irritado", "irritada", "irritados", "irritadas",
        "bravo", "brava", "bravos", "bravas",
        "furioso", "furiosa", "furiosos", "furiosas",
        "com_raiva", "enraivecido", "enraivecida",
        "zangado", "zangada", "zangados", "zangadas",  # PT-PT
        "chateado", "chateada", "chateados", "chateadas",
        "frustrado", "frustrada", "frustrados", "frustradas",
        "indignado", "indignada",
        "revoltado", "revoltada",
    ], 2.2)

    # Anger nouns
    add("anger", [
        "raiva", "fúria", "ira", "cólera", "revolta",
        "indignação", "frustração",
    ], 2.3)

    # Anger verbs - all conjugations
    add("anger", [
        # Odiar
        "odeio", "odeias", "odeia", "odiamos", "odeiam",
        "odiava", "odiavas", "odiávamos", "odiavam",
        "odiei", "odiaste", "odiou", "odiámos", "odiaram",
        # Detestar
        "detesto", "detestas", "detesta", "detestamos", "detestam",
        # Abominar
        "abomino", "abominas", "abomina",
    ], 2.4)

    # Brazilian slang
    add("anger", [
        "puto", "puta", "putos", "putas",
        "putasso", "putassa",
        "de saco cheio", "saco cheio",
        "enchendo o saco",
        "que droga", "que merda", "que porra",
        "caralho", "porra", "merda", "cacete",
        "bosta", "foda", "fodido", "fodida",
        "me irrita", "me estressa",
        "que raiva", "que ódio",
        "não aguento mais",
    ], 2.0)

    # PT-PT slang
    add("anger", [
        "chateado", "chateada",
        "farto", "farta",
        "fulo", "fula",
        "fodasse", "foda-se",
        "cabrão", "cabrões",
        "enerva-me", "chateia-me",
    ], 2.0)

    # Internet anger
    add("anger", [
        "wtf", "pqp", "vsf", "vtnc",
        "putamerda", "namoral",
        "na moral", "pelo amor",
    ], 1.8)

    # =========================================================================
    # NOJO / DISGUST
    # =========================================================================

    add("disgust", [
        # Core
        "enojado", "enojada",  # Note: in PT means disgusted, not angry
        "com_nojo", "nauseado", "nauseada",
        "repugnante", "repugnantes",
        "nojento", "nojenta", "nojentos", "nojentas",
        "asqueroso", "asquerosa",
        "imundo", "imunda",
        "horrível", "horríveis",
        # Nouns
        "nojo", "repugnância", "náusea", "ânsia",
        # Expressions
        "que nojo", "dá nojo", "me dá nojo",
        "eca", "argh", "ugh", "credo",
    ], 2.2)

    # Modern slang
    add("disgust", [
        "cringe", "cringy",
        "vergonha_alheia", "vergonhaalheia",
        "tenso", "tensa", "tensos",
        "estranho", "estranha", "estranhos",
        "bizarro", "bizarra", "bizarros",
        "tosco", "tosca", "toscos",
    ], 1.8)

    # =========================================================================
    # MEDO / FEAR
    # =========================================================================

    add("fear", [
        # Core adjectives
        "assustado", "assustada", "assustados", "assustadas",
        "amedrontado", "amedrontada",
        "aterrorizado", "aterrorizada",
        "apavorado", "apavorada",
        "com_medo", "medroso", "medrosa",
        "temeroso", "temerosa",
    ], 2.3)

    # Anxiety
    add("fear", [
        "ansioso", "ansiosa", "ansiosos", "ansiosas",
        "preocupado", "preocupada", "preocupados", "preocupadas",
        "nervoso", "nervosa", "nervosos", "nervosas",
        "tenso", "tensa", "tensos", "tensas",
        "estressado", "estressada",  # BR
        "stressado", "stressada",  # PT
        "aflito", "aflita",
        "angustiado", "angustiada",
        "apreensivo", "apreensiva",
    ], 2.2)

    # Nouns
    add("fear", [
        "medo", "temor", "terror", "pânico", "pavor",
        "ansiedade", "preocupação", "nervosismo", "stress", "estresse",
        "angústia", "aflição",
    ], 2.1)

    # Expressions
    add("fear", [
        "tenho medo", "estou com medo",
        "me dá medo", "fico com medo",
        "to cagando de medo", "cagando de medo",
        "to tremendo", "estou tremendo",
        "não consigo respirar",
        "to tendo ansiedade", "me dá ansiedade",
        "to mal", "estou mal",
    ], 2.0)

    # =========================================================================
    # ALEGRIA / JOY
    # =========================================================================

    add("joy", [
        # Core
        "feliz", "felizes",
        "contente", "contentes",
        "alegre", "alegres",
        "animado", "animada", "animados", "animadas",
        "empolgado", "empolgada", "empolgados",
        "entusiasmado", "entusiasmada",
        "radiante", "radiantes",
        "satisfeito", "satisfeita",
        "realizado", "realizada",
        "orgulhoso", "orgulhosa",
    ], 2.2)

    # Nouns
    add("joy", [
        "felicidade", "alegria", "contentamento",
        "entusiasmo", "empolgação", "euforia",
    ], 2.1)

    # Laughter
    add("joy", [
        "kkk", "kkkk", "kkkkk", "kkkkkk",
        "rs", "rsrs", "rsrsrs",
        "haha", "hahaha", "hahahaha",
        "hehe", "hehehe",
        "huahua", "huahuahua",
        "ahahaha", "aushuas",
        "ksksk", "ksksks",
        "lol", "lmao", "xd",
    ], 1.8)

    # Brazilian slang
    add("joy", [
        "demais", "muito bom", "massa", "show",
        "legal", "bacana", "maneiro", "maneira",
        "top", "topzera", "topzão",
        "da hora", "dahora",
        "irado", "irada",
        "sinistro", "sinistra",
        "mó legal", "mó massa",
        "brabo", "braba", "brabíssimo",
        "zika", "zica", "zicado",
        "foda", "fodástico",  # positive usage
        "sensacional", "incrível", "maravilhoso",
    ], 1.9)

    # PT-PT slang
    add("joy", [
        "fixe", "fixes",
        "porreiro", "porreira",
        "giro", "gira", "giros",
        "bestial", "espetacular",
        "brutal",
    ], 1.9)

    # Internet expressions
    add("joy", [
        "amei", "adorei", "curti",
        "muito bom", "bom demais",
        "que incrível", "que massa",
        "to amando", "amando",
        "perfeito", "perfeita",
    ], 1.8)

    # Small affirmations
    add("joy", [
        "beleza", "blz", "de boa",
        "suave", "tranquilo", "tranquila",
        "sim", "tá", "ta bom", "ok", "okay",
        "opa", "eba", "uhu", "uhul",
    ], 0.9)

    # =========================================================================
    # TRISTEZA / SADNESS
    # =========================================================================

    add("sadness", [
        # Core
        "triste", "tristes",
        "deprimido", "deprimida", "deprimidos",
        "desanimado", "desanimada",
        "abatido", "abatida",
        "desconsolado", "desconsolada",
        "desolado", "desolada",
        "melancólico", "melancólica",
        "nostálgico", "nostálgica",
        "cabisbaixo", "cabisbaixa",
    ], 2.3)

    # Despair
    add("sadness", [
        "desesperado", "desesperada",
        "desesperançado", "desesperançada",
        "devastado", "devastada",
        "arrasado", "arrasada",
        "destruído", "destruída",
        "acabado", "acabada",
        "vazio", "vazia",
        "oco", "oca",
    ], 2.4)

    # Loneliness
    add("sadness", [
        "sozinho", "sozinha", "sozinhos", "sozinhas",
        "solitário", "solitária",
        "isolado", "isolada",
        "abandonado", "abandonada",
        "rejeitado", "rejeitada",
    ], 2.1)

    # Nouns
    add("sadness", [
        "tristeza", "pena", "dor", "sofrimento",
        "melancolia", "nostalgia", "solidão", "vazio",
        "desespero", "angústia", "depressão", "depre",
    ], 2.2)

    # Verbs/expressions
    add("sadness", [
        "chorando", "chorar", "choro", "choras", "chora",
        "chorei", "choraste", "chorou",
        "sofrer", "sofro", "sofres", "sofre",
        "sinto falta", "sentes falta", "sente falta",
        "saudade", "saudades", "morrendo de saudade",
    ], 2.0)

    # Modern expressions
    add("sadness", [
        "to mal", "estou mal",
        "não to bem", "não estou bem",
        "não aguento mais", "nao aguento mais",
        "cansado de tudo", "cansada de tudo",
        "na bad", "na pior", "muito mal",
        "fundo do poço", "sem chão",
        "coração partido", "destroçado",
    ], 2.0)

    # =========================================================================
    # PAIXÃO / PASSION
    # =========================================================================

    add("passion", [
        # Love verbs - all conjugations
        "amo", "amas", "ama", "amamos", "amais", "amam",
        "amava", "amavas", "amávamos", "amavam",
        "amei", "amaste", "amou", "amámos", "amaram",
        "adoro", "adoras", "adora", "adoramos", "adoram",
        "quero", "queres", "quer", "queremos", "querem",
        # Adjectives
        "apaixonado", "apaixonada", "apaixonados",
        "enamorado", "enamorada",
        "encantado", "encantada",
        "obcecado", "obcecada",
        "louco por", "louca por",
    ], 2.3)

    # Love nouns
    add("passion", [
        "amor", "paixão", "carinho", "afeto", "ternura",
        "desejo", "atração", "adoração",
    ], 2.2)

    # Expressions
    add("passion", [
        "te amo", "te adoro", "eu te amo",
        "meu amor", "minha vida", "meu bem",
        "meu coração", "amor da minha vida",
        "estou apaixonado", "estou apaixonada",
        "to apaixonado", "to apaixonada",
        "gosto de você", "gosto muito de você",
        "você me encanta", "te quero",
    ], 2.4)

    # Modern slang
    add("passion", [
        "crush", "meu crush", "tenho crush",
        "shippo", "shippando",
        "bb", "babe", "mozão", "mozao",
        "gatinho", "gatinha", "gato", "gata",
        "tesão", "tesudo", "tesuda",
        "gostoso", "gostosa",
        "lindo", "linda", "lindão", "lindona",
    ], 1.9)

    # =========================================================================
    # SURPRESA / SURPRISE
    # =========================================================================

    add("surprise", [
        # Adjectives
        "surpreso", "surpresa", "surpreendido", "surpreendida",
        "chocado", "chocada", "chocados",
        "impressionado", "impressionada",
        "espantado", "espantada",
        "atônito", "atônita",
        "perplexo", "perplexa",
        "abismado", "abismada",
    ], 2.2)

    # Nouns
    add("surprise", [
        "surpresa", "espanto", "choque",
    ], 2.0)

    # Exclamations
    add("surprise", [
        "uau", "wow", "nossa", "nossa senhora",
        "meu deus", "ai meu deus", "jesus",
        "caramba", "caraca", "caralho",
        "eita", "eita porra", "vish", "vixi",
        "mano", "cara", "véi", "velho",
        "sério", "serio", "jura",
    ], 1.9)

    # Brazilian expressions
    add("surprise", [
        "não acredito", "nao acredito",
        "mentira", "é mentira",
        "para de mentir", "jura que",
        "pelo amor de deus",
        "que isso", "que loucura",
        "mds", "mano do céu",
        "wtf", "vsf",
    ], 1.8)

    return lex


PORTUGUESE_LEXICON = _build_lexicon()


# =========================================================================
# PHRASE LEXICON
# =========================================================================

def _vec(**kw: float) -> Dict[str, float]:
    v = {"anger": 0.0, "disgust": 0.0, "fear": 0.0, "joy": 0.0,
         "sadness": 0.0, "passion": 0.0, "surprise": 0.0}
    v.update(kw)
    return v


PORTUGUESE_PHRASES: Dict[str, Dict[str, float]] = {
    # Joy
    "nas nuvens": _vec(joy=2.8),
    "no sétimo céu": _vec(joy=2.8),
    "muito feliz": _vec(joy=2.5),
    "super feliz": _vec(joy=2.6),
    "to muito feliz": _vec(joy=2.5),
    "melhor dia": _vec(joy=2.4),
    "que alegria": _vec(joy=2.5),
    "que massa": _vec(joy=2.2),
    "muito bom": _vec(joy=2.2),
    "bom demais": _vec(joy=2.3),
    "demais da conta": _vec(joy=2.3),
    "amei isso": _vec(joy=2.3),
    "to amando": _vec(joy=2.4, passion=1.0),
    "vivendo meu melhor momento": _vec(joy=2.5),

    # Anger
    "de saco cheio": _vec(anger=2.5),
    "encher o saco": _vec(anger=2.3),
    "que raiva": _vec(anger=2.5),
    "me irrita muito": _vec(anger=2.5),
    "estou puto": _vec(anger=2.6),
    "estou puta": _vec(anger=2.6),
    "não aguento mais": _vec(anger=2.3, sadness=1.5),
    "perdi a paciência": _vec(anger=2.4),
    "que ódio": _vec(anger=2.6),
    "sangue fervendo": _vec(anger=2.7),
    "me tira do sério": _vec(anger=2.4),
    "vou explodir": _vec(anger=2.5),
    "estou explodindo": _vec(anger=2.6),

    # Sadness
    "coração partido": _vec(sadness=3.0),
    "me dói o coração": _vec(sadness=2.8),
    "estou passando por muito": _vec(sadness=2.5),
    "to muito mal": _vec(sadness=2.6),
    "me sinto vazio": _vec(sadness=2.7),
    "me sinto vazia": _vec(sadness=2.7),
    "sem vontade de nada": _vec(sadness=2.5),
    "não tenho vontade de nada": _vec(sadness=2.5),
    "nada faz sentido": _vec(sadness=2.4),
    "estou no fundo do poço": _vec(sadness=2.8),
    "morrendo de saudade": _vec(sadness=2.5, passion=1.5),
    "sinto muita falta": _vec(sadness=2.4, passion=1.5),
    "chorando muito": _vec(sadness=2.7),
    "não consigo parar de chorar": _vec(sadness=2.8),
    "quero morrer": _vec(sadness=3.0),  # Also safety

    # Fear
    "muito medo": _vec(fear=2.6),
    "cagando de medo": _vec(fear=2.8),
    "morrendo de medo": _vec(fear=2.7),
    "to com muita ansiedade": _vec(fear=2.5),
    "tendo ataque de pânico": _vec(fear=3.0),
    "não consigo respirar": _vec(fear=2.8),
    "estou tremendo": _vec(fear=2.4),
    "to tremendo": _vec(fear=2.4),
    "muito nervoso": _vec(fear=2.4),
    "muito nervosa": _vec(fear=2.4),
    "estou pirando": _vec(fear=2.5),
    "to surtando": _vec(fear=2.5),
    "me preocupa muito": _vec(fear=2.3),

    # Disgust
    "me dá nojo": _vec(disgust=2.5),
    "que nojo": _vec(disgust=2.4),
    "me dá ânsia": _vec(disgust=2.6),
    "quero vomitar": _vec(disgust=2.5),
    "é nojento": _vec(disgust=2.5),
    "muito cringe": _vec(disgust=2.0),
    "vergonha alheia": _vec(disgust=2.2),

    # Passion
    "estou apaixonado": _vec(passion=2.8),
    "estou apaixonada": _vec(passion=2.8),
    "to apaixonado": _vec(passion=2.7),
    "to apaixonada": _vec(passion=2.7),
    "te amo muito": _vec(passion=3.0),
    "te amo demais": _vec(passion=3.0),
    "você é minha vida": _vec(passion=2.9),
    "não vivo sem você": _vec(passion=2.8),
    "louco por você": _vec(passion=2.7),
    "louca por você": _vec(passion=2.7),
    "morrendo de amor": _vec(passion=2.8),
    "amor da minha vida": _vec(passion=2.9),
    "meu grande amor": _vec(passion=2.8),

    # Surprise
    "não acredito": _vec(surprise=2.5),
    "não pode ser": _vec(surprise=2.4),
    "fiquei sem palavras": _vec(surprise=2.5),
    "estou em choque": _vec(surprise=2.6),
    "to em choque": _vec(surprise=2.5),
    "que loucura": _vec(surprise=2.2),
    "isso é incrível": _vec(surprise=2.3),
    "não é possível": _vec(surprise=2.3),
    "jura que": _vec(surprise=2.0),
    "mano do céu": _vec(surprise=2.2),
}


# =========================================================================
# INTENSIFIERS
# =========================================================================

PORTUGUESE_INTENSIFIERS: Dict[str, float] = {
    # Strong
    "muito": 1.4,
    "demais": 1.5,
    "extremamente": 1.8,
    "incrivelmente": 1.7,
    "totalmente": 1.6,
    "completamente": 1.6,
    "absolutamente": 1.7,
    "super": 1.5,
    "hiper": 1.5,
    "mega": 1.5,
    "ultra": 1.5,

    # Moderate
    "bastante": 1.3,
    "bem": 1.2,

    # Brazilian slang
    "mó": 1.4,  # "mó legal"
    "mo": 1.4,
    "bagarai": 1.5,  # demais
    "pra caramba": 1.6,
    "pra caralho": 1.7,

    # Diminishers
    "um pouco": 0.7,
    "um pouquinho": 0.6,
    "meio": 0.8,
    "tipo": 0.9,
    "quase": 0.7,
}
