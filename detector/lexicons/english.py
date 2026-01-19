# detector/lexicons/english.py
"""
Comprehensive English Emotion Lexicon

Includes:
- Core emotion vocabulary
- Modern slang (Gen Z, Millennial, Internet culture)
- Pop culture references
- Intensifiers and modifiers
- Idiomatic expressions
"""

from typing import Dict, List, Tuple

# Format: {word: {emotion: weight}}
# Higher weights (2.0-3.0) = strong indicators
# Medium weights (1.0-2.0) = moderate indicators
# Lower weights (0.5-1.0) = weak/context-dependent indicators


def _build_lexicon() -> Dict[str, Dict[str, float]]:
    """Build the complete English lexicon."""
    lex: Dict[str, Dict[str, float]] = {}

    def add(emotion: str, words: List[str], weight: float) -> None:
        for w in words:
            w_norm = w.lower().replace(" ", "_").replace("-", "")
            if w_norm not in lex:
                lex[w_norm] = {}
            lex[w_norm][emotion] = lex[w_norm].get(emotion, 0.0) + weight

    # =========================================================================
    # ANGER
    # =========================================================================

    # Core anger words
    add("anger", [
        "angry", "mad", "furious", "enraged", "irate", "livid", "fuming",
        "outraged", "incensed", "infuriated", "seething", "raging", "wrathful",
        "indignant", "exasperated", "aggravated", "irritated", "annoyed",
        "frustrated", "resentful", "bitter", "hostile", "antagonistic",
    ], 2.2)

    # Anger verbs
    add("anger", [
        "hate", "hated", "hates", "hating", "loathe", "loathed", "loathes",
        "despise", "despised", "despises", "detest", "detested", "detests",
        "resent", "resented", "resents", "resenting",
    ], 2.3)

    # Modern slang - anger
    add("anger", [
        "pissed", "pissedoff", "ticked", "tickedoff", "salty", "pressed",
        "triggered", "tilted", "heated", "tight", "vexed", "miffed",
        "butthurt", "butthurt", "riled", "riledup", "aggy", "aggro",
    ], 2.0)

    # Internet/Gen Z anger
    add("anger", [
        "ugh", "smh", "smfh", "ffs", "jfc", "wtf", "tf", "wth", "omfg",
        "istg", "istfg", "ngl", "deadass", "lowkey_mad", "highkey_mad",
        "im_done", "imdone", "over_it", "overit", "sick_of", "sickof",
        "tired_of", "tiredof", "fed_up", "fedup", "had_it", "hadit",
    ], 1.8)

    # Anger insults/expressions
    add("anger", [
        "stupid", "idiot", "idiots", "idiotic", "dumb", "dumbass",
        "moron", "morons", "moronic", "fool", "fools", "foolish",
        "trash", "garbage", "bs", "bullshit", "bs'ing",
        "clown", "clowns", "clownery", "joke", "jokes", "pathetic",
        "ridiculous", "absurd", "unbelievable", "unacceptable",
    ], 1.8)

    # Profanity-based anger
    add("anger", [
        "damn", "dammit", "damnit", "crap", "hell", "bloody", "freaking",
        "frickin", "friggin", "frick", "fudge", "shoot", "heck",
    ], 1.5)

    # =========================================================================
    # DISGUST
    # =========================================================================

    # Core disgust
    add("disgust", [
        "disgusted", "disgusting", "gross", "grossed", "nasty", "repulsed",
        "repulsive", "revolted", "revolting", "sickened", "sickening",
        "nauseated", "nauseating", "nauseous", "queasy", "appalled",
        "appalling", "abhorrent", "vile", "foul", "putrid", "rancid",
    ], 2.2)

    # Disgust exclamations
    add("disgust", [
        "yuck", "yucky", "ew", "eww", "ewww", "ick", "icky", "bleh",
        "blech", "barf", "barfing", "gag", "gagging", "puke", "puking",
    ], 2.0)

    # Modern slang - disgust
    add("disgust", [
        "cringe", "cringy", "cringe", "cringey", "cringeworthy",
        "sus", "sussy", "sketchy", "shady", "iffy", "off", "offputting",
        "weird", "weirdo", "creepy", "creep", "creeps", "yikes",
        "oof", "big_yikes", "bigyikes", "nope", "hard_pass", "hardpass",
    ], 1.8)

    # Disgust descriptions
    add("disgust", [
        "filthy", "dirty", "grimy", "slimy", "greasy", "oily", "sticky",
        "smelly", "stinky", "rank", "rotten", "moldy", "mouldy",
        "crusty", "musty", "dusty", "scummy", "sleazy", "trashy",
    ], 1.7)

    # =========================================================================
    # FEAR / ANXIETY
    # =========================================================================

    # Core fear
    add("fear", [
        "afraid", "scared", "frightened", "terrified", "petrified",
        "horrified", "alarmed", "panicked", "panicking", "panic",
        "fearful", "dreading", "dread", "dreaded",
    ], 2.3)

    # Anxiety words
    add("fear", [
        "anxious", "anxiety", "worried", "worrying", "worry", "worried",
        "nervous", "nervousness", "uneasy", "unease", "apprehensive",
        "tense", "stressed", "stressful", "stress", "stressing",
        "overwhelmed", "overwhelming", "overthinking", "spiraling",
    ], 2.2)

    # Modern anxiety slang
    add("fear", [
        "paranoid", "paranoia", "freaking_out", "freakingout", "freaked",
        "shook", "shooketh", "spooked", "creeped_out", "creepedout",
        "lowkey_scared", "highkey_scared", "lowkey_anxious",
        "on_edge", "onedge", "edgy", "jittery", "jumpy", "antsy",
    ], 1.9)

    # Phobia/intense fear
    add("fear", [
        "phobia", "phobic", "terror", "terrorized", "haunted", "haunting",
        "nightmare", "nightmarish", "traumatized", "traumatic", "trauma",
        "ptsd", "triggered", "flashback", "flashbacks",
    ], 2.0)

    # Uncertainty/worry
    add("fear", [
        "uncertain", "uncertainty", "unsure", "doubtful", "doubt",
        "hesitant", "reluctant", "wary", "cautious", "concerned",
        "concerning", "troubling", "disturbing", "alarming",
    ], 1.5)

    # =========================================================================
    # JOY / HAPPINESS
    # =========================================================================

    # Core joy
    add("joy", [
        "happy", "happier", "happiest", "happiness", "joyful", "joyous",
        "delighted", "delightful", "pleased", "glad", "elated", "ecstatic",
        "euphoric", "thrilled", "overjoyed", "blissful", "bliss",
    ], 2.2)

    # Contentment
    add("joy", [
        "content", "contented", "satisfied", "satisfying", "fulfilling",
        "fulfilled", "peaceful", "serene", "tranquil", "calm", "relaxed",
        "at_ease", "comfortable", "cozy", "comfy",
    ], 1.8)

    # Excitement/enthusiasm
    add("joy", [
        "excited", "exciting", "excitement", "enthusiastic", "eager",
        "pumped", "stoked", "hyped", "hype", "amped", "psyched",
        "fired_up", "firedp", "raring", "ready", "cant_wait", "cantwait",
    ], 2.0)

    # Gratitude
    add("joy", [
        "grateful", "thankful", "appreciative", "blessed", "fortunate",
        "lucky", "thank_you", "thankyou", "thanks", "thx", "ty",
    ], 1.8)

    # Modern slang - joy
    add("joy", [
        "lit", "litty", "fire", "bussin", "bussing", "slaps", "slap",
        "hits_different", "hitsdifferent", "vibe", "vibes", "vibing",
        "slay", "slayed", "slaying", "iconic", "queen", "king",
        "goat", "goated", "legendary", "epic", "based", "valid",
    ], 1.9)

    # Internet expressions - joy
    add("joy", [
        "lol", "lmao", "lmfao", "rofl", "roflmao", "haha", "hahaha",
        "hehe", "hihi", "teehee", "lololol", "lulz", "kek",
        "xd", "xdd", "xddd", ":)", ":d", "c:", ":3",
    ], 1.7)

    # Positive affirmations
    add("joy", [
        "awesome", "amazing", "wonderful", "fantastic", "fabulous",
        "terrific", "excellent", "brilliant", "superb", "outstanding",
        "incredible", "magnificent", "marvelous", "phenomenal",
        "great", "good", "nice", "lovely", "beautiful", "perfect",
    ], 1.8)

    # Gen Z positive
    add("joy", [
        "dope", "sick", "rad", "cool", "chill", "chillin", "chilling",
        "no_cap", "nocap", "fr", "fr_fr", "frfr", "real", "facts",
        "periodt", "period", "ong", "on_god", "ongod", "bet",
        "w", "dub", "winning", "win", "winning",
    ], 1.6)

    # Small affirmations (low weight for short inputs)
    add("joy", [
        "ok", "okay", "okey", "alright", "aight", "sure", "fine",
        "yay", "yayy", "yayyy", "yess", "yesss", "yup", "yeah", "yea",
        "woo", "wooo", "woot", "woohoo", "yippee",
    ], 0.9)

    # =========================================================================
    # SADNESS
    # =========================================================================

    # Core sadness
    add("sadness", [
        "sad", "sadder", "saddest", "sadness", "unhappy", "sorrowful",
        "sorrow", "melancholy", "melancholic", "dejected", "despondent",
        "disheartened", "downcast", "crestfallen", "woeful", "woe",
    ], 2.3)

    # Depression-related
    add("sadness", [
        "depressed", "depressing", "depression", "hopeless", "hopelessness",
        "despair", "despairing", "desperate", "miserable", "misery",
        "wretched", "anguish", "anguished", "tormented", "suffering",
    ], 2.4)

    # Grief/loss
    add("sadness", [
        "grief", "grieving", "mourning", "loss", "lost", "bereaved",
        "heartbroken", "heartbreak", "heartache", "brokenhearted",
        "devastated", "devastating", "shattered", "crushed",
    ], 2.3)

    # Loneliness
    add("sadness", [
        "lonely", "loneliness", "alone", "isolated", "isolation",
        "abandoned", "forsaken", "neglected", "rejected", "unwanted",
        "unloved", "forgotten", "invisible",
    ], 2.1)

    # Modern slang - sadness
    add("sadness", [
        "down", "down_bad", "downbad", "in_my_feels", "inmyfeels",
        "feeling_some_type_of_way", "hurting", "aching", "crying",
        "sobbing", "weeping", "tearing_up", "tearingup", "teary",
    ], 2.0)

    # Exhaustion/burnout
    add("sadness", [
        "drained", "exhausted", "depleted", "burnt_out", "burntout",
        "burned_out", "burnedout", "empty", "hollow", "numb", "dead_inside",
        "deadinside", "broken", "worn_out", "wornout", "spent",
    ], 1.9)

    # Mild sadness
    add("sadness", [
        "meh", "blah", "low", "blue", "bummed", "bummer", "disappointing",
        "disappointed", "letdown", "let_down", "upset", "upsetting",
        "not_okay", "notokay", "not_fine", "notfine", "not_good", "notgood",
    ], 1.6)

    # =========================================================================
    # PASSION / LOVE
    # =========================================================================

    # Core love
    add("passion", [
        "love", "loved", "loves", "loving", "adore", "adored", "adores",
        "adoring", "cherish", "cherished", "cherishes", "treasure",
    ], 2.3)

    # Romantic love
    add("passion", [
        "inlove", "in_love", "smitten", "enamored", "enamoured",
        "infatuated", "infatuation", "devoted", "devotion", "enchanted",
        "captivated", "bewitched", "spellbound", "head_over_heels",
    ], 2.4)

    # Desire/attraction
    add("passion", [
        "desire", "desired", "desires", "desiring", "want", "wanting",
        "crave", "craved", "craves", "craving", "yearn", "yearning",
        "longing", "pining", "attracted", "attraction", "chemistry",
    ], 2.1)

    # Modern slang - passion
    add("passion", [
        "crush", "crushing", "crushin", "simping", "simp", "simps",
        "stan", "stanning", "stans", "ship", "shipping", "shipped",
        "otp", "endgame", "goals", "relationship_goals", "couple_goals",
    ], 1.9)

    # Affection terms
    add("passion", [
        "bae", "babe", "baby", "honey", "sweetheart", "darling", "dear",
        "love", "my_love", "mylove", "soulmate", "my_person", "myperson",
        "my_world", "myworld", "my_everything", "myeverything",
    ], 2.0)

    # Physical attraction
    add("passion", [
        "hot", "sexy", "gorgeous", "beautiful", "handsome", "stunning",
        "attractive", "cute", "cutie", "adorable", "fine", "foine",
        "thirsty", "thirst", "hornball", "horny",
    ], 1.7)

    # =========================================================================
    # SURPRISE
    # =========================================================================

    # Core surprise
    add("surprise", [
        "surprised", "surprising", "surprise", "astonished", "astonishing",
        "amazed", "amazing", "astounded", "astounding", "stunned",
        "stunning", "shocked", "shocking", "startled", "startling",
    ], 2.2)

    # Disbelief
    add("surprise", [
        "unbelievable", "incredible", "inconceivable", "mindblowing",
        "mind_blowing", "jaw_dropping", "jawdropping", "breathtaking",
        "cant_believe", "cantbelieve", "cannot_believe", "cannotbelieve",
    ], 2.0)

    # Exclamations
    add("surprise", [
        "wow", "woah", "whoa", "omg", "omfg", "oh_my_god", "ohmygod",
        "what", "wtf", "wth", "huh", "no_way", "noway", "seriously",
        "really", "for_real", "forreal",
    ], 1.8)

    # Modern slang - surprise
    add("surprise", [
        "shook", "shooketh", "shaking", "im_shook", "imshook",
        "dead", "im_dead", "imdead", "dying", "im_dying", "imdying",
        "screaming", "im_screaming", "imscreaming", "crying", "im_crying",
        "i_cant", "icant", "i_cant_even", "icanteven",
    ], 1.9)

    # Unexpected
    add("surprise", [
        "unexpected", "unforeseen", "out_of_nowhere", "outofnowhere",
        "random", "plot_twist", "plottwist", "twist", "suddenly",
        "all_of_a_sudden", "didnt_see_that_coming",
    ], 1.6)

    return lex


