const $ = (id) => document.getElementById(id);

/* ---------- Per tab session support ---------- */

function createUUID() {
  if (window.crypto && window.crypto.randomUUID) {
    return window.crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getSessionId() {
  try {
    let sid = sessionStorage.getItem("in-tuned-session");
    if (!sid) {
      sid = createUUID();
      sessionStorage.setItem("in-tuned-session", sid);
    }
    return sid;
  } catch {
    return createUUID();
  }
}

const SESSION_ID = getSessionId();

/* ---------- Locales: EN, ES, PT only ---------- */

const LOCALES = {
  en: {
    name: "English",
    short: "EN",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Emotion detector",
      subtitle:
        "A simple space to notice what you are feeling across seven core emotions.",
      inputLabel: "Text",
      inputPlaceholder:
        "Type a short passage. For example: I am grateful and excited to begin something new today.",
      wordInfoDefault: "250 word maximum",
      wordsLabel: "words",
      analyzeButton: "Analyze",
      coreMixtureTitle: "Core mixture",
      analysisTitle: "Analysis",
      resultsTitle: "Results",
      resultsDominantLabel: "Dominant",
      resultsEmotionLabel: "Current emotion",
      resultsSecondaryLabel: "Secondary",
      resultsMixedLabel: "Mixed state",
      resultsMixedYes: "Yes",
      resultsMixedNo: "No",
      resultsValenceLabel: "Valence",
      resultsActivationLabel: "Activation",
      resultsIntensityLabel: "Intensity",
      resultsConfidenceLabel: "Confidence",
      resultsPatternLabel: "Pattern",
      resultsPrototypeLabel: "Closest tone",
      footer: "© 2025 In tuned. All rights reserved.",
      aboutTitle: "About In tuned",
      aboutDescriptionLabel: "Description:",
      aboutBody:
        "In tuned is an intuitive reflection tool that helps you understand what you are feeling in the moment. You write a short passage of up to 250 words and the app highlights a blend of seven core emotions anger, disgust, fear, joy, sadness, passion, and surprise so you can see a simple emotional snapshot of your text. The goal is to support self awareness and healthy reflection only. It is not therapy and it is not a substitute for professional mental health care or medical advice.",
      aboutDone: "Done",
      statusEnterText: "Please enter some text.",
      statusAnalyzing: "Analyzing...",
      statusLowSignal:
        "Too little text to understand how you feel. Try adding a bit more detail.",
      statusNeedAnalysis: "Run an analysis before adding to journal.",
      crisisTitle: "Wait! You are priceless and important.",
      crisisBody:
        "If you or your loved ones are having any thoughts of self harm or suicide, help is always available to you. This world needs you in it.",
      crisisNote:
        "If you feel that you might be in danger, please contact a trusted crisis hotline or your local emergency services right away.",
      crisisHotlineCta: "Contact suicide hotline",
      crisisEmergencyCta: "Contact emergency services",
      crisisClose: "Close",
      langMenuLabel: "Language",
      langSwitchTooltip: "Change language",
      helpButtonLabel: "About In tuned",
      themeToggleLabel: "Toggle light or dark theme",
      settingsThemeLabel: "Theme",
      settingsLanguageLabel: "Language",
      journalNewTitle: "New journal entry",
      journalOriginalTextLabel: "Original text",
      journalAnalysisSnapshotLabel: "Analysis snapshot",
      journalJournalLabel: "Journal",
      journalCancel: "Cancel",
      journalSave: "Save",
      journalDefaultTitle: "Journal entry",
      journalPin: "Pin",
      journalUnpin: "Unpin",
      accountLabel: "Account",
      loginButtonLabel: "Log in",
      maintenanceTitle: "In tuned is temporarily offline",
      maintenanceMessage:
        "Site is currently down due to maintenance. We will be back shortly.",
      maintenanceNote:
        "Thank you for your patience while we finish a few upgrades."
    },
    emotions: {
      anger: "Anger",
      disgust: "Disgust",
      fear: "Fear",
      joy: "Joy",
      sadness: "Sadness",
      passion: "Passion",
      surprise: "Surprise"
    }
  },
  es: {
    name: "Español",
    short: "ES",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Detector de emociones",
      subtitle:
        "Un espacio sencillo para notar lo que sientes en siete emociones básicas.",
      inputLabel: "Texto",
      inputPlaceholder:
        "Escribe un texto corto. Por ejemplo: Estoy agradecido y emocionado por empezar algo nuevo hoy.",
      wordInfoDefault: "Máximo 250 palabras",
      wordsLabel: "palabras",
      analyzeButton: "Analizar",
      coreMixtureTitle: "Mezcla principal",
      analysisTitle: "Análisis",
      resultsTitle: "Resultados",
      resultsDominantLabel: "Principal",
      resultsEmotionLabel: "Emoción actual",
      resultsSecondaryLabel: "Secundaria",
      resultsMixedLabel: "Estado mixto",
      resultsMixedYes: "Sí",
      resultsMixedNo: "No",
      resultsValenceLabel: "Valencia",
      resultsActivationLabel: "Activación",
      resultsIntensityLabel: "Intensidad",
      resultsConfidenceLabel: "Confianza",
      resultsPatternLabel: "Patrón",
      resultsPrototypeLabel: "Tono más cercano",
      footer: "© 2025 In tuned. Todos los derechos reservados.",
      aboutTitle: "Acerca de In tuned",
      aboutDescriptionLabel: "Descripción:",
      aboutBody:
        "In tuned es una herramienta de reflexión intuitiva que te ayuda a entender lo que sientes en este momento. Escribes un texto de hasta 250 palabras y la aplicación resalta una mezcla de siete emociones básicas ira, asco, miedo, alegría, tristeza, pasión y sorpresa para que puedas ver una imagen simple de tu tono emocional. Su objetivo es apoyar la conciencia de uno mismo y una reflexión saludable. No es terapia ni sustituye la atención profesional de salud mental o médica.",
      aboutDone: "Listo",
      statusEnterText: "Por favor, escribe algún texto.",
      statusAnalyzing: "Analizando...",
      statusLowSignal:
        "Hay muy poco texto para comprender cómo te sientes. Intenta añadir un poco más de detalle.",
      statusNeedAnalysis:
        "Realiza un análisis antes de añadir al diario.",
      crisisTitle: "Espera, tu vida es muy valiosa.",
      crisisBody:
        "Si tú o alguien cercano tiene pensamientos de hacerse daño o de suicidio, siempre hay ayuda disponible. El mundo te necesita aquí.",
      crisisNote:
        "Si sientes que puedes estar en peligro, comunícate de inmediato con una línea de ayuda de confianza o con los servicios de emergencia de tu país.",
      crisisHotlineCta: "Contactar línea de ayuda",
      crisisEmergencyCta: "Contactar servicios de emergencia",
      crisisClose: "Cerrar",
      langMenuLabel: "Idioma",
      langSwitchTooltip: "Cambiar idioma",
      helpButtonLabel: "Acerca de In tuned",
      themeToggleLabel: "Cambiar entre tema claro y oscuro",
      journalNewTitle: "Nueva entrada de diario",
      journalOriginalTextLabel: "Texto original",
      journalAnalysisSnapshotLabel: "Resumen del análisis",
      journalJournalLabel: "Diario",
      journalCancel: "Cancelar",
      journalSave: "Guardar",
      journalDefaultTitle: "Entrada de diario",
      journalPin: "Fijar",
      journalUnpin: "Quitar fijación",
      accountLabel: "Cuenta",
      loginButtonLabel: "Iniciar sesión",
      maintenanceTitle: "In tuned está temporalmente fuera de línea",
      maintenanceMessage:
        "El sitio está en mantenimiento en este momento. Volveremos en breve.",
      maintenanceNote:
        "Gracias por tu paciencia mientras terminamos algunas mejoras."
    },
    emotions: {
      anger: "Ira",
      disgust: "Asco",
      fear: "Miedo",
      joy: "Alegría",
      sadness: "Tristeza",
      passion: "Pasión",
      surprise: "Sorpresa"
    }
  },
  pt: {
    name: "Português",
    short: "PT",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Detector de emoções",
      subtitle:
        "Um espaço simples para perceber o que você está sentindo em sete emoções centrais.",
      inputLabel: "Texto",
      inputPlaceholder:
        "Escreva um pequeno texto. Por exemplo: Estou grato e animado para começar algo novo hoje.",
      wordInfoDefault: "Máximo de 250 palavras",
      wordsLabel: "palavras",
      analyzeButton: "Analisar",
      coreMixtureTitle: "Mistura principal",
      analysisTitle: "Análise",
      resultsTitle: "Resultados",
      resultsDominantLabel: "Principal",
      resultsEmotionLabel: "Emoção atual",
      resultsSecondaryLabel: "Secundária",
      resultsMixedLabel: "Estado misto",
      resultsMixedYes: "Sim",
      resultsMixedNo: "Não",
      resultsValenceLabel: "Valência",
      resultsActivationLabel: "Ativação",
      resultsIntensityLabel: "Intensidade",
      resultsConfidenceLabel: "Confiança",
      resultsPatternLabel: "Padrão",
      resultsPrototypeLabel: "Tom mais próximo",
      footer: "© 2025 In tuned. Todos os direitos reservados.",
      aboutTitle: "Sobre o In tuned",
      aboutDescriptionLabel: "Descrição:",
      aboutBody:
        "In tuned é uma ferramenta intuitiva de reflexão que ajuda você a entender o que está sentindo no momento. Você escreve um pequeno texto de até 250 palavras e o aplicativo destaca uma mistura de sete emoções centrais raiva, nojo, medo, alegria, tristeza, paixão e surpresa para mostrar um retrato simples do seu tom emocional. O objetivo é apoiar a autoconsciência e uma reflexão saudável. Não é terapia e não substitui atendimento profissional em saúde mental ou médico.",
      aboutDone: "Concluir",
      statusEnterText: "Por favor, escreva algum texto.",
      statusAnalyzing: "Analisando...",
      statusLowSignal:
        "Há texto insuficiente para entender como você se sente. Tente acrescentar um pouco mais de detalhes.",
      statusNeedAnalysis:
        "Faça uma análise antes de adicionar ao diário.",
      crisisTitle: "Espere, a sua vida é preciosa.",
      crisisBody:
        "Se você ou alguém próximo está tendo pensamentos de autoagressão ou suicídio, sempre existe ajuda disponível. O mundo precisa de você aqui.",
      crisisNote:
        "Se você sentir que pode estar em perigo, procure imediatamente uma linha de apoio de confiança ou os serviços de emergência da sua região.",
      crisisHotlineCta: "Contato linha de apoio",
      crisisEmergencyCta: "Contato serviços de emergência",
      crisisClose: "Fechar",
      langMenuLabel: "Idioma",
      langSwitchTooltip: "Alterar idioma",
      helpButtonLabel: "Sobre o In tuned",
      themeToggleLabel: "Alternar entre tema claro e escuro",
      journalNewTitle: "Nova entrada de diário",
      journalOriginalTextLabel: "Texto original",
      journalAnalysisSnapshotLabel: "Resumo da análise",
      journalJournalLabel: "Diário",
      journalCancel: "Cancelar",
      journalSave: "Salvar",
      journalDefaultTitle: "Entrada de diário",
      journalPin: "Fixar",
      journalUnpin: "Desafixar",
      accountLabel: "Conta",
      loginButtonLabel: "Entrar",
      maintenanceTitle: "In tuned está temporariamente fora do ar",
      maintenanceMessage:
        "O site está em manutenção no momento. Voltaremos em breve.",
      maintenanceNote:
        "Obrigado pela sua paciência enquanto concluímos algumas melhorias."
    },
    emotions: {
      anger: "Raiva",
      disgust: "Nojo",
      fear: "Medo",
      joy: "Alegria",
      sadness: "Tristeza",
      passion: "Paixão",
      surprise: "Surpresa"
    }
  },
  fr: {
    name: "Français",
    short: "FR",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Détecteur d'émotions",
      subtitle: "Un espace simple pour observer ce que vous ressentez à travers sept émotions fondamentales.",
      inputLabel: "Texte",
      inputPlaceholder: "Écrivez un court passage. Par exemple : Je suis reconnaissant et enthousiaste à l'idée de commencer quelque chose de nouveau aujourd'hui.",
      wordInfoDefault: "250 mots maximum",
      wordsLabel: "mots",
      analyzeButton: "Analyser",
      coreMixtureTitle: "Mélange principal",
      analysisTitle: "Analyse",
      resultsTitle: "Résultats",
      resultsDominantLabel: "Dominante",
      resultsEmotionLabel: "Émotion actuelle",
      resultsSecondaryLabel: "Secondaire",
      resultsMixedLabel: "État mixte",
      resultsMixedYes: "Oui",
      resultsMixedNo: "Non",
      resultsValenceLabel: "Valence",
      resultsActivationLabel: "Activation",
      resultsIntensityLabel: "Intensité",
      resultsConfidenceLabel: "Confiance",
      resultsPatternLabel: "Schéma",
      resultsPrototypeLabel: "Ton le plus proche",
      footer: "© 2025 In tuned. Tous droits réservés.",
      aboutTitle: "À propos d'In tuned",
      aboutDescriptionLabel: "Description :",
      aboutBody: "In tuned est un outil de réflexion intuitif qui vous aide à comprendre ce que vous ressentez sur le moment. Vous écrivez un court passage de 250 mots maximum et l'application met en évidence un mélange de sept émotions fondamentales colère, dégoût, peur, joie, tristesse, passion et surprise afin que vous puissiez voir un instantané émotionnel simple de votre texte. L'objectif est de soutenir la conscience de soi et une réflexion saine uniquement. Ce n'est pas une thérapie et ne remplace pas les soins professionnels de santé mentale.",
      aboutDone: "Terminé",
      statusEnterText: "Veuillez saisir du texte.",
      statusAnalyzing: "Analyse en cours...",
      statusLowSignal: "Trop peu de texte pour comprendre ce que vous ressentez. Essayez d'ajouter un peu plus de détails.",
      statusNeedAnalysis: "Effectuez une analyse avant d'ajouter au journal.",
      crisisTitle: "Attendez ! Vous êtes précieux et important.",
      crisisBody: "Si vous ou vos proches avez des pensées d'automutilation ou de suicide, une aide est toujours disponible. Le monde a besoin de vous.",
      crisisNote: "Si vous sentez que vous pourriez être en danger, veuillez contacter une ligne d'aide de confiance ou les services d'urgence de votre région immédiatement.",
      crisisHotlineCta: "Contacter la ligne d'aide",
      crisisEmergencyCta: "Contacter les services d'urgence",
      crisisClose: "Fermer",
      langMenuLabel: "Langue",
      langSwitchTooltip: "Changer de langue",
      helpButtonLabel: "À propos d'In tuned",
      themeToggleLabel: "Basculer entre thème clair et sombre",
      settingsThemeLabel: "Thème",
      settingsLanguageLabel: "Langue",
      journalNewTitle: "Nouvelle entrée de journal",
      journalOriginalTextLabel: "Texte original",
      journalAnalysisSnapshotLabel: "Résumé de l'analyse",
      journalJournalLabel: "Journal",
      journalCancel: "Annuler",
      journalSave: "Enregistrer",
      journalDefaultTitle: "Entrée de journal",
      journalPin: "Épingler",
      journalUnpin: "Désépingler",
      accountLabel: "Compte",
      loginButtonLabel: "Connexion",
      maintenanceTitle: "In tuned est temporairement hors ligne",
      maintenanceMessage: "Le site est actuellement en maintenance. Nous serons de retour bientôt.",
      maintenanceNote: "Merci de votre patience pendant que nous terminons quelques améliorations."
    },
    emotions: {
      anger: "Colère",
      disgust: "Dégoût",
      fear: "Peur",
      joy: "Joie",
      sadness: "Tristesse",
      passion: "Passion",
      surprise: "Surprise"
    }
  },
  de: {
    name: "Deutsch",
    short: "DE",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Emotionserkennung",
      subtitle: "Ein einfacher Raum, um wahrzunehmen, was Sie über sieben Grundemotionen fühlen.",
      inputLabel: "Text",
      inputPlaceholder: "Schreiben Sie einen kurzen Text. Zum Beispiel: Ich bin dankbar und freue mich darauf, heute etwas Neues zu beginnen.",
      wordInfoDefault: "Maximal 250 Wörter",
      wordsLabel: "Wörter",
      analyzeButton: "Analysieren",
      coreMixtureTitle: "Kernmischung",
      analysisTitle: "Analyse",
      resultsTitle: "Ergebnisse",
      resultsDominantLabel: "Dominant",
      resultsEmotionLabel: "Aktuelle Emotion",
      resultsSecondaryLabel: "Sekundär",
      resultsMixedLabel: "Gemischter Zustand",
      resultsMixedYes: "Ja",
      resultsMixedNo: "Nein",
      resultsValenceLabel: "Valenz",
      resultsActivationLabel: "Aktivierung",
      resultsIntensityLabel: "Intensität",
      resultsConfidenceLabel: "Konfidenz",
      resultsPatternLabel: "Muster",
      resultsPrototypeLabel: "Nächster Ton",
      footer: "© 2025 In tuned. Alle Rechte vorbehalten.",
      aboutTitle: "Über In tuned",
      aboutDescriptionLabel: "Beschreibung:",
      aboutBody: "In tuned ist ein intuitives Reflexionswerkzeug, das Ihnen hilft zu verstehen, was Sie im Moment fühlen. Sie schreiben einen kurzen Text von bis zu 250 Wörtern und die App hebt eine Mischung aus sieben Grundemotionen hervor Wut, Ekel, Angst, Freude, Traurigkeit, Leidenschaft und Überraschung damit Sie einen einfachen emotionalen Schnappschuss Ihres Textes sehen können. Das Ziel ist es, Selbstbewusstsein und gesunde Reflexion zu unterstützen. Es ist keine Therapie und kein Ersatz für professionelle psychische Gesundheitsversorgung.",
      aboutDone: "Fertig",
      statusEnterText: "Bitte geben Sie einen Text ein.",
      statusAnalyzing: "Analysiere...",
      statusLowSignal: "Zu wenig Text, um zu verstehen, wie Sie sich fühlen. Versuchen Sie, etwas mehr Detail hinzuzufügen.",
      statusNeedAnalysis: "Führen Sie eine Analyse durch, bevor Sie zum Tagebuch hinzufügen.",
      crisisTitle: "Warten Sie! Sie sind wertvoll und wichtig.",
      crisisBody: "Wenn Sie oder Ihre Liebsten Gedanken an Selbstverletzung oder Suizid haben, ist immer Hilfe verfügbar. Die Welt braucht Sie.",
      crisisNote: "Wenn Sie das Gefühl haben, in Gefahr zu sein, kontaktieren Sie bitte sofort eine vertrauenswürdige Krisenhotline oder den Notdienst.",
      crisisHotlineCta: "Krisenhotline kontaktieren",
      crisisEmergencyCta: "Notdienst kontaktieren",
      crisisClose: "Schließen",
      langMenuLabel: "Sprache",
      langSwitchTooltip: "Sprache ändern",
      helpButtonLabel: "Über In tuned",
      themeToggleLabel: "Zwischen hellem und dunklem Thema wechseln",
      settingsThemeLabel: "Thema",
      settingsLanguageLabel: "Sprache",
      journalNewTitle: "Neuer Tagebucheintrag",
      journalOriginalTextLabel: "Originaltext",
      journalAnalysisSnapshotLabel: "Analysezusammenfassung",
      journalJournalLabel: "Tagebuch",
      journalCancel: "Abbrechen",
      journalSave: "Speichern",
      journalDefaultTitle: "Tagebucheintrag",
      journalPin: "Anheften",
      journalUnpin: "Lösen",
      accountLabel: "Konto",
      loginButtonLabel: "Anmelden",
      maintenanceTitle: "In tuned ist vorübergehend offline",
      maintenanceMessage: "Die Seite befindet sich derzeit in Wartung. Wir sind bald zurück.",
      maintenanceNote: "Vielen Dank für Ihre Geduld, während wir einige Verbesserungen abschließen."
    },
    emotions: {
      anger: "Wut",
      disgust: "Ekel",
      fear: "Angst",
      joy: "Freude",
      sadness: "Traurigkeit",
      passion: "Leidenschaft",
      surprise: "Überraschung"
    }
  },
  it: {
    name: "Italiano",
    short: "IT",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Rilevatore di emozioni",
      subtitle: "Uno spazio semplice per notare ciò che senti attraverso sette emozioni fondamentali.",
      inputLabel: "Testo",
      inputPlaceholder: "Scrivi un breve passaggio. Ad esempio: Sono grato ed entusiasta di iniziare qualcosa di nuovo oggi.",
      wordInfoDefault: "Massimo 250 parole",
      wordsLabel: "parole",
      analyzeButton: "Analizza",
      coreMixtureTitle: "Miscela principale",
      analysisTitle: "Analisi",
      resultsTitle: "Risultati",
      resultsDominantLabel: "Dominante",
      resultsEmotionLabel: "Emozione attuale",
      resultsSecondaryLabel: "Secondaria",
      resultsMixedLabel: "Stato misto",
      resultsMixedYes: "Sì",
      resultsMixedNo: "No",
      resultsValenceLabel: "Valenza",
      resultsActivationLabel: "Attivazione",
      resultsIntensityLabel: "Intensità",
      resultsConfidenceLabel: "Fiducia",
      resultsPatternLabel: "Schema",
      resultsPrototypeLabel: "Tono più vicino",
      footer: "© 2025 In tuned. Tutti i diritti riservati.",
      aboutTitle: "Informazioni su In tuned",
      aboutDescriptionLabel: "Descrizione:",
      aboutBody: "In tuned è uno strumento di riflessione intuitivo che ti aiuta a capire cosa stai provando nel momento. Scrivi un breve passaggio di massimo 250 parole e l'app evidenzia un mix di sette emozioni fondamentali rabbia, disgusto, paura, gioia, tristezza, passione e sorpresa in modo da poter vedere un semplice istantanea emotiva del tuo testo. L'obiettivo è supportare la consapevolezza di sé e una riflessione sana. Non è terapia e non sostituisce l'assistenza professionale per la salute mentale.",
      aboutDone: "Fatto",
      statusEnterText: "Inserisci del testo.",
      statusAnalyzing: "Analisi in corso...",
      statusLowSignal: "Troppo poco testo per capire come ti senti. Prova ad aggiungere qualche dettaglio in più.",
      statusNeedAnalysis: "Esegui un'analisi prima di aggiungere al diario.",
      crisisTitle: "Aspetta! Sei prezioso e importante.",
      crisisBody: "Se tu o i tuoi cari avete pensieri di autolesionismo o suicidio, l'aiuto è sempre disponibile. Il mondo ha bisogno di te.",
      crisisNote: "Se senti di essere in pericolo, contatta immediatamente una linea di crisi affidabile o i servizi di emergenza della tua zona.",
      crisisHotlineCta: "Contatta la linea di aiuto",
      crisisEmergencyCta: "Contatta i servizi di emergenza",
      crisisClose: "Chiudi",
      langMenuLabel: "Lingua",
      langSwitchTooltip: "Cambia lingua",
      helpButtonLabel: "Informazioni su In tuned",
      themeToggleLabel: "Passa tra tema chiaro e scuro",
      settingsThemeLabel: "Tema",
      settingsLanguageLabel: "Lingua",
      journalNewTitle: "Nuova voce del diario",
      journalOriginalTextLabel: "Testo originale",
      journalAnalysisSnapshotLabel: "Riepilogo dell'analisi",
      journalJournalLabel: "Diario",
      journalCancel: "Annulla",
      journalSave: "Salva",
      journalDefaultTitle: "Voce del diario",
      journalPin: "Fissa",
      journalUnpin: "Rimuovi fissaggio",
      accountLabel: "Account",
      loginButtonLabel: "Accedi",
      maintenanceTitle: "In tuned è temporaneamente offline",
      maintenanceMessage: "Il sito è attualmente in manutenzione. Torneremo presto.",
      maintenanceNote: "Grazie per la pazienza mentre completiamo alcuni aggiornamenti."
    },
    emotions: {
      anger: "Rabbia",
      disgust: "Disgusto",
      fear: "Paura",
      joy: "Gioia",
      sadness: "Tristezza",
      passion: "Passione",
      surprise: "Sorpresa"
    }
  },
  ja: {
    name: "日本語",
    short: "JA",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "感情検出器",
      subtitle: "7つの基本感情を通じて、今の気持ちに気づくためのシンプルな空間です。",
      inputLabel: "テキスト",
      inputPlaceholder: "短い文章を入力してください。例：今日、新しいことを始められることに感謝し、ワクワクしています。",
      wordInfoDefault: "最大250語",
      wordsLabel: "語",
      analyzeButton: "分析する",
      coreMixtureTitle: "感情の配合",
      analysisTitle: "分析",
      resultsTitle: "結果",
      resultsDominantLabel: "主要な感情",
      resultsEmotionLabel: "現在の感情",
      resultsSecondaryLabel: "二次的",
      resultsMixedLabel: "混合状態",
      resultsMixedYes: "はい",
      resultsMixedNo: "いいえ",
      resultsValenceLabel: "感情価",
      resultsActivationLabel: "活性度",
      resultsIntensityLabel: "強度",
      resultsConfidenceLabel: "信頼度",
      resultsPatternLabel: "パターン",
      resultsPrototypeLabel: "最も近いトーン",
      footer: "© 2025 In tuned. All rights reserved.",
      aboutTitle: "In tunedについて",
      aboutDescriptionLabel: "説明：",
      aboutBody: "In tunedは、今の瞬間に何を感じているかを理解するのに役立つ直感的な振り返りツールです。250語以内の短い文章を書くと、アプリが怒り、嫌悪、恐怖、喜び、悲しみ、情熱、驚きの7つの基本感情のブレンドを強調表示し、テキストの感情的なスナップショットを表示します。目的は自己認識と健全な振り返りを支援することのみです。セラピーではなく、専門的なメンタルヘルスケアの代替にはなりません。",
      aboutDone: "完了",
      statusEnterText: "テキストを入力してください。",
      statusAnalyzing: "分析中...",
      statusLowSignal: "テキストが少なすぎて気持ちを理解できません。もう少し詳しく書いてみてください。",
      statusNeedAnalysis: "日記に追加する前に分析を実行してください。",
      crisisTitle: "お待ちください！あなたはかけがえのない大切な存在です。",
      crisisBody: "あなたやあなたの大切な人が自傷や自殺の考えをお持ちの場合、いつでも助けを求めることができます。この世界にはあなたが必要です。",
      crisisNote: "危険を感じている場合は、すぐに信頼できる相談窓口または緊急サービスに連絡してください。",
      crisisHotlineCta: "相談窓口に連絡",
      crisisEmergencyCta: "緊急サービスに連絡",
      crisisClose: "閉じる",
      langMenuLabel: "言語",
      langSwitchTooltip: "言語を変更",
      helpButtonLabel: "In tunedについて",
      themeToggleLabel: "ライト・ダークテーマの切り替え",
      settingsThemeLabel: "テーマ",
      settingsLanguageLabel: "言語",
      journalNewTitle: "新しい日記エントリ",
      journalOriginalTextLabel: "元のテキスト",
      journalAnalysisSnapshotLabel: "分析のスナップショット",
      journalJournalLabel: "日記",
      journalCancel: "キャンセル",
      journalSave: "保存",
      journalDefaultTitle: "日記エントリ",
      journalPin: "ピン留め",
      journalUnpin: "ピン解除",
      accountLabel: "アカウント",
      loginButtonLabel: "ログイン",
      maintenanceTitle: "In tunedは一時的にオフラインです",
      maintenanceMessage: "現在メンテナンス中です。まもなく復旧いたします。",
      maintenanceNote: "アップグレード完了までしばらくお待ちください。"
    },
    emotions: {
      anger: "怒り",
      disgust: "嫌悪",
      fear: "恐怖",
      joy: "喜び",
      sadness: "悲しみ",
      passion: "情熱",
      surprise: "驚き"
    }
  },
  ko: {
    name: "한국어",
    short: "KO",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "감정 감지기",
      subtitle: "일곱 가지 핵심 감정을 통해 지금 느끼는 것을 알아차리는 간단한 공간입니다.",
      inputLabel: "텍스트",
      inputPlaceholder: "짧은 글을 작성하세요. 예: 오늘 새로운 것을 시작하게 되어 감사하고 설렙니다.",
      wordInfoDefault: "최대 250단어",
      wordsLabel: "단어",
      analyzeButton: "분석",
      coreMixtureTitle: "핵심 혼합",
      analysisTitle: "분석",
      resultsTitle: "결과",
      resultsDominantLabel: "주요 감정",
      resultsEmotionLabel: "현재 감정",
      resultsSecondaryLabel: "부차적",
      resultsMixedLabel: "혼합 상태",
      resultsMixedYes: "예",
      resultsMixedNo: "아니오",
      resultsValenceLabel: "감정가",
      resultsActivationLabel: "활성화",
      resultsIntensityLabel: "강도",
      resultsConfidenceLabel: "신뢰도",
      resultsPatternLabel: "패턴",
      resultsPrototypeLabel: "가장 가까운 톤",
      footer: "© 2025 In tuned. All rights reserved.",
      aboutTitle: "In tuned 소개",
      aboutDescriptionLabel: "설명:",
      aboutBody: "In tuned는 지금 이 순간 무엇을 느끼고 있는지 이해하는 데 도움이 되는 직관적인 성찰 도구입니다. 최대 250단어의 짧은 글을 작성하면 앱이 분노, 혐오, 공포, 기쁨, 슬픔, 열정, 놀라움의 일곱 가지 핵심 감정의 혼합을 강조하여 텍스트의 감정적 스냅샷을 보여줍니다. 목표는 자기 인식과 건강한 성찰을 지원하는 것뿐입니다. 치료가 아니며 전문적인 정신 건강 관리를 대체하지 않습니다.",
      aboutDone: "완료",
      statusEnterText: "텍스트를 입력하세요.",
      statusAnalyzing: "분석 중...",
      statusLowSignal: "텍스트가 너무 적어 감정을 이해할 수 없습니다. 조금 더 자세히 작성해 보세요.",
      statusNeedAnalysis: "일기에 추가하기 전에 분석을 실행하세요.",
      crisisTitle: "잠깐! 당신은 소중하고 중요한 사람입니다.",
      crisisBody: "당신이나 소중한 사람이 자해나 자살에 대한 생각을 가지고 있다면, 언제든지 도움을 받을 수 있습니다. 이 세상에는 당신이 필요합니다.",
      crisisNote: "위험하다고 느끼신다면, 즉시 신뢰할 수 있는 위기 상담 전화나 응급 서비스에 연락하세요.",
      crisisHotlineCta: "위기 상담 전화 연락",
      crisisEmergencyCta: "응급 서비스 연락",
      crisisClose: "닫기",
      langMenuLabel: "언어",
      langSwitchTooltip: "언어 변경",
      helpButtonLabel: "In tuned 소개",
      themeToggleLabel: "밝은/어두운 테마 전환",
      settingsThemeLabel: "테마",
      settingsLanguageLabel: "언어",
      journalNewTitle: "새 일기 항목",
      journalOriginalTextLabel: "원본 텍스트",
      journalAnalysisSnapshotLabel: "분석 스냅샷",
      journalJournalLabel: "일기",
      journalCancel: "취소",
      journalSave: "저장",
      journalDefaultTitle: "일기 항목",
      journalPin: "고정",
      journalUnpin: "고정 해제",
      accountLabel: "계정",
      loginButtonLabel: "로그인",
      maintenanceTitle: "In tuned가 일시적으로 오프라인입니다",
      maintenanceMessage: "현재 유지보수 중입니다. 곧 돌아오겠습니다.",
      maintenanceNote: "업그레이드를 완료하는 동안 기다려 주셔서 감사합니다."
    },
    emotions: {
      anger: "분노",
      disgust: "혐오",
      fear: "공포",
      joy: "기쁨",
      sadness: "슬픔",
      passion: "열정",
      surprise: "놀라움"
    }
  },
  zh: {
    name: "中文",
    short: "ZH",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "情绪检测器",
      subtitle: "一个简单的空间，帮助您通过七种核心情绪来感知当下的感受。",
      inputLabel: "文本",
      inputPlaceholder: "输入一段短文。例如：我很感激，也很期待今天开始新的事物。",
      wordInfoDefault: "最多250个词",
      wordsLabel: "词",
      analyzeButton: "分析",
      coreMixtureTitle: "核心混合",
      analysisTitle: "分析",
      resultsTitle: "结果",
      resultsDominantLabel: "主要情绪",
      resultsEmotionLabel: "当前情绪",
      resultsSecondaryLabel: "次要",
      resultsMixedLabel: "混合状态",
      resultsMixedYes: "是",
      resultsMixedNo: "否",
      resultsValenceLabel: "效价",
      resultsActivationLabel: "激活度",
      resultsIntensityLabel: "强度",
      resultsConfidenceLabel: "置信度",
      resultsPatternLabel: "模式",
      resultsPrototypeLabel: "最接近的色调",
      footer: "© 2025 In tuned. All rights reserved.",
      aboutTitle: "关于 In tuned",
      aboutDescriptionLabel: "描述：",
      aboutBody: "In tuned 是一款直觉反思工具，帮助您了解当下的感受。您写一段不超过250词的短文，应用会突出显示七种核心情绪的混合——愤怒、厌恶、恐惧、喜悦、悲伤、热情和惊讶——让您看到文本的简单情绪快照。目标仅在于支持自我意识和健康的反思。这不是治疗，也不能替代专业的心理健康护理。",
      aboutDone: "完成",
      statusEnterText: "请输入一些文字。",
      statusAnalyzing: "分析中...",
      statusLowSignal: "文本太少，无法理解您的感受。请尝试添加更多细节。",
      statusNeedAnalysis: "在添加到日记之前，请先进行分析。",
      crisisTitle: "等等！您是无价的、重要的。",
      crisisBody: "如果您或您的亲人有自我伤害或自杀的想法，帮助随时都有。这个世界需要您。",
      crisisNote: "如果您感到自己可能处于危险之中，请立即联系值得信赖的危机热线或当地紧急服务。",
      crisisHotlineCta: "联系危机热线",
      crisisEmergencyCta: "联系紧急服务",
      crisisClose: "关闭",
      langMenuLabel: "语言",
      langSwitchTooltip: "切换语言",
      helpButtonLabel: "关于 In tuned",
      themeToggleLabel: "切换浅色和深色主题",
      settingsThemeLabel: "主题",
      settingsLanguageLabel: "语言",
      journalNewTitle: "新日记条目",
      journalOriginalTextLabel: "原始文本",
      journalAnalysisSnapshotLabel: "分析摘要",
      journalJournalLabel: "日记",
      journalCancel: "取消",
      journalSave: "保存",
      journalDefaultTitle: "日记条目",
      journalPin: "置顶",
      journalUnpin: "取消置顶",
      accountLabel: "账户",
      loginButtonLabel: "登录",
      maintenanceTitle: "In tuned 暂时离线",
      maintenanceMessage: "网站正在维护中。我们很快就会回来。",
      maintenanceNote: "感谢您在我们完成升级期间的耐心等待。"
    },
    emotions: {
      anger: "愤怒",
      disgust: "厌恶",
      fear: "恐惧",
      joy: "喜悦",
      sadness: "悲伤",
      passion: "热情",
      surprise: "惊讶"
    }
  },
  ar: {
    name: "العربية",
    short: "AR",
    direction: "rtl",
    strings: {
      appTitle: "In tuned",
      headline: "كاشف المشاعر",
      subtitle: "مساحة بسيطة لملاحظة ما تشعر به عبر سبع مشاعر أساسية.",
      inputLabel: "النص",
      inputPlaceholder: "اكتب نصاً قصيراً. مثال: أنا ممتن ومتحمس لبدء شيء جديد اليوم.",
      wordInfoDefault: "الحد الأقصى 250 كلمة",
      wordsLabel: "كلمات",
      analyzeButton: "تحليل",
      coreMixtureTitle: "المزيج الأساسي",
      analysisTitle: "التحليل",
      resultsTitle: "النتائج",
      resultsDominantLabel: "المشاعر السائدة",
      resultsEmotionLabel: "المشاعر الحالية",
      resultsSecondaryLabel: "ثانوي",
      resultsMixedLabel: "حالة مختلطة",
      resultsMixedYes: "نعم",
      resultsMixedNo: "لا",
      resultsValenceLabel: "التكافؤ",
      resultsActivationLabel: "التنشيط",
      resultsIntensityLabel: "الشدة",
      resultsConfidenceLabel: "الثقة",
      resultsPatternLabel: "النمط",
      resultsPrototypeLabel: "أقرب نبرة",
      footer: "© 2025 In tuned. جميع الحقوق محفوظة.",
      aboutTitle: "حول In tuned",
      aboutDescriptionLabel: "الوصف:",
      aboutBody: "In tuned هي أداة تأمل بديهية تساعدك على فهم ما تشعر به في اللحظة. تكتب نصاً قصيراً لا يتجاوز 250 كلمة ويبرز التطبيق مزيجاً من سبع مشاعر أساسية الغضب والاشمئزاز والخوف والفرح والحزن والشغف والمفاجأة لتتمكن من رؤية لقطة عاطفية بسيطة لنصك. الهدف هو دعم الوعي الذاتي والتأمل الصحي فقط. ليست علاجاً ولا بديلاً عن الرعاية الصحية النفسية المهنية.",
      aboutDone: "تم",
      statusEnterText: "يرجى إدخال نص.",
      statusAnalyzing: "جاري التحليل...",
      statusLowSignal: "النص قصير جداً لفهم مشاعرك. حاول إضافة المزيد من التفاصيل.",
      statusNeedAnalysis: "قم بإجراء تحليل قبل الإضافة إلى اليوميات.",
      crisisTitle: "انتظر! أنت ثمين ومهم.",
      crisisBody: "إذا كنت أنت أو أحباؤك تراودكم أفكار إيذاء النفس أو الانتحار، فالمساعدة متاحة دائماً. العالم يحتاجك.",
      crisisNote: "إذا شعرت أنك قد تكون في خطر، يرجى الاتصال بخط أزمات موثوق أو خدمات الطوارئ المحلية فوراً.",
      crisisHotlineCta: "اتصل بخط المساعدة",
      crisisEmergencyCta: "اتصل بخدمات الطوارئ",
      crisisClose: "إغلاق",
      langMenuLabel: "اللغة",
      langSwitchTooltip: "تغيير اللغة",
      helpButtonLabel: "حول In tuned",
      themeToggleLabel: "التبديل بين المظهر الفاتح والداكن",
      settingsThemeLabel: "المظهر",
      settingsLanguageLabel: "اللغة",
      journalNewTitle: "إدخال يوميات جديد",
      journalOriginalTextLabel: "النص الأصلي",
      journalAnalysisSnapshotLabel: "ملخص التحليل",
      journalJournalLabel: "اليوميات",
      journalCancel: "إلغاء",
      journalSave: "حفظ",
      journalDefaultTitle: "إدخال اليوميات",
      journalPin: "تثبيت",
      journalUnpin: "إلغاء التثبيت",
      accountLabel: "الحساب",
      loginButtonLabel: "تسجيل الدخول",
      maintenanceTitle: "In tuned غير متاح مؤقتاً",
      maintenanceMessage: "الموقع قيد الصيانة حالياً. سنعود قريباً.",
      maintenanceNote: "شكراً لصبركم بينما ننهي بعض التحسينات."
    },
    emotions: {
      anger: "غضب",
      disgust: "اشمئزاز",
      fear: "خوف",
      joy: "فرح",
      sadness: "حزن",
      passion: "شغف",
      surprise: "مفاجأة"
    }
  },
  hi: {
    name: "हिन्दी",
    short: "HI",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "भावना पहचानक",
      subtitle: "सात मूल भावनाओं के माध्यम से अपनी भावनाओं को जानने के लिए एक सरल स्थान।",
      inputLabel: "पाठ",
      inputPlaceholder: "एक छोटा अनुच्छेद लिखें। उदाहरण: मैं आभारी हूँ और आज कुछ नया शुरू करने के लिए उत्साहित हूँ।",
      wordInfoDefault: "अधिकतम 250 शब्द",
      wordsLabel: "शब्द",
      analyzeButton: "विश्लेषण करें",
      coreMixtureTitle: "मूल मिश्रण",
      analysisTitle: "विश्लेषण",
      resultsTitle: "परिणाम",
      resultsDominantLabel: "प्रमुख",
      resultsEmotionLabel: "वर्तमान भावना",
      resultsSecondaryLabel: "द्वितीयक",
      resultsMixedLabel: "मिश्रित स्थिति",
      resultsMixedYes: "हाँ",
      resultsMixedNo: "नहीं",
      resultsValenceLabel: "वैलेंस",
      resultsActivationLabel: "सक्रियता",
      resultsIntensityLabel: "तीव्रता",
      resultsConfidenceLabel: "विश्वास",
      resultsPatternLabel: "पैटर्न",
      resultsPrototypeLabel: "निकटतम स्वर",
      footer: "© 2025 In tuned. सर्वाधिकार सुरक्षित।",
      aboutTitle: "In tuned के बारे में",
      aboutDescriptionLabel: "विवरण:",
      aboutBody: "In tuned एक सहज प्रतिबिंब उपकरण है जो आपको इस पल में क्या महसूस कर रहे हैं यह समझने में मदद करता है। आप 250 शब्दों तक का एक छोटा अनुच्छेद लिखते हैं और ऐप सात मूल भावनाओं क्रोध, घृणा, भय, आनंद, उदासी, जुनून और आश्चर्य का मिश्रण उजागर करता है ताकि आप अपने पाठ का एक सरल भावनात्मक स्नैपशॉट देख सकें। लक्ष्य केवल आत्म-जागरूकता और स्वस्थ प्रतिबिंब का समर्थन करना है। यह चिकित्सा नहीं है और पेशेवर मानसिक स्वास्थ्य देखभाल का विकल्प नहीं है।",
      aboutDone: "पूर्ण",
      statusEnterText: "कृपया कुछ पाठ दर्ज करें।",
      statusAnalyzing: "विश्लेषण हो रहा है...",
      statusLowSignal: "आप कैसा महसूस कर रहे हैं यह समझने के लिए बहुत कम पाठ है। थोड़ा और विवरण जोड़ने का प्रयास करें।",
      statusNeedAnalysis: "डायरी में जोड़ने से पहले एक विश्लेषण चलाएँ।",
      crisisTitle: "रुकिए! आप अनमोल और महत्वपूर्ण हैं।",
      crisisBody: "यदि आप या आपके प्रियजन आत्महानि या आत्महत्या के विचार रखते हैं, तो मदद हमेशा उपलब्ध है। इस दुनिया को आपकी ज़रूरत है।",
      crisisNote: "यदि आपको लगता है कि आप खतरे में हो सकते हैं, तो कृपया तुरंत किसी विश्वसनीय संकट हेल्पलाइन या अपनी स्थानीय आपातकालीन सेवाओं से संपर्क करें।",
      crisisHotlineCta: "हेल्पलाइन से संपर्क करें",
      crisisEmergencyCta: "आपातकालीन सेवाओं से संपर्क करें",
      crisisClose: "बंद करें",
      langMenuLabel: "भाषा",
      langSwitchTooltip: "भाषा बदलें",
      helpButtonLabel: "In tuned के बारे में",
      themeToggleLabel: "हल्के और गहरे थीम के बीच टॉगल करें",
      settingsThemeLabel: "थीम",
      settingsLanguageLabel: "भाषा",
      journalNewTitle: "नई डायरी प्रविष्टि",
      journalOriginalTextLabel: "मूल पाठ",
      journalAnalysisSnapshotLabel: "विश्लेषण सारांश",
      journalJournalLabel: "डायरी",
      journalCancel: "रद्द करें",
      journalSave: "सहेजें",
      journalDefaultTitle: "डायरी प्रविष्टि",
      journalPin: "पिन करें",
      journalUnpin: "अनपिन करें",
      accountLabel: "खाता",
      loginButtonLabel: "लॉग इन",
      maintenanceTitle: "In tuned अस्थायी रूप से ऑफ़लाइन है",
      maintenanceMessage: "साइट वर्तमान में रखरखाव में है। हम जल्द वापस आएँगे।",
      maintenanceNote: "कुछ सुधार पूरे करने के दौरान आपके धैर्य के लिए धन्यवाद।"
    },
    emotions: {
      anger: "क्रोध",
      disgust: "घृणा",
      fear: "भय",
      joy: "आनंद",
      sadness: "उदासी",
      passion: "जुनून",
      surprise: "आश्चर्य"
    }
  },
  ru: {
    name: "Русский",
    short: "RU",
    direction: "ltr",
    strings: {
      appTitle: "In tuned",
      headline: "Детектор эмоций",
      subtitle: "Простое пространство для осознания своих чувств через семь основных эмоций.",
      inputLabel: "Текст",
      inputPlaceholder: "Напишите короткий текст. Например: Я благодарен и взволнован начать что-то новое сегодня.",
      wordInfoDefault: "Максимум 250 слов",
      wordsLabel: "слов",
      analyzeButton: "Анализировать",
      coreMixtureTitle: "Основная смесь",
      analysisTitle: "Анализ",
      resultsTitle: "Результаты",
      resultsDominantLabel: "Доминирующая",
      resultsEmotionLabel: "Текущая эмоция",
      resultsSecondaryLabel: "Вторичная",
      resultsMixedLabel: "Смешанное состояние",
      resultsMixedYes: "Да",
      resultsMixedNo: "Нет",
      resultsValenceLabel: "Валентность",
      resultsActivationLabel: "Активация",
      resultsIntensityLabel: "Интенсивность",
      resultsConfidenceLabel: "Уверенность",
      resultsPatternLabel: "Паттерн",
      resultsPrototypeLabel: "Ближайший тон",
      footer: "© 2025 In tuned. Все права защищены.",
      aboutTitle: "О приложении In tuned",
      aboutDescriptionLabel: "Описание:",
      aboutBody: "In tuned — это интуитивный инструмент рефлексии, который помогает понять, что вы чувствуете в данный момент. Вы пишете короткий текст до 250 слов, а приложение выделяет смесь семи основных эмоций — гнев, отвращение, страх, радость, печаль, страсть и удивление — чтобы вы могли увидеть простой эмоциональный снимок вашего текста. Цель — поддержать самосознание и здоровую рефлексию. Это не терапия и не замена профессиональной помощи в области психического здоровья.",
      aboutDone: "Готово",
      statusEnterText: "Пожалуйста, введите текст.",
      statusAnalyzing: "Анализ...",
      statusLowSignal: "Слишком мало текста для понимания ваших чувств. Попробуйте добавить больше деталей.",
      statusNeedAnalysis: "Выполните анализ перед добавлением в дневник.",
      crisisTitle: "Подождите! Вы бесценны и важны.",
      crisisBody: "Если у вас или ваших близких есть мысли о самоповреждении или суициде, помощь всегда доступна. Мир нуждается в вас.",
      crisisNote: "Если вы чувствуете, что можете быть в опасности, немедленно свяжитесь с доверенной горячей линией помощи или экстренными службами.",
      crisisHotlineCta: "Связаться с горячей линией",
      crisisEmergencyCta: "Связаться с экстренными службами",
      crisisClose: "Закрыть",
      langMenuLabel: "Язык",
      langSwitchTooltip: "Изменить язык",
      helpButtonLabel: "О приложении In tuned",
      themeToggleLabel: "Переключить между светлой и тёмной темой",
      settingsThemeLabel: "Тема",
      settingsLanguageLabel: "Язык",
      journalNewTitle: "Новая запись в дневнике",
      journalOriginalTextLabel: "Исходный текст",
      journalAnalysisSnapshotLabel: "Снимок анализа",
      journalJournalLabel: "Дневник",
      journalCancel: "Отмена",
      journalSave: "Сохранить",
      journalDefaultTitle: "Запись в дневнике",
      journalPin: "Закрепить",
      journalUnpin: "Открепить",
      accountLabel: "Аккаунт",
      loginButtonLabel: "Войти",
      maintenanceTitle: "In tuned временно недоступен",
      maintenanceMessage: "Сайт находится на техническом обслуживании. Мы скоро вернёмся.",
      maintenanceNote: "Благодарим за терпение, пока мы завершаем обновления."
    },
    emotions: {
      anger: "Гнев",
      disgust: "Отвращение",
      fear: "Страх",
      joy: "Радость",
      sadness: "Печаль",
      passion: "Страсть",
      surprise: "Удивление"
    }
  }
};

