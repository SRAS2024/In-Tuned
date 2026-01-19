# detector/lexicons/safety.py
"""
Comprehensive Safety Detection Module

This module provides expanded patterns for detecting:
- Self-harm and suicidal ideation
- Crisis indicators
- Help-seeking behavior

IMPORTANT: These patterns are designed to trigger safety resources,
not to diagnose or treat mental health conditions.
"""

from typing import Dict, List, Set

# =========================================================================
# ENGLISH SELF-HARM PATTERNS
# =========================================================================

# Hard patterns: Strong indicators requiring immediate safety response
SELF_HARM_PATTERNS_EN: Dict[str, List[str]] = {
    "hard": [
        # Direct suicide statements
        r"\bkill myself\b",
        r"\bkill\s+myself\b",
        r"\bend my life\b",
        r"\bend it all\b",
        r"\bending it all\b",
        r"\bput an end to it\b",
        r"\bno reason to live\b",
        r"\bnothing to live for\b",
        r"\bwant to die\b",
        r"\bwanna die\b",
        r"\bwant to be dead\b",
        r"\bwish i was dead\b",
        r"\bwish i were dead\b",
        r"\bwish was dead\b",
        r"\bbetter off dead\b",
        r"\bworld would be better without me\b",
        r"\beveryone would be better off\b",
        r"\bno one would miss me\b",
        r"\bnobody would care if i\b",

        # Suicide planning
        r"\bsuicide\b",
        r"\bsuicidal\b",
        r"\bcommit suicide\b",
        r"\bkms\b",  # kill myself
        r"\bctb\b",  # catch the bus (euphemism)
        r"\bgoing to end it\b",
        r"\bgonna end it\b",
        r"\bplanning to end\b",
        r"\bhave a plan\b.*\b(die|end|kill)\b",

        # Modern slang - self-harm
        r"\boff myself\b",
        r"\boffing myself\b",
        r"\boff thyself\b",
        r"\bunalive myself\b",
        r"\bunaliving myself\b",
        r"\bunalive\b",
        r"\bsewerslide\b",  # TikTok censorship bypass
        r"\bsewer slide\b",
        r"\bsu1c1de\b",
        r"\bs\*icide\b",
        r"\bselfdelete\b",
        r"\bself delete\b",
        r"\bpermanent solution\b",
        r"\bpermanent sleep\b",
        r"\beternal sleep\b",
        r"\bjoin the 27 club\b",  # die at 27

        # Self-harm statements
        r"\bself[-\s]?harm\b",
        r"\bself[-\s]?injury\b",
        r"\bhurt myself\b",
        r"\bhurting myself\b",
        r"\bcut myself\b",
        r"\bcutting myself\b",
        r"\bcuts on my\b",
        r"\bburning myself\b",
        r"\bburn myself\b",
        r"\bpunish myself\b",
        r"\bsh\b(?=.*\b(urges?|relapse|clean|streak))",  # SH context

        # Hopelessness/giving up
        r"\bcant go on\b",
        r"\bcan'?t go on\b",
        r"\bcannot go on\b",
        r"\bdone with life\b",
        r"\bdone living\b",
        r"\btired of living\b",
        r"\btired of being alive\b",
        r"\bgive up on life\b",
        r"\bgiving up on life\b",
        r"\bgave up on life\b",
        r"\bno point in living\b",
        r"\bwhat'?s the point\b.*\b(living|life|anymore)\b",
        r"\bno hope left\b",
        r"\blast resort\b",
        r"\bfinal goodbye\b",
        r"\bsaying goodbye\b.*\bforever\b",
        r"\bwon'?t be here much longer\b",
        r"\bwon'?t be around\b.*\bmuch longer\b",
    ],

    # Soft patterns: May indicate distress but need context
    # (humor, hyperbole, or genuine crisis)
    "soft": [
        # Hyperbolic expressions (often used casually)
        r"\bkill me\b",
        r"\bi'?m dead\b",
        r"\bim dead\b",
        r"\bdead inside\b",
        r"\bwant to disappear\b",
        r"\bwanna disappear\b",
        r"\bjust disappear\b",
        r"\bfade away\b",
        r"\brun away from everything\b",
        r"\bescape everything\b",

        # Mild distress signals
        r"\bcan'?t take it anymore\b",
        r"\bcant take it\b",
        r"\bcan'?t deal\b",
        r"\bcant deal\b",
        r"\bover it\b",
        r"\bso done\b",
        r"\bi'?m done\b",
        r"\bim done\b",
        r"\bneed to escape\b",
        r"\bneed an escape\b",
        r"\bwant it to stop\b",
        r"\bmake it stop\b",
    ],
}