ENGLISH_LEXICON = _build_lexicon()


# =========================================================================
# PHRASE LEXICON
# =========================================================================

def _vec(**kw: float) -> Dict[str, float]:
    """Create emotion vector."""
    v = {"anger": 0.0, "disgust": 0.0, "fear": 0.0, "joy": 0.0,
         "sadness": 0.0, "passion": 0.0, "surprise": 0.0}
    v.update(kw)
    return v


ENGLISH_PHRASES: Dict[str, Dict[str, float]] = {
    # Joy phrases
    "on cloud nine": _vec(joy=3.0),
    "over the moon": _vec(joy=3.0),
    "walking on sunshine": _vec(joy=2.8),
    "on top of the world": _vec(joy=2.8),
    "living my best life": _vec(joy=2.5),
    "good vibes only": _vec(joy=2.0),
    "feeling myself": _vec(joy=2.2),
    "living the dream": _vec(joy=2.3),
    "couldnt be happier": _vec(joy=2.8),
    "best day ever": _vec(joy=2.5),
    "this made my day": _vec(joy=2.3),
    "you made my day": _vec(joy=2.5),
    "so happy right now": _vec(joy=2.4),
    "i love this": _vec(joy=2.0, passion=1.0),
    "i love it": _vec(joy=2.0, passion=1.0),
    "this slaps": _vec(joy=2.2),
    "hits different": _vec(joy=2.0),
    "no cap this is fire": _vec(joy=2.3),
    "lets go": _vec(joy=1.8, surprise=0.8),
    "lets gooo": _vec(joy=2.2, surprise=1.0),

    # Anger phrases
    "pissed off": _vec(anger=2.8),
    "ticked off": _vec(anger=2.3),
    "fed up": _vec(anger=2.0, sadness=1.0),
    "at my wits end": _vec(anger=1.8, sadness=1.8),
    "at the end of my rope": _vec(anger=1.5, sadness=2.0),
    "lost my patience": _vec(anger=2.2),
    "losing my mind": _vec(anger=1.8, fear=1.5),
    "drives me crazy": _vec(anger=2.0),
    "makes my blood boil": _vec(anger=2.8),
    "seeing red": _vec(anger=2.5),
    "im so done": _vec(anger=2.0, sadness=1.0),
    "done with this": _vec(anger=2.0),
    "over it": _vec(anger=1.8, sadness=1.0),
    "sick of this": _vec(anger=2.0, disgust=1.5),
    "tired of this": _vec(anger=1.8, sadness=1.2),
    "i hate this": _vec(anger=2.5),
    "i hate you": _vec(anger=3.0),
    "go to hell": _vec(anger=2.8),
    "screw you": _vec(anger=2.5),
    "what the hell": _vec(anger=2.0, surprise=1.0),
    "are you kidding me": _vec(anger=2.0, surprise=1.5),
    "you have got to be kidding": _vec(anger=2.0, surprise=1.5),
    "this is ridiculous": _vec(anger=2.2),
    "this is absurd": _vec(anger=2.0),
    "this is bs": _vec(anger=2.3),
    "this is bullshit": _vec(anger=2.5),

    # Sadness phrases
    "heartbroken": _vec(sadness=3.0),
    "heart broken": _vec(sadness=3.0),
    "my heart hurts": _vec(sadness=2.8),
    "my heart aches": _vec(sadness=2.6),
    "feeling empty": _vec(sadness=2.5),
    "feeling hollow": _vec(sadness=2.4),
    "in a dark place": _vec(sadness=2.6, fear=1.0),
    "down in the dumps": _vec(sadness=2.2),
    "feeling low": _vec(sadness=2.0),
    "feeling down": _vec(sadness=2.0),
    "not doing well": _vec(sadness=2.0),
    "not okay": _vec(sadness=2.2),
    "im not okay": _vec(sadness=2.4),
    "im not fine": _vec(sadness=2.3),
    "its been hard": _vec(sadness=2.0),
    "struggling lately": _vec(sadness=2.2),
    "going through a lot": _vec(sadness=2.3),
    "going through it": _vec(sadness=2.2),
    "miss you": _vec(sadness=2.0, passion=1.5),
    "i miss you": _vec(sadness=2.2, passion=1.8),
    "i miss you so much": _vec(sadness=2.5, passion=2.0),
    "wish you were here": _vec(sadness=2.3, passion=1.5),
    "cant stop crying": _vec(sadness=2.8),
    "cried myself to sleep": _vec(sadness=3.0),
    "crying my eyes out": _vec(sadness=2.8),
    "tears wont stop": _vec(sadness=2.6),
    "in my feels": _vec(sadness=2.0),
    "down bad": _vec(sadness=2.2, passion=1.0),

    # Fear/anxiety phrases
    "scared to death": _vec(fear=3.0),
    "scared out of my mind": _vec(fear=2.8),
    "freaking out": _vec(fear=2.5),
    "having a panic attack": _vec(fear=3.0),
    "cant breathe": _vec(fear=2.8),
    "heart is racing": _vec(fear=2.3),
    "on edge": _vec(fear=2.0),
    "walking on eggshells": _vec(fear=2.2),
    "worried sick": _vec(fear=2.5),
    "cant stop thinking about": _vec(fear=1.8),
    "what if": _vec(fear=1.5),
    "im so scared": _vec(fear=2.6),
    "im terrified": _vec(fear=2.8),
    "this is scary": _vec(fear=2.2),
    "gives me anxiety": _vec(fear=2.3),
    "having anxiety": _vec(fear=2.4),
    "so anxious": _vec(fear=2.3),
    "stressed out": _vec(fear=2.2),
    "stressed af": _vec(fear=2.3),
    "losing sleep over": _vec(fear=2.0, sadness=1.0),
    "cant sleep": _vec(fear=1.8, sadness=1.5),

    # Disgust phrases
    "makes me sick": _vec(disgust=2.5),
    "sick to my stomach": _vec(disgust=2.8),
    "want to throw up": _vec(disgust=2.5),
    "makes me want to puke": _vec(disgust=2.6),
    "grossed out": _vec(disgust=2.3),
    "so gross": _vec(disgust=2.2),
    "thats disgusting": _vec(disgust=2.4),
    "thats nasty": _vec(disgust=2.2),
    "ew no": _vec(disgust=2.0),
    "hard pass": _vec(disgust=1.8),
    "thats so cringe": _vec(disgust=2.0),
    "cringe af": _vec(disgust=2.1),
    "big yikes": _vec(disgust=2.0, surprise=1.0),
    "major yikes": _vec(disgust=2.0, surprise=1.0),
    "not it": _vec(disgust=1.5),
    "aint it": _vec(disgust=1.5),

    # Passion/love phrases
    "head over heels": _vec(passion=3.0),
    "falling for you": _vec(passion=2.8),
    "fallen for you": _vec(passion=2.8),
    "in love with you": _vec(passion=3.0),
    "love you so much": _vec(passion=3.0),
    "i love you": _vec(passion=2.8),
    "love of my life": _vec(passion=3.0),
    "my everything": _vec(passion=2.8),
    "you mean everything": _vec(passion=2.8),
    "cant live without you": _vec(passion=2.8, fear=1.0),
    "youre my world": _vec(passion=2.7),
    "crazy about you": _vec(passion=2.6),
    "obsessed with you": _vec(passion=2.5),
    "to die for": _vec(passion=2.2, joy=1.0),
    "have a crush on": _vec(passion=2.3),
    "crushing hard": _vec(passion=2.4),
    "simping hard": _vec(passion=2.2),
    "such a simp": _vec(passion=1.8),
    "they are goals": _vec(passion=2.0, joy=1.0),
    "couple goals": _vec(passion=2.2, joy=1.0),
    "relationship goals": _vec(passion=2.2, joy=1.0),

    # Surprise phrases
    "cant believe it": _vec(surprise=2.5),
    "i cant believe": _vec(surprise=2.3),
    "no way": _vec(surprise=2.2),
    "get out": _vec(surprise=2.0),
    "shut up": _vec(surprise=1.8),
    "are you serious": _vec(surprise=2.2),
    "you are joking": _vec(surprise=2.0),
    "out of nowhere": _vec(surprise=2.0),
    "did not see that coming": _vec(surprise=2.3),
    "plot twist": _vec(surprise=2.2),
    "mind blown": _vec(surprise=2.5),
    "blew my mind": _vec(surprise=2.4),
    "im shook": _vec(surprise=2.3),
    "im dead": _vec(surprise=2.2, joy=1.0),
    "im screaming": _vec(surprise=2.2, joy=1.0),
    "i cant even": _vec(surprise=2.0),

    # Pop culture references
    "its giving": _vec(joy=1.5),
    "no cap": _vec(joy=1.2),
    "on god": _vec(joy=1.3),
    "finna": _vec(joy=1.0),
    "bussin bussin": _vec(joy=2.3),
    "understood the assignment": _vec(joy=2.2),
    "ate that": _vec(joy=2.2),
    "ate and left no crumbs": _vec(joy=2.5),
    "main character energy": _vec(joy=2.0),
    "villain era": _vec(anger=1.5, joy=1.0),
    "roman empire": _vec(passion=1.5),
    "rent free": _vec(passion=1.8),
    "living rent free": _vec(passion=2.0),
    "core memory": _vec(joy=2.0, sadness=1.0),
    "ick": _vec(disgust=2.0),
    "giving me the ick": _vec(disgust=2.3),
    "red flag": _vec(fear=1.5, disgust=1.5),
    "green flag": _vec(joy=1.8, passion=1.0),
    "beige flag": _vec(surprise=1.0),
    "touch grass": _vec(anger=1.5),
    "chronically online": _vec(disgust=1.5),
}