const SUPPORTED_LOCALES = Object.keys(LOCALES);

function normalizeLocaleCode(raw) {
  if (!raw) return "en";
  const lower = String(raw).toLowerCase();
  if (LOCALES[lower]) return lower;
  const base = lower.split("-")[0];
  if (LOCALES[base]) return base;
  return "en";
}

function getInitialLocale() {
  try {
    const stored = localStorage.getItem("in-tuned-locale");
    if (stored && LOCALES[stored]) return stored;
  } catch (e) {}
  const nav =
    (navigator.languages && navigator.languages[0]) ||
    navigator.language ||
    "en";
  return normalizeLocaleCode(nav);
}

let currentLocale = getInitialLocale();

/* ---------- Global state ---------- */

let currentUser = null;
let lastAcceptedText = "";
let lastAnalysisSnapshot = null;
let journals = [];
let currentJournal = null;
let isEditingJournal = false;
let isCreatingJournal = false;

const root = document.documentElement;

/* ---------- Simple API helpers ---------- */

async function apiFetchJSON(path, options = {}) {
  const opts = {
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(options.method && options.method !== "GET"
        ? { "Content-Type": "application/json" }
        : {}),
      ...(options.headers || {})
    },
    ...options
  };

  try {
    const res = await fetch(path, opts);
    let json;

    try {
      json = await res.json();
    } catch (e) {
      if (!res.ok) {
        throw new Error(`Request failed with status ${res.status}`);
      }
      json = null;
    }

    if (!res.ok) {
      let message = `Request failed with status ${res.status}`;

      if (json) {
        if (json.error) {
          if (typeof json.error === 'object' && json.error.message) {
            message = json.error.message;
          } else if (typeof json.error === 'string') {
            message = json.error;
          }
        } else if (json.message) {
          message = json.message;
        }
      }

      throw new Error(message);
    }

    return json || {};

  } catch (error) {
    if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
      throw new Error('Network error. Please check your connection and try again.');
    }
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.');
    }
    throw error;
  }
}