# =========================================================================
# SPANISH SELF-HARM PATTERNS
# =========================================================================

SELF_HARM_PATTERNS_ES: Dict[str, List[str]] = {
    "hard": [
        # Direct suicide statements
        r"\bquiero morir\b",
        r"\bme quiero morir\b",
        r"\bdeseo morir\b",
        r"\bquiero morirme\b",
        r"\bno quiero vivir\b",
        r"\bno quiero seguir viviendo\b",
        r"\bya no quiero vivir\b",
        r"\bprefiero morir\b",
        r"\bestaria mejor muerto\b",
        r"\bestaria mejor muerta\b",
        r"\bmejor muerto\b",
        r"\bmejor muerta\b",
        r"\bestarían mejor sin mi\b",
        r"\bestarian mejor sin mi\b",
        r"\bnadie me extrañaría\b",
        r"\bnadie me extrañaria\b",
        r"\ba nadie le importo\b",

        # Suicide planning/methods
        r"\bsuicidio\b",
        r"\bsuicidarme\b",
        r"\bquitarme la vida\b",
        r"\bacabar con mi vida\b",
        r"\bacabar con todo\b",
        r"\bterminar con todo\b",
        r"\bponer fin a mi vida\b",
        r"\bponer fin a todo\b",
        r"\bmatarme\b",
        r"\bme voy a matar\b",
        r"\bvoy a matarme\b",

        # Self-harm
        r"\bautolesi[oó]n\b",
        r"\bautolesionarme\b",
        r"\bhacerme da[ñn]o\b",
        r"\bme hago da[ñn]o\b",
        r"\bcortarme\b",
        r"\bme corto\b",
        r"\bquemarme\b",
        r"\bme quemo\b",

        # Hopelessness
        r"\bno puedo m[aá]s\b",
        r"\bya no puedo m[aá]s\b",
        r"\bno aguanto m[aá]s\b",
        r"\bya no aguanto\b",
        r"\bno tengo raz[oó]n para vivir\b",
        r"\bsin raz[oó]n para vivir\b",
        r"\bsin ganas de vivir\b",
        r"\bperd[ií] las ganas de vivir\b",
        r"\bno hay esperanza\b",
        r"\bsin esperanza\b",
        r"\btodo est[aá] perdido\b",
        r"\bme rindo\b",
        r"\bme doy por vencido\b",
        r"\bme doy por vencida\b",
    ],

    "soft": [
        # Hyperbolic expressions
        r"\bme muero\b",
        r"\bquiero desaparecer\b",
        r"\bdesaparecer\b",
        r"\bescapar de todo\b",
        r"\bhuir de todo\b",

        # Mild distress
        r"\bno puedo seguir\b",
        r"\bya no puedo\b",
        r"\bestoy hart[oa]\b",
        r"\bno aguanto\b",
        r"\bnecesito escapar\b",
    ],
}

# =========================================================================
# PORTUGUESE SELF-HARM PATTERNS
# =========================================================================

SELF_HARM_PATTERNS_PT: Dict[str, List[str]] = {
    "hard": [
        # Direct suicide statements
        r"\bquero morrer\b",
        r"\beu quero morrer\b",
        r"\bdesejo morrer\b",
        r"\bn[aã]o quero viver\b",
        r"\bn[aã]o quero mais viver\b",
        r"\bprefiro morrer\b",
        r"\bestaria melhor morto\b",
        r"\bestaria melhor morta\b",
        r"\bmelhor morto\b",
        r"\bmelhor morta\b",
        r"\bestariam melhor sem mim\b",
        r"\bningu[eé]m sentiria minha falta\b",
        r"\bninguem sentiria minha falta\b",
        r"\bningu[eé]m se importa\b",
        r"\bninguem se importa\b",
        r"\bningu[eé]m liga pra mim\b",

        # Suicide planning
        r"\bsuic[ií]dio\b",
        r"\bme matar\b",
        r"\bvou me matar\b",
        r"\bquero me matar\b",
        r"\bqueria me matar\b",
        r"\btirar minha vida\b",
        r"\btirar a minha vida\b",
        r"\bacabar com tudo\b",
        r"\bacabar com a minha vida\b",
        r"\bdar fim a tudo\b",
        r"\bdar fim [aà] minha vida\b",

        # Self-harm
        r"\bauto[-\s]?mutila[çc][aã]o\b",
        r"\bauto[-\s]?les[aã]o\b",
        r"\bme machucar\b",
        r"\bme machuco\b",
        r"\bme cortar\b",
        r"\bme corto\b",
        r"\bme queimar\b",
        r"\bme queimo\b",

        # Hopelessness
        r"\bn[aã]o aguento mais\b",
        r"\bnao aguento mais\b",
        r"\beu n[aã]o aguento\b",
        r"\bn[aã]o consigo mais\b",
        r"\bn[aã]o d[aá] mais\b",
        r"\bnao da mais\b",
        r"\bperdi a vontade de viver\b",
        r"\bsem vontade de viver\b",
        r"\bsem raz[aã]o para viver\b",
        r"\bsem esperan[çc]a\b",
        r"\bn[aã]o h[aá] esperan[çc]a\b",
        r"\bdesisti de tudo\b",
        r"\bvou desistir\b",
        r"\beu desisto\b",
        r"\bme rendo\b",
        r"\bto cansado de viver\b",
        r"\bto cansada de viver\b",
        r"\bcansado de existir\b",
        r"\bcansada de existir\b",
    ],

    "soft": [
        # Hyperbolic expressions
        r"\bme quero morrer\b",  # softer form
        r"\bto morrendo\b",  # casual "I'm dying"
        r"\bquero sumir\b",
        r"\bquero desaparecer\b",
        r"\bfugir de tudo\b",

        # Mild distress
        r"\bn[aã]o consigo continuar\b",
        r"\bn[aã]o d[aá] pra continuar\b",
        r"\bto de saco cheio\b",
        r"\bpreciso fugir\b",
        r"\bpreciso escapar\b",
    ],
}