# =========================================================================
# INTENSIFIERS
# =========================================================================

ENGLISH_INTENSIFIERS: Dict[str, float] = {
    # Strong intensifiers (1.5-2.0x)
    "extremely": 1.8,
    "incredibly": 1.7,
    "absolutely": 1.7,
    "completely": 1.6,
    "totally": 1.5,
    "utterly": 1.7,
    "thoroughly": 1.5,
    "deeply": 1.6,
    "immensely": 1.7,
    "intensely": 1.7,

    # Moderate intensifiers (1.2-1.5x)
    "very": 1.4,
    "really": 1.4,
    "so": 1.3,
    "quite": 1.2,
    "pretty": 1.2,
    "fairly": 1.1,
    "rather": 1.2,
    "somewhat": 1.1,

    # Slang intensifiers
    "hella": 1.5,
    "mad": 1.4,
    "super": 1.4,
    "mega": 1.5,
    "ultra": 1.5,
    "lowkey": 0.8,
    "highkey": 1.5,
    "deadass": 1.5,
    "straight_up": 1.4,
    "legit": 1.3,
    "literally": 1.4,
    "fr": 1.3,
    "frfr": 1.5,
    "ong": 1.4,

    # Diminishers (0.5-0.9x)
    "slightly": 0.7,
    "somewhat": 0.8,
    "a_bit": 0.7,
    "a_little": 0.7,
    "kinda": 0.8,
    "kind_of": 0.8,
    "sorta": 0.8,
    "sort_of": 0.8,

    # Superlatives
    "most": 1.6,
    "least": 0.5,
}