/* ---------- DOM references ---------- */

const fields = {
  anger: $("v-anger"),
  disgust: $("v-disgust"),
  fear: $("v-fear"),
  joy: $("v-joy"),
  sadness: $("v-sadness"),
  passion: $("v-passion"),
  surprise: $("v-surprise"),
  dominant_emotion: $("v-dominant"),
  emotion: $("v-emotion"),
  secondary_emotion: $("v-secondary"),
  mixed_state: $("v-mixed"),
  valence: $("v-valence"),
  activation: $("v-activation"),
  intensity: $("v-intensity"),
  confidence_metric: $("v-confidence"),
  pattern: $("v-pattern"),
  prototype: $("v-prototype")
};

const emojiTray = $("emojiTray");
const textArea = $("text");
const wordInfo = $("wordInfo");

/* Header and layout */
const appHeader = $("appHeader");
const appMain = $("appMain");
const appFooter = $("appFooter");
const noticeBanner = $("noticeBanner");
const maintenanceShell = $("maintenanceShell");
const maintenanceMessageEl = $("maintenanceMessage");

/* Settings and language (guest) */
const settingsControl = $("settingsControl");
const settingsBtn = $("settingsBtn");
const settingsMenu = $("settingsMenu");
const langToggle = $("langToggle");
const langMenu = $("langMenu");
const langCurrentLabel = $("langCurrentLabel");