# =========================================================================
# CRISIS INDICATORS (UNIVERSAL)
# =========================================================================

# These patterns indicate someone may be in acute crisis
CRISIS_INDICATORS: Dict[str, Set[str]] = {
    # Time urgency
    "urgency": {
        "tonight", "today", "right now", "this moment",
        "before tomorrow", "cant wait", "running out of time",
        "esta noche", "ahora mismo", "ahora", "hoy",
        "hoje", "agora", "agora mesmo",
    },

    # Finality language
    "finality": {
        "goodbye", "final", "last", "never again", "forever",
        "the end", "its over", "all over",
        "adios", "despedida", "final", "último", "ultima", "nunca más",
        "adeus", "tchau pra sempre", "final", "ultimo", "ultima", "nunca mais",
    },

    # Giving away / settling affairs
    "settling": {
        "giving away", "give away my", "take care of my",
        "will says", "my belongings", "who gets",
        "regalar mis", "quiero que tengas", "cuida de mi",
        "dando minhas coisas", "quero que fique com", "cuida do meu",
    },

    # Recent loss/trauma
    "trauma": {
        "just lost", "died yesterday", "found out",
        "cant believe", "in shock", "devastating",
        "acabo de perder", "murió", "murio", "me enteré", "me entere",
        "acabei de perder", "morreu", "descobri", "recebi a notícia",
    },

    # Help-seeking (POSITIVE indicators - person seeking help)
    "help_seeking": {
        "need help", "help me", "someone help",
        "dont know what to do", "who can i talk to",
        "crisis line", "hotline", "suicide hotline",
        "necesito ayuda", "ayúdame", "ayudame", "alguien que me ayude",
        "preciso de ajuda", "me ajuda", "alguém me ajuda", "alguem me ajuda",
    },
}

# =========================================================================
# HELPER FUNCTIONS
# =========================================================================

def get_all_hard_patterns() -> List[str]:
    """Get all hard self-harm patterns across languages."""
    patterns = []
    patterns.extend(SELF_HARM_PATTERNS_EN["hard"])
    patterns.extend(SELF_HARM_PATTERNS_ES["hard"])
    patterns.extend(SELF_HARM_PATTERNS_PT["hard"])
    return patterns


def get_all_soft_patterns() -> List[str]:
    """Get all soft self-harm patterns across languages."""
    patterns = []
    patterns.extend(SELF_HARM_PATTERNS_EN["soft"])
    patterns.extend(SELF_HARM_PATTERNS_ES["soft"])
    patterns.extend(SELF_HARM_PATTERNS_PT["soft"])
    return patterns


def get_patterns_for_language(lang: str) -> Dict[str, List[str]]:
    """Get self-harm patterns for a specific language."""
    lang = lang.lower()[:2]
    if lang == "en":
        return SELF_HARM_PATTERNS_EN
    elif lang == "es":
        return SELF_HARM_PATTERNS_ES
    elif lang == "pt":
        return SELF_HARM_PATTERNS_PT
    # Return all patterns if language unknown
    return {
        "hard": get_all_hard_patterns(),
        "soft": get_all_soft_patterns(),
    }