/* Help modal */
const helpBtn = $("helpBtn");
const overlay = $("overlay");
const closeModal = $("closeModal");

/* Crisis overlay */
const crisisOverlay = $("crisisOverlay");
const closeCrisis = $("closeCrisis");
const crisisHotlineBtn = $("crisisHotline");
const crisisEmergencyBtn = $("crisisEmergency");
const crisisHotlineNumberSpan = $("crisisHotlineNumber");
const crisisEmergencyNumberSpan = $("crisisEmergencyNumber");

/* Auth header controls */
const loginBtn = $("loginBtn");
const accountControl = $("accountControl");
const accountBtn = $("accountBtn");
const accountMenu = $("accountMenu");
const accountNameLabel = $("accountNameLabel");

/* Auth overlays and forms */
const authOverlayLogin = $("authOverlayLogin");
const authOverlayRegister = $("authOverlayRegister");
const authOverlayForgot = $("authOverlayForgot");

// Login form
const loginForm = $("loginForm");
const loginIdentifierInput = $("loginIdentifier");
const loginPasswordInput = $("loginPassword");
const loginError = $("loginError");
const openRegisterFromLoginBtn = $("openRegisterFromLogin");
const openForgotFromLoginBtn = $("openForgotFromLogin");
const cancelLoginBtn = $("cancelLogin");
const submitLoginBtn = $("submitLogin");

// Register form
const registerForm = $("registerForm");
const registerFirstName = $("registerFirstName");
const registerLastName = $("registerLastName");
const registerUsername = $("registerUsername");
const registerEmail = $("registerEmail");
const registerPassword = $("registerPassword");
const registerConfirmPassword = $("registerConfirmPassword");
const registerError = $("registerError");
const cancelRegisterBtn = $("cancelRegister");
const submitRegisterBtn = $("submitRegister");

// Forgot form (two step flow)
const forgotForm = $("forgotForm");
const forgotEmail = $("forgotEmail");
const forgotFirstName = $("forgotFirstName");
const forgotLastName = $("forgotLastName");
const forgotNewPassword = $("forgotNewPassword");
const forgotConfirmPassword = $("forgotConfirmPassword");
const forgotError = $("forgotError");
const cancelForgotBtn = $("cancelForgot");
const submitForgotBtn = $("submitForgot");
const forgotStepIdentity = $("forgotStepIdentity");
const forgotStepReset = $("forgotStepReset");
const forgotContinueBtn = $("forgotContinue");
const cancelForgotResetBtn = $("cancelForgotReset");

/* Account settings overlay */
const accountSettingsOverlay = $("accountSettingsOverlay");
const accountSettingsForm = $("accountSettingsForm");
const accountThemeToggle = $("accountThemeToggle");
const accountLangToggle = $("accountLangToggle");
const accountLangMenu = $("accountLangMenu");
const accountLangCurrentLabel = $("accountLangCurrentLabel");
const accountSettingsError = $("accountSettingsError");
const cancelAccountSettingsBtn = $("cancelAccountSettings");
const saveAccountSettingsBtn = $("saveAccountSettings");

/* Delete account overlay */
const openDeleteAccountBtn = $("openDeleteAccount");
const deleteAccountOverlay = $("deleteAccountOverlay");
const deleteAccountPassword = $("deleteAccountPassword");
const deleteConfirmSure = $("deleteConfirmSure");
const deleteConfirmUnderstand = $("deleteConfirmUnderstand");
const deleteAccountError = $("deleteAccountError");
const cancelDeleteAccountBtn = $("cancelDeleteAccount");
const confirmDeleteAccountBtn = $("confirmDeleteAccount");

/* Journal overlay and controls */
const addJournalButton = $("addJournalButton");
const addJournalHint = $("addJournalHint");
const journalOverlay = $("journalOverlay");
const closeJournalBtn = $("closeJournal");
const pinnedSectionHeader = $("pinnedSectionHeader");
const pinnedJournalList = $("pinnedJournalList");
const journalList = $("journalList");
const journalEmptyState = $("journalEmptyState");
const journalDetail = $("journalDetail");
const journalDetailTitle = $("journalDetailTitle");
const journalDetailMeta = $("journalDetailMeta");
const journalDetailSourceText = $("journalDetailSourceText");
const journalDetailAnalysis = $("journalDetailAnalysis");
const journalDetailText = $("journalDetailText");
const journalDetailActionsRow = $("journalDetailActionsRow");
const journalDetailDominant = $("journalDetailDominant");
const journalDetailEmotion = $("journalDetailEmotion");
const journalDetailBarnhart = $("journalDetailBarnhart");
const journalFlagButton = $("journalFlagButton");
const journalEditMenuBtn = $("journalEditMenu");
const journalEditMenuDropdown = $("journalEditMenuDropdown");
const journalEditButton = $("journalEditButton");
const journalPinToggleButton = $("journalPinToggleButton");
const cancelJournalEditBtn = $("cancelJournalEdit");
const saveJournalEditBtn = $("saveJournalEdit");
const journalDeleteButton = $("journalDeleteButton");
const journalDeleteConfirmOverlay = $("journalDeleteConfirmOverlay");
const cancelJournalDeleteBtn = $("cancelJournalDelete");
const confirmJournalDeleteBtn = $("confirmJournalDelete");
const journalBackButton = $("journalBackButton");

/* Analyze button */
const analyzeBtn = $("analyze");

/* Entry help / feedback elements */
const entryHelpContainer = $("entryHelpContainer");
const entryHelpBtn = $("entryHelpBtn");
const loggedInHelpBtn = $("loggedInHelpBtn");
const feedbackOverlay = $("feedbackOverlay");
const feedbackEntryText = $("feedbackEntryText");
const feedbackAnalysisRating = $("feedbackAnalysisRating");
const feedbackText = $("feedbackText");
const feedbackError = $("feedbackError");
const cancelFeedbackBtn = $("cancelFeedback");
const submitFeedbackBtn = $("submitFeedback");

/* ---------- Utility helpers ---------- */

const titleCase = (s) => {
  if (!s || typeof s !== "string") return "N/A";
  if (s.toUpperCase() === s) return s;
  return s.charAt(0).toUpperCase() + s.slice(1);
};

function setStatus(text, isError = false) {
  const s = $("status");
  if (!s) return;
  s.textContent = text || "";
  s.className = "status" + (isError ? " err" : "");
}

const fmt = (v) =>
  typeof v === "number" ? v.toFixed(3) : String(v ?? "");

/* ---------- Word count and limit ---------- */

function wordCountAndLimit() {
  if (!textArea) return;
  let value = textArea.value;
  if (!value) {
    lastAcceptedText = "";
    if (wordInfo) wordInfo.textContent = t("wordInfoDefault");
    return;
  }

  let tokens = value
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (tokens.length > 250) {
    const prev = lastAcceptedText || "";
    const candidate = value;

    const justPeriodAllowed =
      candidate.length === prev.length + 1 &&
      candidate.endsWith(".") &&
      !prev.trim().endsWith(".");

    if (justPeriodAllowed) {
      lastAcceptedText = candidate;
    } else {
      textArea.value = prev;
    }

    value = textArea.value;
    tokens = value.trim()
      ? value
          .trim()
          .split(/\s+/)
          .filter(Boolean)
      : [];
  } else {
    lastAcceptedText = value;
  }

  const count = tokens.length;
  if (wordInfo) {
    if (count === 0) {
      wordInfo.textContent = t("wordInfoDefault");
    } else {
      wordInfo.textContent = `${count}/250 ${t("wordsLabel")}`;
    }
  }
}

/* ---------- Crisis overlay helpers ---------- */

function showCrisisModal() {
  if (crisisOverlay) crisisOverlay.classList.add("show");
}
function hideCrisisModal() {
  if (crisisOverlay) crisisOverlay.classList.remove("show");
}

if (closeCrisis) {
  closeCrisis.addEventListener("click", hideCrisisModal);
}
if (crisisOverlay) {
  crisisOverlay.addEventListener("click", (e) => {
    if (e.target === crisisOverlay) hideCrisisModal();
  });
}

/* Emergency numbers by region code for the crisis CTA */

const EMERGENCY_NUMBERS = {
  US: "911",
  CA: "911",
  BR: "190",
  PT: "112",
  ES: "112",
  MX: "911",
  INTL: "112"
};

function applyRiskToUI(risk) {
  if (!risk) return;

  const level = risk.level || "none";
  const hotline = risk.hotline || {};
  const regionCode = hotline.regionCode || "INTL";
  const hotlineNumber = hotline.number || "988";
  const emergencyNumber =
    EMERGENCY_NUMBERS[regionCode] || EMERGENCY_NUMBERS.INTL;

  if (crisisHotlineNumberSpan) {
    crisisHotlineNumberSpan.textContent = hotlineNumber;
  }
  if (crisisEmergencyNumberSpan) {
    crisisEmergencyNumberSpan.textContent = emergencyNumber;
  }

  if (crisisHotlineBtn) {
    const clean = String(hotlineNumber || "").replace(/\s+/g, "");
    crisisHotlineBtn.href = clean ? `tel:${clean}` : "#";
  }
  if (crisisEmergencyBtn) {
    const cleanE = String(emergencyNumber || "").replace(/\s+/g, "");
    crisisEmergencyBtn.href = cleanE ? `tel:${cleanE}` : "#";
  }

  if (level && level !== "none") {
    showCrisisModal();
  }
}

/* ---------- Chart setup ---------- */

const CORE_ORDER = [
  "anger",
  "disgust",
  "fear",
  "joy",
  "sadness",
  "passion",
  "surprise"
];
const CORE_COLOR = {
  anger: "var(--c-anger)",
  disgust: "var(--c-disgust)",
  fear: "var(--c-fear)",
  joy: "var(--c-joy)",
  sadness: "var(--c-sadness)",
  passion: "var(--c-passion)",
  surprise: "var(--c-surprise)"
};

function initBars() {
  const container = $("bars");
  if (!container) return;
  container.innerHTML = "";
  CORE_ORDER.forEach((key) => {
    const row = document.createElement("div");
    row.className = "barRow";

    const label = document.createElement("div");
    label.className = "barLabel";
    label.setAttribute("data-emotion-label", key);
    label.textContent = LOCALES.en.emotions[key];

    const track = document.createElement("div");
    track.className = "barTrack";

    const fill = document.createElement("div");
    fill.className = "barFill";
    fill.style.background = CORE_COLOR[key];
    fill.style.width = "0%";
    fill.id = `bar-${key}`;

    track.appendChild(fill);

    const value = document.createElement("div");
    value.className = "barValue";
    value.id = `barv-${key}`;
    value.textContent = "0.0%";

    row.appendChild(label);
    row.appendChild(track);
    row.appendChild(value);
    container.appendChild(row);
  });
}

function renderBars(mixture) {
  if (!mixture || typeof mixture !== "object") return;
  CORE_ORDER.forEach((key) => {
    const v = Number(mixture[key]) || 0;
    const pct = Math.max(0, Math.min(100, v * 100));
    const fill = $(`bar-${key}`);
    const val = $(`barv-${key}`);
    if (fill) fill.style.width = `${pct}%`;
    if (val) val.textContent = `${pct.toFixed(1)}%`;
  });
}

function renderBarsZero() {
  renderBars({
    anger: 0,
    disgust: 0,
    fear: 0,
    joy: 0,
    sadness: 0,
    passion: 0,
    surprise: 0
  });
}

/* Normalize mixture fractions */

function normalizeMix(m) {
  const keys = CORE_ORDER;
  let sum = 0;
  const out = {};
  keys.forEach((k) => {
    out[k] = Math.max(0, Number(m[k] ?? 0));
    sum += out[k];
  });
  if (sum <= 0) {
    keys.forEach((k) => (out[k] = 0));
    return out;
  }
  keys.forEach((k) => (out[k] = out[k] / sum));
  return out;
}

/* ---------- Emoji tray ---------- */

function renderEmojisFromResults(dominant, current) {
  const dom = dominant || {};
  const cur = current || {};

  const domEmoji = dom.emoji || "🤔";
  const curEmoji = cur.emoji || domEmoji;

  const same =
    dom.emotionId &&
    cur.emotionId &&
    dom.emotionId === cur.emotionId;

  if (!emojiTray) return;

  emojiTray.title = same
    ? "Dominant and current emotion match"
    : "Dominant and current emotion";
  emojiTray.textContent = same
    ? domEmoji
    : `${domEmoji} ${curEmoji}`;
}

/* ---------- Reset and error helper ---------- */

function resetToZero() {
  const numericKeys = [
    "anger",
    "disgust",
    "fear",
    "joy",
    "sadness",
    "passion",
    "surprise"
  ];
  Object.entries(fields).forEach(([key, el]) => {
    if (!el) return;
    if (numericKeys.includes(key)) {
      el.textContent = "0.000";
    } else {
      el.textContent = "N/A";
    }
  });
  if (emojiTray) {
    emojiTray.textContent = "🤔";
    emojiTray.title = "";
  }
  renderBarsZero();
  hideEntryHelpButton();
}

/* ---------- Locale application ---------- */

function t(key) {
  const loc = LOCALES[currentLocale] || LOCALES.en;
  return loc.strings[key] || LOCALES.en.strings[key] || "";
}

function applyLocale(locale) {
  currentLocale = normalizeLocaleCode(locale);
  const loc = LOCALES[currentLocale] || LOCALES.en;
  const strings = loc.strings;

  document.documentElement.setAttribute(
    "lang",
    currentLocale.split("-")[0] || "en"
  );
  document.documentElement.dir = loc.direction || "ltr";

  document
    .querySelectorAll("[data-i18n]")
    .forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key) return;
      const value =
        strings[key] || LOCALES.en.strings[key] || "";
      el.textContent = value;
    });

  document
    .querySelectorAll("[data-i18n-placeholder]")
    .forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (!key) return;
      const value =
        strings[key] || LOCALES.en.strings[key] || "";
      if (value) el.setAttribute("placeholder", value);
    });

  document
    .querySelectorAll("[data-i18n-aria-label]")
    .forEach((el) => {
      const key = el.getAttribute("data-i18n-aria-label");
      if (!key) return;
      const value =
        strings[key] || LOCALES.en.strings[key] || "";
      if (value) el.setAttribute("aria-label", value);
    });

  document
    .querySelectorAll("[data-emotion-label]")
    .forEach((el) => {
      const emoKey = el.getAttribute("data-emotion-label");
      const emoName =
        loc.emotions[emoKey] ||
        LOCALES.en.emotions[emoKey] ||
        emoKey;
      el.textContent = emoName;
    });

  if (wordInfo) {
    const text = wordInfo.textContent || "";
    if (
      !text ||
      text === LOCALES.en.strings.wordInfoDefault ||
      text === strings.wordInfoDefault
    ) {
      wordInfo.textContent =
        strings.wordInfoDefault ||
        LOCALES.en.strings.wordInfoDefault;
    }
  }
}

function buildLangMenuFor(container) {
  if (!container) return;
  container.innerHTML = "";

  const heading = document.createElement("div");
  heading.className = "langHeading";
  heading.textContent = t("langMenuLabel") || "Language";
  container.appendChild(heading);

  SUPPORTED_LOCALES.forEach((code) => {
    const def = LOCALES[code];
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "langOption";
    btn.dataset.locale = code;
    btn.setAttribute("role", "menuitemradio");
    btn.setAttribute(
      "aria-checked",
      code === currentLocale ? "true" : "false"
    );

    const nameSpan = document.createElement("span");
    nameSpan.textContent = def.name;
    const shortSpan = document.createElement("span");
    shortSpan.textContent = def.short || code.toUpperCase();

    btn.appendChild(nameSpan);
    btn.appendChild(shortSpan);

    container.appendChild(btn);
  });
}

function updateLangUI() {
  const loc = LOCALES[currentLocale] || LOCALES.en;
  const short = loc.short || currentLocale.toUpperCase();

  if (langCurrentLabel) {
    langCurrentLabel.textContent = short;
  }
  if (accountLangCurrentLabel) {
    accountLangCurrentLabel.textContent = short;
  }

  if (langMenu) {
    langMenu
      .querySelectorAll(".langOption")
      .forEach((btn) => {
        const code = btn.dataset.locale;
        btn.setAttribute(
          "aria-checked",
          code === currentLocale ? "true" : "false"
        );
      });
    const heading = langMenu.querySelector(".langHeading");
    if (heading) heading.textContent = t("langMenuLabel") || "Language";
  }

  if (accountLangMenu) {
    accountLangMenu
      .querySelectorAll(".langOption")
      .forEach((btn) => {
        const code = btn.dataset.locale;
        btn.setAttribute(
          "aria-checked",
          code === currentLocale ? "true" : "false"
        );
      });
    const heading = accountLangMenu.querySelector(".langHeading");
    if (heading) heading.textContent = t("langMenuLabel") || "Language";
  }
}

function setLocale(locale, { persist = true } = {}) {
  applyLocale(locale);
  updateLangUI();
  if (persist && !currentUser) {
    try {
      localStorage.setItem("in-tuned-locale", currentLocale);
    } catch (e) {}
  }
}

/* ---------- Language dropdown events (guest) ---------- */

if (langToggle) {
  langToggle.addEventListener("click", () => {
    if (!langMenu) return;
    const isOpen = langMenu.classList.contains("open");
    if (isOpen) {
      langMenu.classList.remove("open");
      langToggle.setAttribute("aria-expanded", "false");
    } else {
      langMenu.classList.add("open");
      langToggle.setAttribute("aria-expanded", "true");
    }
  });
}

if (langMenu) {
  langMenu.addEventListener("click", (e) => {
    const btn = e.target.closest(".langOption");
    if (!btn) return;
    const code = btn.dataset.locale;
    if (!code) return;
    langMenu.classList.remove("open");
    if (langToggle) langToggle.setAttribute("aria-expanded", "false");
    setLocale(code);
  });
  document.addEventListener("click", (e) => {
    if (!langMenu.classList.contains("open")) return;
    if (
      langMenu.contains(e.target) ||
      (langToggle && langToggle.contains(e.target))
    )
      return;
    langMenu.classList.remove("open");
    if (langToggle) langToggle.setAttribute("aria-expanded", "false");
  });
}

/* ---------- Settings menu (guest) ---------- */

if (settingsBtn && settingsMenu) {
  settingsBtn.addEventListener("click", () => {
    const isOpen = settingsMenu.classList.contains("open");
    if (isOpen) {
      settingsMenu.classList.remove("open");
      settingsBtn.setAttribute("aria-expanded", "false");
      if (langMenu) {
        langMenu.classList.remove("open");
        if (langToggle) langToggle.setAttribute("aria-expanded", "false");
      }
    } else {
      settingsMenu.classList.add("open");
      settingsBtn.setAttribute("aria-expanded", "true");
    }
  });

  document.addEventListener("click", (e) => {
    if (!settingsMenu.classList.contains("open")) return;
    if (
      settingsMenu.contains(e.target) ||
      settingsBtn.contains(e.target)
    )
      return;
    settingsMenu.classList.remove("open");
    settingsBtn.setAttribute("aria-expanded", "false");
    if (langMenu) {
      langMenu.classList.remove("open");
      if (langToggle) langToggle.setAttribute("aria-expanded", "false");
    }
  });
}

/* ---------- Help modal ---------- */

if (helpBtn && overlay) {
  helpBtn.addEventListener("click", () =>
    overlay.classList.add("show")
  );
}
if (closeModal && overlay) {
  closeModal.addEventListener("click", () =>
    overlay.classList.remove("show")
  );
}
if (overlay) {
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.classList.remove("show");
  });
}

/* ---------- Theme helpers ---------- */

function applyGuestTheme() {
  let theme = "dark";
  try {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: light)").matches
    ) {
      theme = "light";
    }
  } catch (e) {}
  root.setAttribute("data-theme", theme);
}

function applyUserTheme(theme) {
  let tTheme = theme;
  if (tTheme !== "light" && tTheme !== "dark") {
    tTheme = "dark";
    try {
      if (
        window.matchMedia &&
        window.matchMedia("(prefers-color-scheme: light)").matches
      ) {
        tTheme = "light";
      }
    } catch (e) {}
  }
  root.setAttribute("data-theme", tTheme || "dark");
}

/* ---------- Region helper for backend ---------- */

function detectRegionFromNavigator() {
  const navLang =
    (navigator.languages && navigator.languages[0]) ||
    navigator.language ||
    "en-US";

  const parts = navLang.split("-");
  if (parts.length > 1) {
    const regionCandidate = parts[1].toUpperCase();
    if (EMERGENCY_NUMBERS[regionCandidate]) {
      return regionCandidate;
    }
  }

  const base = parts[0].toLowerCase();
  if (base === "pt") return "BR";
  if (base === "es") return "ES";
  if (base === "fr") return "CA";
  return "US";
}

/* ---------- Helpers for analysis result labels and snapshots ---------- */

function getResultEmotionLabel(entry) {
  if (!entry) return "";
  return (
    entry.labelLocalized ||
    entry.nuancedLabelLocalized ||
    entry.nuancedLabel ||
    entry.label ||
    entry.emotionId ||
    ""
  );
}

function getDominantLabel(entry) {
  if (!entry) return "";
  return (
    entry.labelLocalized ||
    entry.label ||
    entry.emotionId ||
    ""
  );
}

function getCurrentEmotionPhrase(entry) {
  if (!entry) return "";
  return (
    entry.nuancedLabelLocalized ||
    entry.nuancedLabel ||
    entry.labelLocalized ||
    entry.label ||
    entry.emotionId ||
    ""
  );
}

/* Metric rendering helper for valence, activation, intensity, confidence, pattern, prototype */

function renderMetricField(el, sourceObj, fallbackNumber) {
  if (!el) return;

  if (!sourceObj && typeof fallbackNumber !== "number") {
    el.textContent = "N/A";
    return;
  }

  const obj = sourceObj || {};
  const parts = [];

  const label =
    obj.labelLocalized ||
    obj.label ||
    obj.rating ||
    obj.bucket ||
    obj.name ||
    "";

  if (label) {
    parts.push(label);
  }

  let num = null;
  if (typeof obj.score === "number") {
    num = obj.score;
  } else if (typeof obj.value === "number") {
    num = obj.value;
  } else if (typeof fallbackNumber === "number") {
    num = fallbackNumber;
  }

  if (typeof num === "number") {
    parts.push(num.toFixed(3));
  }

  if (!parts.length) {
    el.textContent = "N/A";
  } else {
    el.textContent = parts.join(" · ");
  }
}

/**
 * Build the text block for an analysis snapshot.
 * Emotions are listed with labels on the left and
 * percentages aligned in a column on the right.
 * Then Dominant and Current emotion lines are appended.
 */
function buildAnalysisSnapshotText(analysis) {
  if (!analysis || typeof analysis !== "object") return "";

  const core = Array.isArray(analysis.coreMixture)
    ? analysis.coreMixture
    : [];

  const nonZero = core
    .filter(
      (row) =>
        row &&
        typeof row.percent === "number" &&
        row.percent > 0
    )
    .slice()
    .sort(
      (a, b) =>
        (b.percent || 0) - (a.percent || 0)
    );

  const rows = [];

  nonZero.forEach((row) => {
    const baseLabel =
      row.labelLocalized || row.label || row.id || "";
    if (!baseLabel) return;
    const labelWithColon = `${baseLabel}:`;
    const pctNum =
      typeof row.percent === "number" ? row.percent : 0;
    const pctStr = pctNum.toFixed(1);
    rows.push({
      label: labelWithColon,
      pct: pctStr
    });
  });

  let maxLabelLen = 0;
  rows.forEach((r) => {
    if (r.label.length > maxLabelLen) {
      maxLabelLen = r.label.length;
    }
  });

  const lines = [];

  rows.forEach((r) => {
    const paddedLabel = r.label.padEnd(maxLabelLen + 2);
    lines.push(`${paddedLabel}${r.pct}%`);
  });

  const results = analysis.results || {};
  const dom = results.dominant || {};
  const cur = results.current || {};

  const domName = getResultEmotionLabel(dom);
  const curName = getResultEmotionLabel(cur);

  if (domName || curName) {
    const domLabel = t("resultsDominantLabel") || "Dominant";
    const curLabel =
      t("resultsEmotionLabel") || "Current emotion";

    if (lines.length > 0) {
      lines.push("");
    }
    if (domName) {
      lines.push(`${domLabel}: ${domName}`);
    }
    if (curName) {
      lines.push(`${curLabel}: ${curName}`);
    }
  }

  return lines.join("\n");
}

/* ---------- Apply API analysis to UI ---------- */

function renderResultsMeta(data) {
  const results = data.results || {};
  const metrics = data.metrics || {};

  const secondary = results.secondary || {};
  if (fields.secondary_emotion) {
    const label = getResultEmotionLabel(secondary) || "N/A";
    fields.secondary_emotion.textContent = label;
  }

  const mixed = results.mixed_state || {};
  if (fields.mixed_state) {
    let mixedLabel = "N/A";
    if (typeof mixed.is_mixed === "boolean") {
      mixedLabel = mixed.is_mixed
        ? t("resultsMixedYes") || "Yes"
        : t("resultsMixedNo") || "No";
    } else if (mixed.labelLocalized || mixed.label) {
      mixedLabel = mixed.labelLocalized || mixed.label;
    }
    fields.mixed_state.textContent = mixedLabel;
  }

  const valenceObj =
    results.valence ||
    metrics.valence ||
    data.valence ||
    null;
  const activationObj =
    results.activation ||
    metrics.activation ||
    data.activation ||
    null;
  const intensityObj =
    results.intensity ||
    metrics.intensity ||
    data.intensity ||
    null;
  const patternObj =
    results.pattern ||
    data.pattern ||
    metrics.pattern ||
    null;
  const prototypeObj =
    results.prototype ||
    data.prototype ||
    metrics.prototype ||
    null;

  if (fields.valence) {
    renderMetricField(fields.valence, valenceObj);
  }
  if (fields.activation) {
    renderMetricField(fields.activation, activationObj);
  }
  if (fields.intensity) {
    renderMetricField(fields.intensity, intensityObj);
  }
  if (fields.pattern) {
    renderMetricField(fields.pattern, patternObj);
  }
  if (fields.prototype) {
    renderMetricField(fields.prototype, prototypeObj);
  }

  if (fields.confidence_metric) {
    const confidenceObj =
      results.confidence ||
      metrics.confidence_detail ||
      null;
    const confidenceNumber =
      typeof metrics.confidence === "number"
        ? metrics.confidence
        : undefined;
    renderMetricField(
      fields.confidence_metric,
      confidenceObj,
      confidenceNumber
    );
  }
}

function applyAnalysisFromApi(data, sourceText) {
  const analysis = data.analysis || [];
  const analysisById = {};
  analysis.forEach((row) => {
    if (row && row.id) {
      analysisById[row.id] = row;
    }
  });

  CORE_ORDER.forEach((id) => {
    const el = fields[id];
    if (!el) return;
    const row = analysisById[id];
    if (!row) {
      el.textContent = "0.000";
      return;
    }
    if (typeof row.score === "number") {
      el.textContent = fmt(row.score);
    } else if (typeof row.scoreDisplay === "string") {
      el.textContent = row.scoreDisplay;
    } else {
      el.textContent = "0.000";
    }
  });

  const results = data.results || {};
  const dom = results.dominant || {};
  const cur = results.current || {};

  const domLabel =
    getDominantLabel(dom) || "N/A";

  const curLabel =
    getCurrentEmotionPhrase(cur) || "N/A";

  if (fields.dominant_emotion) {
    fields.dominant_emotion.textContent = domLabel;
  }
  if (fields.emotion) {
    fields.emotion.textContent = curLabel;
  }

  const mixRows = data.coreMixture || [];
  const mixture = {};
  mixRows.forEach((row) => {
    if (!row || !row.id) return;
    const pct = typeof row.percent === "number" ? row.percent : 0;
    mixture[row.id] = pct / 100;
  });

  const normalized = normalizeMix(mixture);
  renderBars(normalized);
  renderEmojisFromResults(dom, cur);

  const metrics = data.metrics || {};
  if (typeof metrics.confidence === "number") {
    const conf = metrics.confidence || 0;
    if (conf < 0.25) {
      setStatus(t("statusLowSignal"), false);
    } else {
      setStatus("");
    }
  } else {
    setStatus("");
  }

  renderResultsMeta(data);

  const risk = data.risk || {};
  applyRiskToUI(risk);

  lastAnalysisSnapshot = {
    text: sourceText,
    data
  };

  // Show the help button after successful analysis
  showEntryHelpButton();
}

/* ---------- Analyze button handler ---------- */

if (analyzeBtn && textArea) {
  analyzeBtn.addEventListener("click", async () => {
    const text = textArea.value.trim();
    if (!text) {
      setStatus(t("statusEnterText") || "Please enter some text.", true);
      textArea.classList.add("input-error");
      resetToZero();
      lastAnalysisSnapshot = null;
      return;
    }

    const wordCount = text.split(/\s+/).filter(w => w.length > 0).length;
    if (wordCount > 250) {
      setStatus(`Too many words (${wordCount}/250). Please shorten your text.`, true);
      textArea.classList.add("input-error");
      return;
    }

    setStatus(t("statusAnalyzing") || "Analyzing...");
    textArea.classList.remove("input-error");
    if (analyzeBtn) analyzeBtn.disabled = true;

    const payload = {
      text,
      locale: currentLocale,
      session_id: SESSION_ID,
      token: "5000",
      region: detectRegionFromNavigator()
    };

    let retryCount = 0;
    const maxRetries = 2;

    const attemptAnalysis = async () => {
      try {
        const res = await fetch("/api/analyze", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-App-Token": "5000"
          },
          body: JSON.stringify(payload)
        });

        let responseData;
        try {
          responseData = await res.json();
        } catch (parseErr) {
          console.error("Failed to parse response JSON:", parseErr);
          throw new Error("Invalid response from server");
        }

        if (!res.ok) {
          // Extract error message from standardized error response
          const errMsg = responseData?.error?.message
            || responseData?.error
            || responseData?.message
            || `Request failed with status ${res.status}`;
          const err = new Error(errMsg);
          err.code = responseData?.error?.code || "UNKNOWN_ERROR";
          err.status = res.status;
          throw err;
        }

        // Handle both response shapes for safety:
        // Shape 1: { ok: true, data: { analysis, results, coreMixture, ... } }
        // Shape 2: { analysis, results, coreMixture, ... } (direct)
        const analysisData = responseData.data || responseData;

        // Validate we have the expected structure
        if (!analysisData || typeof analysisData !== "object") {
          console.error("Unexpected response structure:", responseData);
          throw new Error("Invalid response structure from server");
        }

        applyAnalysisFromApi(analysisData, text);
        setStatus("Analysis complete");

      } catch (err) {
        console.error("Analysis error:", err);

        if (retryCount < maxRetries &&
            (err.message.includes('Network error') || err.message.includes('Failed to fetch'))) {
          retryCount++;
          setStatus(`Connection issue. Retrying (${retryCount}/${maxRetries})...`);
          await new Promise(resolve => setTimeout(resolve, 1000 * retryCount));
          return attemptAnalysis();
        }

        const msg = err && err.message ? err.message : "Unexpected error occurred";
        setStatus(msg, true);
        textArea.classList.add("input-error");
        resetToZero();
        lastAnalysisSnapshot = null;
      }
    };

    try {
      await attemptAnalysis();
    } finally {
      if (analyzeBtn) analyzeBtn.disabled = false;
    }
  });
}

/* ---------- Text input handler ---------- */

if (textArea) {
  textArea.addEventListener("input", () => {
    wordCountAndLimit();
    if (textArea.classList.contains("input-error")) {
      textArea.classList.remove("input-error");
    }
    const s = $("status");
    if (s && s.textContent) {
      setStatus("");
    }
  });
}

/* ---------- Site state: maintenance and notice ---------- */

async function loadSiteState() {
  try {
    const data = await apiFetchJSON("/api/site-state", {
      method: "GET"
    });

    const siteState = data.data || data;
    const maintenance = !!siteState.maintenance_mode;
    const message =
      siteState.maintenance_message ||
      t("maintenanceMessage") ||
      "Site is currently down due to maintenance. We will be back shortly.";
    const notice = siteState.notice;

    if (maintenance) {
      if (maintenanceShell) {
        maintenanceShell.classList.remove("hidden");
      }
      if (maintenanceMessageEl) {
        maintenanceMessageEl.textContent = message;
      }
      if (appHeader) appHeader.classList.add("hidden");
      if (appMain) appMain.classList.add("hidden");
      if (appFooter) appFooter.classList.add("hidden");
      if (noticeBanner) noticeBanner.classList.add("hidden");
    } else {
      if (maintenanceShell) {
        maintenanceShell.classList.add("hidden");
      }
      if (appHeader) appHeader.classList.remove("hidden");
      if (appMain) appMain.classList.remove("hidden");
      if (appFooter) appFooter.classList.remove("hidden");

      if (notice && notice.text) {
        if (noticeBanner) {
          noticeBanner.textContent = notice.text;
          noticeBanner.classList.remove("hidden");
        }
      } else if (noticeBanner) {
        noticeBanner.textContent = "";
        noticeBanner.classList.add("hidden");
      }
    }
  } catch (e) {
    if (maintenanceShell) maintenanceShell.classList.add("hidden");
    if (appHeader) appHeader.classList.remove("hidden");
    if (appMain) appMain.classList.remove("hidden");
    if (appFooter) appFooter.classList.remove("hidden");
    if (noticeBanner) {
      noticeBanner.textContent = "";
      noticeBanner.classList.add("hidden");
    }
  }
}

/* ---------- Auth overlays helper ---------- */

function hideAllAuthOverlays() {
  if (authOverlayLogin) authOverlayLogin.classList.remove("show");
  if (authOverlayRegister) authOverlayRegister.classList.remove("show");
  if (authOverlayForgot) authOverlayForgot.classList.remove("show");
  if (deleteAccountOverlay) deleteAccountOverlay.classList.remove("show");
  if (accountSettingsOverlay) accountSettingsOverlay.classList.remove("show");
}

function openLoginOverlay() {
  hideAllAuthOverlays();
  if (authOverlayLogin) authOverlayLogin.classList.add("show");
  if (loginIdentifierInput) loginIdentifierInput.value = "";
  if (loginPasswordInput) loginPasswordInput.value = "";
  if (loginError) {
    loginError.textContent = "";
    loginError.classList.add("hidden");
    loginError.style.color = "";
  }
}

function openRegisterOverlay() {
  hideAllAuthOverlays();
  if (authOverlayRegister) authOverlayRegister.classList.add("show");
  if (registerForm) registerForm.reset();
  if (registerError) {
    registerError.textContent = "";
    registerError.classList.add("hidden");
  }
}

function openForgotOverlay() {
  hideAllAuthOverlays();
  if (authOverlayForgot) authOverlayForgot.classList.add("show");
  if (forgotError) {
    forgotError.textContent = "";
    forgotError.classList.add("hidden");
  }
  if (forgotStepIdentity) forgotStepIdentity.classList.remove("hidden");
  if (forgotStepReset) forgotStepReset.classList.add("hidden");
  if (forgotNewPassword) forgotNewPassword.value = "";
  if (forgotConfirmPassword) forgotConfirmPassword.value = "";
}

/* Close auth overlays when background clicked */

[authOverlayLogin, authOverlayRegister, authOverlayForgot].forEach(
  (ov) => {
    if (!ov) return;
    ov.addEventListener("click", (e) => {
      if (e.target === ov) {
        hideAllAuthOverlays();
      }
    });
  }
);

/* ---------- Account header state ---------- */

function applyUserState() {
  const loggedIn = !!(currentUser && currentUser.id);

  if (loggedIn) {
    if (loginBtn) loginBtn.classList.add("hidden");
    if (accountControl) accountControl.classList.remove("hidden");
    if (helpBtn) helpBtn.classList.add("hidden");
    if (settingsControl) settingsControl.classList.add("hidden");

    if (accountNameLabel) {
      const fallback = t("accountLabel") || "Account";
      accountNameLabel.textContent =
        currentUser.first_name || fallback;
    }

    const lang = currentUser.preferred_language || currentLocale;
    setLocale(lang, { persist: false });
    applyUserTheme(currentUser.preferred_theme || null);

    if (addJournalButton) addJournalButton.classList.remove("hidden");
    if (addJournalHint) addJournalHint.classList.remove("hidden");
  } else {
    if (loginBtn) {
      loginBtn.classList.remove("hidden");
      const label = t("loginButtonLabel") || "Log in";
      loginBtn.textContent = label;
    }
    if (accountControl) accountControl.classList.add("hidden");
    if (helpBtn) helpBtn.classList.remove("hidden");
    if (settingsControl) settingsControl.classList.remove("hidden");

    applyGuestTheme();
    setLocale(currentLocale, { persist: true });

    if (addJournalButton) addJournalButton.classList.add("hidden");
    if (addJournalHint) addJournalHint.classList.add("hidden");
  }
}

/* ---------- Fetch current user on load ---------- */

async function fetchCurrentUser() {
  try {
    const data = await apiFetchJSON("/api/auth/me", {
      method: "GET"
    });
    const payload = data.data || data;
    currentUser = payload.user || null;
  } catch (e) {
    currentUser = null;
  }
  applyUserState();
}

/* ---------- Auth flows ---------- */

/* Login */

if (loginBtn) {
  loginBtn.addEventListener("click", () => {
    openLoginOverlay();
  });
}

if (cancelLoginBtn) {
  cancelLoginBtn.addEventListener("click", () => {
    hideAllAuthOverlays();
  });
}

if (openRegisterFromLoginBtn) {
  openRegisterFromLoginBtn.addEventListener("click", () => {
    openRegisterOverlay();
  });
}

if (openForgotFromLoginBtn) {
  openForgotFromLoginBtn.addEventListener("click", () => {
    openForgotOverlay();
  });
}

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!loginIdentifierInput || !loginPasswordInput) return;

    const identifier = loginIdentifierInput.value.trim();
    const password = loginPasswordInput.value;

    if (!identifier || !password) {
      if (loginError) {
        loginError.textContent =
          "Email or username and password are required.";
        loginError.classList.remove("hidden");
      }
      return;
    }

    if (submitLoginBtn) submitLoginBtn.disabled = true;

    try {
      const data = await apiFetchJSON("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ identifier, password })
      });
      const loginPayload = data.data || data;
      currentUser = loginPayload.user || null;
      hideAllAuthOverlays();
      applyUserState();
    } catch (err) {
      if (loginError) {
        loginError.textContent =
          err.message || "Invalid credentials.";
        loginError.classList.remove("hidden");
      }
    } finally {
      if (submitLoginBtn) submitLoginBtn.disabled = false;
      if (loginPasswordInput) loginPasswordInput.value = "";
    }
  });
}

/* Register */

if (cancelRegisterBtn) {
  cancelRegisterBtn.addEventListener("click", () => {
    hideAllAuthOverlays();
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (
      !registerFirstName ||
      !registerLastName ||
      !registerUsername ||
      !registerEmail ||
      !registerPassword ||
      !registerConfirmPassword
    )
      return;

    const first_name = registerFirstName.value.trim();
    const last_name = registerLastName.value.trim();
    const username = registerUsername.value.trim();
    const email = registerEmail.value.trim();
    const password = registerPassword.value;
    const confirm = registerConfirmPassword.value;

    if (!first_name || !last_name || !username || !email || !password) {
      if (registerError) {
        registerError.textContent = "All fields are required.";
        registerError.classList.remove("hidden");
      }
      return;
    }
    if (password !== confirm) {
      if (registerError) {
        registerError.textContent = "Passwords do not match.";
        registerError.classList.remove("hidden");
      }
      return;
    }

    if (submitRegisterBtn) submitRegisterBtn.disabled = true;

    try {
      const data = await apiFetchJSON("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({
          first_name,
          last_name,
          username,
          email,
          password
        })
      });
      const regPayload = data.data || data;
      currentUser = regPayload.user || null;
      hideAllAuthOverlays();
      applyUserState();
      if (registerForm) registerForm.reset();
      // Fallback: re-fetch user from session to guarantee state is correct
      if (!currentUser || !currentUser.id) {
        await fetchCurrentUser();
      }
    } catch (err) {
      // The server may have created the account and set the session cookie
      // even when it returns an error (e.g. 500). Check if we're actually
      // logged in before showing the error.
      try {
        await fetchCurrentUser();
      } catch (_ignored) { /* fetchCurrentUser handles its own errors */ }

      if (currentUser && currentUser.id) {
        // Account was created successfully despite the error response.
        // Close the overlay and update the UI.
        hideAllAuthOverlays();
        applyUserState();
        if (registerForm) registerForm.reset();
      } else {
        if (registerError) {
          registerError.textContent =
            err.message || "Unable to create account.";
          registerError.classList.remove("hidden");
        }
      }
    } finally {
      if (submitRegisterBtn) submitRegisterBtn.disabled = false;
      if (registerPassword) registerPassword.value = "";
      if (registerConfirmPassword) registerConfirmPassword.value = "";
    }
  });
}

/* Forgot password (two step flow) */

if (cancelForgotBtn) {
  cancelForgotBtn.addEventListener("click", () => {
    hideAllAuthOverlays();
  });
}

if (cancelForgotResetBtn) {
  cancelForgotResetBtn.addEventListener("click", () => {
    hideAllAuthOverlays();
  });
}

if (forgotContinueBtn) {
  forgotContinueBtn.addEventListener("click", () => {
    if (!forgotEmail || !forgotFirstName || !forgotLastName) return;

    const email = forgotEmail.value.trim();
    const first_name = forgotFirstName.value.trim();
    const last_name = forgotLastName.value.trim();

    if (!email || !first_name || !last_name) {
      if (forgotError) {
        forgotError.textContent = "All fields are required.";
        forgotError.classList.remove("hidden");
      }
      return;
    }

    if (forgotError) {
      forgotError.textContent = "";
      forgotError.classList.add("hidden");
    }

    if (forgotStepIdentity) forgotStepIdentity.classList.add("hidden");
    if (forgotStepReset) forgotStepReset.classList.remove("hidden");
  });
}

if (forgotForm) {
  forgotForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (
      !forgotEmail ||
      !forgotFirstName ||
      !forgotLastName ||
      !forgotNewPassword ||
      !forgotConfirmPassword
    )
      return;

    const email = forgotEmail.value.trim();
    const first_name = forgotFirstName.value.trim();
    const last_name = forgotLastName.value.trim();
    const new_password = forgotNewPassword.value;
    const confirm_password = forgotConfirmPassword.value;

    if (
      !email ||
      !first_name ||
      !last_name ||
      !new_password ||
      !confirm_password
    ) {
      if (forgotError) {
        forgotError.textContent = "All fields are required.";
        forgotError.classList.remove("hidden");
      }
      return;
    }

    if (new_password !== confirm_password) {
      if (forgotError) {
        forgotError.textContent = "Passwords do not match.";
        forgotError.classList.remove("hidden");
      }
      return;
    }

    if (submitForgotBtn) submitForgotBtn.disabled = true;

    try {
      await apiFetchJSON("/api/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({
          email,
          first_name,
          last_name,
          new_password,
          confirm_password
        })
      });
      hideAllAuthOverlays();
      if (forgotForm) forgotForm.reset();
      if (forgotStepIdentity) forgotStepIdentity.classList.remove("hidden");
      if (forgotStepReset) forgotStepReset.classList.add("hidden");
      openLoginOverlay();
      if (loginError) {
        loginError.textContent = "Password reset successful. Please log in.";
        loginError.classList.remove("hidden");
        loginError.style.color = "var(--accent)";
        setTimeout(() => {
          loginError.style.color = "";
        }, 5000);
      }
    } catch (err) {
      if (forgotError) {
        forgotError.textContent =
          err.message || "Unable to reset password.";
        forgotError.classList.remove("hidden");
      }
    } finally {
      if (submitForgotBtn) submitForgotBtn.disabled = false;
      if (forgotNewPassword) forgotNewPassword.value = "";
      if (forgotConfirmPassword) forgotConfirmPassword.value = "";
    }
  });
}

/* ---------- Account menu actions ---------- */

if (accountBtn && accountMenu) {
  accountBtn.addEventListener("click", () => {
    const isOpen = accountMenu.classList.contains("open");
    if (isOpen) {
      accountMenu.classList.remove("open");
      accountBtn.setAttribute("aria-expanded", "false");
    } else {
      accountMenu.classList.add("open");
      accountBtn.setAttribute("aria-expanded", "true");
    }
  });

  document.addEventListener("click", (e) => {
    if (!accountMenu.classList.contains("open")) return;
    if (
      accountMenu.contains(e.target) ||
      accountBtn.contains(e.target)
    )
      return;
    accountMenu.classList.remove("open");
    accountBtn.setAttribute("aria-expanded", "false");
  });

  accountMenu.addEventListener("click", async (e) => {
    const btn = e.target.closest(".accountMenuItem");
    if (!btn) return;
    const action = btn.dataset.action;

    if (action === "journal") {
      openJournalOverlay();
    } else if (action === "settings") {
      openAccountSettingsOverlay();
    } else if (action === "logout") {
      try {
        await apiFetchJSON("/api/auth/logout", {
          method: "POST"
        });
      } catch (err) {}
      currentUser = null;
      applyUserState();
    }

    accountMenu.classList.remove("open");
    accountBtn.setAttribute("aria-expanded", "false");
  });
}

/* ---------- Account settings overlay ---------- */

let accountSettingsSnapshot = {
  theme: null,
  language: null
};

function openAccountSettingsOverlay() {
  if (!currentUser) return;
  const currentTheme =
    root.getAttribute("data-theme") || "dark";
  const currentLang = currentLocale;

  accountSettingsSnapshot = {
    theme: currentTheme,
    language: currentLang
  };

  if (accountSettingsOverlay) {
    accountSettingsOverlay.classList.add("show");
  }
  if (accountSettingsError) {
    accountSettingsError.textContent = "";
    accountSettingsError.classList.add("hidden");
  }
}

function closeAccountSettingsOverlay(resetToSnapshot) {
  if (resetToSnapshot && currentUser && accountSettingsSnapshot) {
    applyUserTheme(accountSettingsSnapshot.theme);
    setLocale(accountSettingsSnapshot.language, { persist: false });
  }
  if (accountSettingsOverlay) {
    accountSettingsOverlay.classList.remove("show");
  }
}

if (accountSettingsOverlay) {
  accountSettingsOverlay.addEventListener("click", (e) => {
    if (e.target === accountSettingsOverlay) {
      closeAccountSettingsOverlay(true);
    }
  });
}

if (cancelAccountSettingsBtn) {
  cancelAccountSettingsBtn.addEventListener("click", () => {
    closeAccountSettingsOverlay(true);
  });
}

if (accountThemeToggle) {
  accountThemeToggle.addEventListener("click", () => {
    if (!currentUser) return;
    const current =
      root.getAttribute("data-theme") === "light"
        ? "light"
        : "dark";
    const next = current === "dark" ? "light" : "dark";
    applyUserTheme(next);
    accountSettingsSnapshot.theme = next;
  });
}

if (accountLangToggle && accountLangMenu) {
  accountLangToggle.addEventListener("click", () => {
    const isOpen = accountLangMenu.classList.contains("open");
    if (isOpen) {
      accountLangMenu.classList.remove("open");
      accountLangToggle.setAttribute("aria-expanded", "false");
    } else {
      accountLangMenu.classList.add("open");
      accountLangToggle.setAttribute("aria-expanded", "true");
    }
  });

  accountLangMenu.addEventListener("click", (e) => {
    const btn = e.target.closest(".langOption");
    if (!btn) return;
    const code = btn.dataset.locale;
    if (!code) return;
    const normalized = normalizeLocaleCode(code);
    accountLangMenu.classList.remove("open");
    accountLangToggle.setAttribute("aria-expanded", "false");
    accountSettingsSnapshot.language = normalized;
    setLocale(normalized, { persist: false });
  });

  document.addEventListener("click", (e) => {
    if (!accountLangMenu.classList.contains("open")) return;
    if (
      accountLangMenu.contains(e.target) ||
      accountLangToggle.contains(e.target)
    )
      return;
    accountLangMenu.classList.remove("open");
    accountLangToggle.setAttribute("aria-expanded", "false");
  });
}

if (accountSettingsForm) {
  accountSettingsForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!currentUser) return;

    const preferred_language = accountSettingsSnapshot.language;
    const preferred_theme = accountSettingsSnapshot.theme;

    if (saveAccountSettingsBtn) saveAccountSettingsBtn.disabled = true;

    try {
      const data = await apiFetchJSON("/api/auth/update-settings", {
        method: "POST",
        body: JSON.stringify({
          preferred_language,
          preferred_theme
        })
      });
      const settingsPayload = data.data || data;
      currentUser = settingsPayload.user || currentUser;
      applyUserTheme(currentUser.preferred_theme || null);
      setLocale(currentUser.preferred_language || currentLocale, {
        persist: false
      });
      if (accountSettingsError) {
        accountSettingsError.textContent = "";
        accountSettingsError.classList.add("hidden");
      }
      closeAccountSettingsOverlay(false);
    } catch (err) {
      if (accountSettingsError) {
        accountSettingsError.textContent =
          err.message || "Unable to save settings.";
        accountSettingsError.classList.remove("hidden");
      }
    } finally {
      if (saveAccountSettingsBtn)
        saveAccountSettingsBtn.disabled = false;
    }
  });
}

/* ---------- Delete account ---------- */

function openDeleteAccountOverlay() {
  closeAccountSettingsOverlay(false);
  if (deleteAccountOverlay) deleteAccountOverlay.classList.add("show");
  if (deleteAccountPassword) deleteAccountPassword.value = "";
  if (deleteConfirmSure) deleteConfirmSure.checked = false;
  if (deleteConfirmUnderstand) deleteConfirmUnderstand.checked = false;
  if (deleteAccountError) {
    deleteAccountError.textContent = "";
    deleteAccountError.classList.add("hidden");
  }
  updateDeleteButtonState();
}

function closeDeleteAccountOverlay() {
  if (deleteAccountOverlay) deleteAccountOverlay.classList.remove("show");
}

function updateDeleteButtonState() {
  if (!confirmDeleteAccountBtn) return;
  const passwordFilled = deleteAccountPassword && deleteAccountPassword.value.length > 0;
  const sureChecked = deleteConfirmSure && deleteConfirmSure.checked;
  const understandChecked = deleteConfirmUnderstand && deleteConfirmUnderstand.checked;
  confirmDeleteAccountBtn.disabled = !(passwordFilled && sureChecked && understandChecked);
}

if (openDeleteAccountBtn) {
  openDeleteAccountBtn.addEventListener("click", () => {
    openDeleteAccountOverlay();
  });
}

if (cancelDeleteAccountBtn) {
  cancelDeleteAccountBtn.addEventListener("click", () => {
    closeDeleteAccountOverlay();
  });
}

if (deleteAccountOverlay) {
  deleteAccountOverlay.addEventListener("click", (e) => {
    if (e.target === deleteAccountOverlay) {
      closeDeleteAccountOverlay();
    }
  });
}

if (deleteConfirmSure) {
  deleteConfirmSure.addEventListener("change", updateDeleteButtonState);
}
if (deleteConfirmUnderstand) {
  deleteConfirmUnderstand.addEventListener("change", updateDeleteButtonState);
}
if (deleteAccountPassword) {
  deleteAccountPassword.addEventListener("input", updateDeleteButtonState);
}

if (confirmDeleteAccountBtn) {
  confirmDeleteAccountBtn.addEventListener("click", async () => {
    if (!currentUser) return;
    const password = deleteAccountPassword ? deleteAccountPassword.value : "";

    if (!password) {
      if (deleteAccountError) {
        deleteAccountError.textContent = "Password is required.";
        deleteAccountError.classList.remove("hidden");
      }
      return;
    }

    confirmDeleteAccountBtn.disabled = true;

    try {
      await apiFetchJSON("/api/users/account", {
        method: "DELETE",
        body: JSON.stringify({
          password: password,
          confirmation: "DELETE"
        })
      });
      currentUser = null;
      closeDeleteAccountOverlay();
      hideAllAuthOverlays();
      applyUserState();
    } catch (err) {
      if (deleteAccountError) {
        deleteAccountError.textContent =
          err.message || "Unable to delete account.";
        deleteAccountError.classList.remove("hidden");
      }
      updateDeleteButtonState();
    }
  });
}

/* ---------- Journal overlay and APIs ---------- */

function openJournalOverlay() {
  if (!currentUser) {
    openLoginOverlay();
    return;
  }
  if (journalOverlay) {
    journalOverlay.classList.add("show");
  }
  if (journalEmptyState) journalEmptyState.classList.remove("hidden");
  if (journalDetail) journalDetail.classList.add("hidden");
  loadJournals();
}

function closeJournalOverlay() {
  if (journalOverlay) {
    journalOverlay.classList.remove("show");
  }
  currentJournal = null;
  isEditingJournal = false;
  isCreatingJournal = false;
}

if (closeJournalBtn) {
  closeJournalBtn.addEventListener("click", () => {
    closeJournalOverlay();
  });
}

if (journalOverlay) {
  journalOverlay.addEventListener("click", (e) => {
    if (e.target === journalOverlay) {
      closeJournalOverlay();
    }
  });
}

if (journalBackButton) {
  journalBackButton.addEventListener("click", () => {
    if (journalDetail) journalDetail.classList.add("hidden");
    if (journalEmptyState) journalEmptyState.classList.remove("hidden");
  });
}

async function loadJournals() {
  if (!currentUser) return;
  try {
    const data = await apiFetchJSON("/api/journals", {
      method: "GET"
    });
    journals = data.data || data.journals || [];
    renderJournalLists();
  } catch (err) {
  }
}

function renderJournalLists() {
  if (!pinnedJournalList || !journalList) return;

  pinnedJournalList.innerHTML = "";
  journalList.innerHTML = "";

  const pinned = journals.filter((j) => j.is_pinned);
  const others = journals.filter((j) => !j.is_pinned);

  if (pinned.length === 0) {
    pinnedJournalList.classList.add("hidden");
    if (pinnedSectionHeader) pinnedSectionHeader.classList.add("hidden");
  } else {
    pinnedJournalList.classList.remove("hidden");
    if (pinnedSectionHeader) pinnedSectionHeader.classList.remove("hidden");
  }

  function makeRow(journal) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "journalListItem";

    const title = document.createElement("div");
    title.className = "journalListTitle";
    title.textContent =
      journal.title || t("journalDefaultTitle") || "Journal entry";

    const meta = document.createElement("div");
    meta.className = "journalListMeta";
    meta.textContent = formatDateTime(journal.created_at);

    btn.appendChild(title);
    btn.appendChild(meta);

    if (journal.has_self_harm_flag) {
      const flag = document.createElement("span");
      flag.className = "journalListFlag";
      flag.textContent = "⚠️";
      btn.appendChild(flag);
    }

    btn.addEventListener("click", () => {
      openJournalDetail(journal.id);
    });

    return btn;
  }

  pinned.forEach((j) => {
    pinnedJournalList.appendChild(makeRow(j));
  });
  others.forEach((j) => {
    journalList.appendChild(makeRow(j));
  });
}

function formatDateTime(value) {
  if (!value) return "";
  try {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return "";
    return d.toLocaleString();
  } catch (e) {
    return "";
  }
}

async function openJournalDetail(journalId) {
  if (!currentUser) return;
  try {
    const data = await apiFetchJSON(`/api/journals/${journalId}`, {
      method: "GET"
    });
    const journalPayload = data.data || data;
    const journal = journalPayload.journal;
    currentJournal = journal;
    isEditingJournal = false;
    isCreatingJournal = false;

    if (journalEmptyState) journalEmptyState.classList.add("hidden");
    if (journalDetail) journalDetail.classList.remove("hidden");
    if (journalDetailActionsRow)
      journalDetailActionsRow.classList.add("hidden");

    if (journalDetailTitle) {
      journalDetailTitle.textContent =
        journal.title || t("journalDefaultTitle") || "Journal entry";
    }
    if (journalDetailMeta) {
      journalDetailMeta.textContent = formatDateTime(
        journal.created_at
      );
    }
    if (journalDetailSourceText) {
      journalDetailSourceText.textContent = journal.source_text || "";
    }

    const analysis = journal.analysis_json || {};
    if (journalDetailAnalysis) {
      journalDetailAnalysis.textContent =
        buildAnalysisSnapshotText(analysis);
    }

    if (journalDetailText) {
      journalDetailText.value = journal.journal_text || "";
      journalDetailText.disabled = true;
    }

    const results = (analysis && analysis.results) || {};
    const dom = results.dominant || {};
    const cur = results.current || {};
    const metrics = (analysis && analysis.metrics) || {};

    if (journalDetailDominant) {
      journalDetailDominant.textContent =
        getDominantLabel(dom) || "N/A";
    }
    if (journalDetailEmotion) {
      journalDetailEmotion.textContent =
        getCurrentEmotionPhrase(cur) || "N/A";
    }
    if (journalDetailBarnhart) {
      let barnVal = null;
      if (
        metrics.barnhart &&
        typeof metrics.barnhart.score === "number"
      ) {
        barnVal = metrics.barnhart.score;
      } else if (typeof metrics.confidence === "number") {
        barnVal = metrics.confidence;
      }
      journalDetailBarnhart.textContent =
        typeof barnVal === "number" ? barnVal.toFixed(3) : "N/A";
    }

    if (journalFlagButton) {
      if (journal.has_self_harm_flag) {
        journalFlagButton.classList.remove("hidden");
      } else {
        journalFlagButton.classList.add("hidden");
      }
    }

    if (journalPinToggleButton) {
      journalPinToggleButton.textContent = journal.is_pinned
        ? t("journalUnpin") || "Unpin"
        : t("journalPin") || "Pin";
    }
  } catch (err) {
  }
}

if (journalFlagButton) {
  journalFlagButton.addEventListener("click", () => {
    showCrisisModal();
  });
}

/* Journal edit menu */

if (journalEditMenuBtn && journalEditMenuDropdown) {
  journalEditMenuBtn.addEventListener("click", () => {
    const isOpen = !journalEditMenuDropdown.classList.contains(
      "hidden"
    );
    if (isOpen) {
      journalEditMenuDropdown.classList.add("hidden");
    } else {
      journalEditMenuDropdown.classList.remove("hidden");
    }
  });

  document.addEventListener("click", (e) => {
    if (journalEditMenuDropdown.classList.contains("hidden")) return;
    if (
      journalEditMenuDropdown.contains(e.target) ||
      journalEditMenuBtn.contains(e.target)
    )
      return;
    journalEditMenuDropdown.classList.add("hidden");
  });
}

if (journalEditButton) {
  journalEditButton.addEventListener("click", () => {
    if (!currentJournal || !journalDetailText) return;
    isEditingJournal = true;
    isCreatingJournal = false;
    journalDetailText.disabled = false;
    if (journalDetailActionsRow)
      journalDetailActionsRow.classList.remove("hidden");
    if (journalEditMenuDropdown)
      journalEditMenuDropdown.classList.add("hidden");
  });
}

if (journalPinToggleButton) {
  journalPinToggleButton.addEventListener("click", async () => {
    if (!currentJournal) return;
    if (journalEditMenuDropdown)
      journalEditMenuDropdown.classList.add("hidden");
    try {
      const nextPinned = !currentJournal.is_pinned;
      const data = await apiFetchJSON(
        `/api/journals/${currentJournal.id}/pin`,
        {
          method: "POST",
          body: JSON.stringify({ is_pinned: nextPinned })
        }
      );
      const pinPayload = data.data || data;
      currentJournal = pinPayload.journal || currentJournal;
      if (journalPinToggleButton) {
        journalPinToggleButton.textContent = currentJournal.is_pinned
          ? t("journalUnpin") || "Unpin"
          : t("journalPin") || "Pin";
      }
      await loadJournals();
    } catch (err) {
    }
  });
}

/* Journal delete menu item and confirmation */

if (journalDeleteButton) {
  journalDeleteButton.addEventListener("click", () => {
    if (!currentJournal || !journalDeleteConfirmOverlay) return;
    if (journalEditMenuDropdown) {
      journalEditMenuDropdown.classList.add("hidden");
    }
    journalDeleteConfirmOverlay.classList.add("show");
  });
}

if (cancelJournalDeleteBtn && journalDeleteConfirmOverlay) {
  cancelJournalDeleteBtn.addEventListener("click", () => {
    journalDeleteConfirmOverlay.classList.remove("show");
  });
}

if (journalDeleteConfirmOverlay) {
  journalDeleteConfirmOverlay.addEventListener("click", (e) => {
    if (e.target === journalDeleteConfirmOverlay) {
      journalDeleteConfirmOverlay.classList.remove("show");
    }
  });
}

if (confirmJournalDeleteBtn && journalDeleteConfirmOverlay) {
  confirmJournalDeleteBtn.addEventListener("click", async () => {
    if (!currentJournal) {
      journalDeleteConfirmOverlay.classList.remove("show");
      return;
    }
    try {
      await apiFetchJSON(`/api/journals/${currentJournal.id}`, {
        method: "DELETE"
      });
      currentJournal = null;
      if (journalDetail) journalDetail.classList.add("hidden");
      if (journalEmptyState)
        journalEmptyState.classList.remove("hidden");
      await loadJournals();
    } catch (err) {
    } finally {
      journalDeleteConfirmOverlay.classList.remove("show");
    }
  });
}

if (cancelJournalEditBtn) {
  cancelJournalEditBtn.addEventListener("click", () => {
    if (!currentJournal || !journalDetailText) return;
    journalDetailText.value = currentJournal.journal_text || "";
    journalDetailText.disabled = true;
    isEditingJournal = false;
    isCreatingJournal = false;
    if (journalDetailActionsRow)
      journalDetailActionsRow.classList.add("hidden");
  });
}

if (saveJournalEditBtn) {
  saveJournalEditBtn.addEventListener("click", async () => {
    if (!currentJournal || !journalDetailText) return;
    const updatedText = journalDetailText.value;
    try {
      const data = await apiFetchJSON(
        `/api/journals/${currentJournal.id}`,
        {
          method: "PUT",
          body: JSON.stringify({
            journal_text: updatedText
          })
        }
      );
      const updatePayload = data.data || data;
      currentJournal = updatePayload.journal || currentJournal;
      journalDetailText.disabled = true;
      isEditingJournal = false;
      isCreatingJournal = false;
      if (journalDetailActionsRow)
        journalDetailActionsRow.classList.add("hidden");
      await loadJournals();
    } catch (err) {
    }
  });
}

/* ---------- Add to journal from analysis ---------- */

let newJournalOverlay = null;
let newJournalSourceEl = null;
let newJournalAnalysisEl = null;
let newJournalTextEl = null;
let newJournalCancelBtn = null;
let newJournalSaveBtn = null;

function ensureNewJournalOverlay() {
  if (newJournalOverlay) return;

  const overlayEl = document.createElement("div");
  overlayEl.id = "newJournalOverlay";
  overlayEl.className = "overlay";
  overlayEl.setAttribute("role", "dialog");
  overlayEl.setAttribute("aria-modal", "true");

  const modal = document.createElement("div");
  modal.className = "modal authModal";

  const header = document.createElement("div");
  header.className = "journalHeaderRow";

  const h2 = document.createElement("h2");
  h2.textContent = t("journalNewTitle") || "New journal entry";

  const closeBtn = document.createElement("button");
  closeBtn.type = "button";
  closeBtn.className = "ghost";
  closeBtn.textContent = t("journalCancel") || "Cancel";

  header.appendChild(h2);
  header.appendChild(closeBtn);

  const content = document.createElement("div");
  content.className = "journalNewContent";

  const srcBlock = document.createElement("div");
  srcBlock.className = "journalSourceBlock";
  const srcTitle = document.createElement("h4");
  srcTitle.textContent =
    t("journalOriginalTextLabel") || "Original text";
  newJournalSourceEl = document.createElement("p");
  srcBlock.appendChild(srcTitle);
  srcBlock.appendChild(newJournalSourceEl);

  const analBlock = document.createElement("div");
  analBlock.className = "journalAnalysisBlock";
  const analTitle = document.createElement("h4");
  analTitle.textContent =
    t("journalAnalysisSnapshotLabel") || "Analysis snapshot";
  newJournalAnalysisEl = document.createElement("pre");
  newJournalAnalysisEl.style.fontFamily =
    'SF Mono, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace';
  newJournalAnalysisEl.style.whiteSpace = "pre-wrap";
  analBlock.appendChild(analTitle);
  analBlock.appendChild(newJournalAnalysisEl);

  const textBlock = document.createElement("div");
  textBlock.className = "journalTextBlock";
  const textTitle = document.createElement("h4");
  textTitle.textContent =
    t("journalJournalLabel") || "Journal";
  newJournalTextEl = document.createElement("textarea");
  newJournalTextEl.className = "journalEditArea";
  textBlock.appendChild(textTitle);
  textBlock.appendChild(newJournalTextEl);

  content.appendChild(srcBlock);
  content.appendChild(analBlock);
  content.appendChild(textBlock);

  const actionsRow = document.createElement("div");
  actionsRow.className = "actionsRow";
  newJournalCancelBtn = document.createElement("button");
  newJournalCancelBtn.type = "button";
  newJournalCancelBtn.className = "ghost";
  newJournalCancelBtn.textContent =
    t("journalCancel") || "Cancel";
  newJournalSaveBtn = document.createElement("button");
  newJournalSaveBtn.type = "button";
  newJournalSaveBtn.className = "btn";
  newJournalSaveBtn.textContent =
    t("journalSave") || "Save";
  actionsRow.appendChild(newJournalCancelBtn);
  actionsRow.appendChild(newJournalSaveBtn);

  modal.appendChild(header);
  modal.appendChild(content);
  modal.appendChild(actionsRow);
  overlayEl.appendChild(modal);
  document.body.appendChild(overlayEl);

  newJournalOverlay = overlayEl;

  overlayEl.addEventListener("click", (e) => {
    if (e.target === overlayEl) {
      closeNewJournalOverlay();
    }
  });
  closeBtn.addEventListener("click", () => {
    closeNewJournalOverlay();
  });
  newJournalCancelBtn.addEventListener("click", () => {
    closeNewJournalOverlay();
  });
  newJournalSaveBtn.addEventListener("click", () => {
    saveNewJournalEntry();
  });
}

function openNewJournalOverlay() {
  if (!lastAnalysisSnapshot) {
    setStatus(
      t("statusNeedAnalysis") ||
        "Run an analysis before adding to journal."
    );
    return;
  }
  if (!currentUser) {
    openLoginOverlay();
    return;
  }
  ensureNewJournalOverlay();
  const { text, data } = lastAnalysisSnapshot;
  if (newJournalSourceEl) {
    newJournalSourceEl.textContent = text || "";
  }
  if (newJournalAnalysisEl) {
    newJournalAnalysisEl.textContent =
      buildAnalysisSnapshotText(data || {});
  }
  if (newJournalTextEl) {
    newJournalTextEl.value = "";
  }
  if (newJournalOverlay) {
    newJournalOverlay.classList.add("show");
  }
}

function closeNewJournalOverlay() {
  if (newJournalOverlay) {
    newJournalOverlay.classList.remove("show");
  }
}

async function saveNewJournalEntry() {
  if (!lastAnalysisSnapshot || !currentUser || !newJournalTextEl)
    return;
  const { text, data } = lastAnalysisSnapshot;
  const journal_text = newJournalTextEl.value || "";

  const baseTitle = t("journalDefaultTitle") || "Journal entry";
  const title = `${baseTitle} ${new Date().toLocaleString()}`;

  try {
    await apiFetchJSON("/api/journals", {
      method: "POST",
      body: JSON.stringify({
        title,
        source_text: text,
        analysis_json: data,
        journal_text
      })
    });
    closeNewJournalOverlay();
    if (journalOverlay && journalOverlay.classList.contains("show")) {
      await loadJournals();
    }
  } catch (err) {
  }
}

if (addJournalButton) {
  addJournalButton.addEventListener("click", () => {
    if (!currentUser) {
      openLoginOverlay();
      return;
    }
    openNewJournalOverlay();
  });
}

/* ---------- Feedback / Help popup ---------- */

function showEntryHelpButton() {
  if (!lastAnalysisSnapshot) return;

  // For guests (not logged in), show the container with divider + Help button
  if (!currentUser) {
    if (entryHelpContainer) entryHelpContainer.classList.remove("hidden");
    if (loggedInHelpBtn) loggedInHelpBtn.classList.add("hidden");
  } else {
    // For logged-in users, show the icon button next to the plus button
    if (entryHelpContainer) entryHelpContainer.classList.add("hidden");
    if (loggedInHelpBtn) loggedInHelpBtn.classList.remove("hidden");
  }
}

function hideEntryHelpButton() {
  if (entryHelpContainer) entryHelpContainer.classList.add("hidden");
  if (loggedInHelpBtn) loggedInHelpBtn.classList.add("hidden");
}

function buildFeedbackAnalysisRating(analysis) {
  if (!feedbackAnalysisRating) return;

  feedbackAnalysisRating.innerHTML = "";

  const core = Array.isArray(analysis.coreMixture)
    ? analysis.coreMixture
    : [];

  const nonZero = core
    .filter(
      (row) =>
        row &&
        typeof row.percent === "number" &&
        row.percent > 0
    )
    .slice()
    .sort((a, b) => (b.percent || 0) - (a.percent || 0));

  // Build emotion bars display
  nonZero.forEach((row) => {
    const emotionRow = document.createElement("div");
    emotionRow.className = "feedbackEmotionRow";

    const label = document.createElement("span");
    label.className = "feedbackEmotionLabel";
    label.textContent = row.labelLocalized || row.label || row.id || "";

    const barContainer = document.createElement("div");
    barContainer.className = "feedbackEmotionBarContainer";

    const bar = document.createElement("div");
    bar.className = "feedbackEmotionBar";
    bar.style.width = `${row.percent}%`;
    bar.style.background = `var(--c-${row.id})`;

    const value = document.createElement("span");
    value.className = "feedbackEmotionValue";
    value.textContent = `${row.percent.toFixed(1)}%`;

    barContainer.appendChild(bar);
    emotionRow.appendChild(label);
    emotionRow.appendChild(barContainer);
    emotionRow.appendChild(value);
    feedbackAnalysisRating.appendChild(emotionRow);
  });

  // Add dominant and current emotion
  const results = analysis.results || {};
  const dom = results.dominant || {};
  const cur = results.current || {};

  const domLabel = getResultEmotionLabel(dom);
  const curLabel = getResultEmotionLabel(cur);

  if (domLabel || curLabel) {
    const resultsSummary = document.createElement("div");
    resultsSummary.className = "feedbackResultsSummary";

    if (domLabel) {
      const domRow = document.createElement("div");
      domRow.innerHTML = `<span class="feedbackSummaryLabel">Dominant:</span> <span class="feedbackSummaryValue">${domLabel}</span>`;
      resultsSummary.appendChild(domRow);
    }

    if (curLabel) {
      const curRow = document.createElement("div");
      curRow.innerHTML = `<span class="feedbackSummaryLabel">Current:</span> <span class="feedbackSummaryValue">${curLabel}</span>`;
      resultsSummary.appendChild(curRow);
    }

    feedbackAnalysisRating.appendChild(resultsSummary);
  }
}

function openFeedbackOverlay() {
  if (!lastAnalysisSnapshot) {
    setStatus("Please run an analysis first.");
    return;
  }

  const { text, data } = lastAnalysisSnapshot;

  // Prefill the entry text
  if (feedbackEntryText) {
    feedbackEntryText.value = text || "";
  }

  // Build the analysis rating display
  if (data) {
    buildFeedbackAnalysisRating(data);
  }

  // Clear feedback text and error
  if (feedbackText) {
    feedbackText.value = "";
  }
  if (feedbackError) {
    feedbackError.textContent = "";
    feedbackError.classList.add("hidden");
  }

  if (feedbackOverlay) {
    feedbackOverlay.classList.add("show");
  }
}

function closeFeedbackOverlay() {
  if (feedbackOverlay) {
    feedbackOverlay.classList.remove("show");
  }
  if (feedbackText) {
    feedbackText.value = "";
  }
  if (feedbackError) {
    feedbackError.textContent = "";
    feedbackError.classList.add("hidden");
  }
}

async function submitFeedback() {
  if (!lastAnalysisSnapshot) {
    if (feedbackError) {
      feedbackError.textContent = "No analysis data available.";
      feedbackError.classList.remove("hidden");
    }
    return;
  }

  const feedback = feedbackText ? feedbackText.value.trim() : "";

  if (!feedback) {
    if (feedbackError) {
      feedbackError.textContent = "Feedback is required.";
      feedbackError.classList.remove("hidden");
    }
    return;
  }

  if (submitFeedbackBtn) submitFeedbackBtn.disabled = true;

  try {
    const { text, data } = lastAnalysisSnapshot;

    await apiFetchJSON("/api/feedback", {
      method: "POST",
      body: JSON.stringify({
        entry_text: text,
        analysis_json: data,
        feedback_text: feedback
      })
    });

    closeFeedbackOverlay();
    setStatus("Feedback submitted. Thank you!");
  } catch (err) {
    if (feedbackError) {
      feedbackError.textContent = err.message || "Failed to submit feedback.";
      feedbackError.classList.remove("hidden");
    }
  } finally {
    if (submitFeedbackBtn) submitFeedbackBtn.disabled = false;
  }
}

// Event listeners for feedback popup
if (entryHelpBtn) {
  entryHelpBtn.addEventListener("click", openFeedbackOverlay);
}

if (loggedInHelpBtn) {
  loggedInHelpBtn.addEventListener("click", openFeedbackOverlay);
}

if (cancelFeedbackBtn) {
  cancelFeedbackBtn.addEventListener("click", closeFeedbackOverlay);
}

if (submitFeedbackBtn) {
  submitFeedbackBtn.addEventListener("click", submitFeedback);
}

if (feedbackOverlay) {
  feedbackOverlay.addEventListener("click", (e) => {
    if (e.target === feedbackOverlay) {
      closeFeedbackOverlay();
    }
  });
}

/* ---------- Responsive header for small screens ---------- */

function applyResponsiveHeaderLayout() {
  if (!appHeader) return;
  const isMobile =
    window.matchMedia &&
    window.matchMedia("(max-width: 640px)").matches;

  if (isMobile) {
    appHeader.style.display = "flex";
    appHeader.style.alignItems = "center";
    appHeader.style.justifyContent = "space-between";
    appHeader.style.gap = "12px";
  } else {
    appHeader.style.display = "";
    appHeader.style.alignItems = "";
    appHeader.style.justifyContent = "";
    appHeader.style.gap = "";
  }
}

function setupResponsiveHeader() {
  applyResponsiveHeaderLayout();
  window.addEventListener("resize", applyResponsiveHeaderLayout);
}

/* ---------- Connection Status Monitoring ---------- */

let isOnline = navigator.onLine;

function updateConnectionStatus() {
  const wasOnline = isOnline;
  isOnline = navigator.onLine;

  if (!isOnline && wasOnline) {
    setStatus("No internet connection. Please check your network.", true);
  } else if (isOnline && !wasOnline) {
    setStatus("Connection restored", false);
    loadSiteState();
    fetchCurrentUser();
  }
}

window.addEventListener('online', updateConnectionStatus);
window.addEventListener('offline', updateConnectionStatus);

/* ---------- Initial setup ---------- */

async function initialSetup() {
  initBars();
  buildLangMenuFor(langMenu);
  buildLangMenuFor(accountLangMenu);
  setLocale(currentLocale);
  renderBarsZero();
  wordCountAndLimit();
  applyGuestTheme();

  // Load site state and user data in parallel, waiting for both to complete
  // This ensures the page renders correctly after data is loaded
  await Promise.all([
    loadSiteState(),
    fetchCurrentUser()
  ]);

  if (journalDetailAnalysis) {
    journalDetailAnalysis.style.fontFamily =
      'SF Mono, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace';
    journalDetailAnalysis.style.whiteSpace = "pre-wrap";
  }

  setupResponsiveHeader();
}

document.addEventListener("DOMContentLoaded", () => {
  initialSetup().catch((err) => {
    console.error("Failed to initialize application:", err);
  });
});
