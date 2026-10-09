(() => {
  "use strict";
  const KEY = "oae.language";
  const SUPPORTED = {
    en: { name: "English", flag: "EN" }, it: { name: "Italiano", flag: "IT" },
    de: { name: "Deutsch", flag: "DE" }, fr: { name: "Français", flag: "FR" },
    es: { name: "Español", flag: "ES" }, pt: { name: "Português", flag: "PT" },
    ar: { name: "العربية", flag: "AR" }, yo: { name: "Yorùbá", flag: "YO" },
    ha: { name: "Hausa", flag: "HA" }, ig: { name: "Igbo", flag: "IG" }
  };
  const EN = {
    "API documentation":"API documentation","A clearer picture of any public repository.":"A clearer picture of any public repository.",
    "Start with repository facts, not a black-box promise. OAE gives your team an inspectable analysis and keeps the evidence with your workspace.":"Start with repository facts, not a black-box promise. OAE gives your team an inspectable analysis and keeps the evidence with your workspace.",
    "GOVERNED ENGINEERING WORKSPACE":"GOVERNED ENGINEERING WORKSPACE","Repository context":"Repository context",
    "Branch, file counts, language surface and project signals.":"Branch, file counts, language surface and project signals.",
    "Evidence that stays":"Evidence that stays","Mission status and results remain in your workspace history.":"Mission status and results remain in your workspace history.",
    "Clear boundaries":"Clear boundaries","This beta reads public repositories; it does not change them.":"This beta reads public repositories; it does not change them.",
    "Built for developers who want to understand the work before trusting the automation.":"Built for developers who want to understand the work before trusting the automation.",
    "Install OAE on this device":"Install OAE on this device","Keep your engineering workspace one tap away.":"Keep your engineering workspace one tap away.",
    "Install OAE":"Install OAE","YOUR WORKSPACE":"YOUR WORKSPACE","Create or sign in":"Create or sign in",
    "A workspace keeps your repository analyses and mission history together.":"A workspace keeps your repository analyses and mission history together.",
    "Workspace name":"Workspace name","Create workspace":"Create workspace","Your API key will be shown once. You can use it to sign in again.":"Your API key will be shown once. You can use it to sign in again.",
    "Already have a workspace?":"Already have a workspace?","Sign in with API key":"Sign in with API key","Open workspace":"Open workspace",
    "Your key stays in this browser on this device. Never share it publicly.":"Your key stays in this browser on this device. Never share it publicly.",
    "OAE · Controlled beta":"OAE · Controlled beta","Read-only repository analysis":"Read-only repository analysis",
    "ENGINEERING WORKSPACE":"ENGINEERING WORKSPACE","API docs":"API docs","Checking connection":"Checking connection","Sign out":"Sign out",
    "WORKSPACE NAVIGATION":"WORKSPACE NAVIGATION","Overview":"Overview","Missions":"Missions","Analyzed repositories":"Analyzed repositories",
    "ABOUT OAE":"ABOUT OAE","What OAE checks":"What OAE checks","Security & limits":"Security & limits",
    "Human authority stays":"Human authority stays","OAE analyzes and records. This beta does not publish repository changes.":"OAE analyzes and records. This beta does not publish repository changes.",
    "Controlled beta":"Controlled beta","WORKSPACE":"WORKSPACE","Repository intelligence, with receipts.":"Repository intelligence, with receipts.",
    "Analyze a public GitHub repository and keep the result close to the work.":"Analyze a public GitHub repository and keep the result close to the work.",
    "CONTROLLED BETA":"CONTROLLED BETA","Completed":"Completed","Repositories analyzed":"Repositories analyzed","Repository changes":"Repository changes",
    "Not enabled":"Not enabled","FIRST MISSION":"FIRST MISSION","Start with a repository you can inspect.":"Start with a repository you can inspect.",
    "OAE reads public GitHub metadata and returns a saved, evidence-backed snapshot. Your repository is not modified.":"OAE reads public GitHub metadata and returns a saved, evidence-backed snapshot. Your repository is not modified.",
    "Public GitHub repository URL":"Public GitHub repository URL","Analyze repository":"Analyze repository","Public repositories only":"Public repositories only",
    "WORKSPACE HISTORY":"WORKSPACE HISTORY","Latest mission":"Latest mission","No missions yet":"No missions yet",
    "No repository selected":"No repository selected","Governed control plane":"Governed control plane","Ready":"Ready",
    "New engineering session":"New engineering session","RECENT SESSIONS":"RECENT SESSIONS",
    "What do you want me to build?":"What do you want me to build?","Describe the engineering objective. Add a screenshot, document, voice note, or screen recording when words are not enough.":"Describe the engineering objective. Add a screenshot, document, voice note, or screen recording when words are not enough.",
    "Fix a bug":"Fix a bug","Build a feature":"Build a feature","Review security":"Review security","Implement a specification":"Implement a specification",
    "MODE":"MODE","REPOSITORY":"REPOSITORY","WORKSPACE":"WORKSPACE","Current / none":"Current / none",
    "Describe an engineering task...":"Describe an engineering task...","Send":"Send","Voice input":"Voice input",
    "Ask is read-only. Plan prepares. Execute requires an active governed authorization.":"Ask is read-only. Plan prepares. Execute requires an active governed authorization.",
    "English":"English"
  };
  const TRANSLATIONS = {
    it: {
      "API documentation":"Documentazione API","A clearer picture of any public repository.":"Una visione più chiara di qualsiasi repository pubblico.",
      "GOVERNED ENGINEERING WORKSPACE":"AMBIENTE DI INGEGNERIA GOVERNATO","Repository context":"Contesto del repository",
      "Branch, file counts, language surface and project signals.":"Branch, numero di file, linguaggi e indicatori del progetto.",
      "Evidence that stays":"Prove che restano","Mission status and results remain in your workspace history.":"Lo stato delle attività e i risultati restano nella cronologia dell'area di lavoro.",
      "Clear boundaries":"Limiti chiari","This beta reads public repositories; it does not change them.":"Questa beta legge repository pubblici, senza modificarli.",
      "Install OAE on this device":"Installa OAE su questo dispositivo","Keep your engineering workspace one tap away.":"Accedi al tuo spazio di lavoro con un solo tocco.",
      "Install OAE":"Installa OAE","YOUR WORKSPACE":"IL TUO SPAZIO DI LAVORO","Create or sign in":"Crea un account o accedi",
      "A workspace keeps your repository analyses and mission history together.":"Uno spazio di lavoro riunisce analisi dei repository e cronologia delle attività.",
      "Workspace name":"Nome dello spazio di lavoro","Create workspace":"Crea spazio di lavoro","Already have a workspace?":"Hai già uno spazio di lavoro?",
      "Sign in with API key":"Accedi con chiave API","Open workspace":"Apri spazio di lavoro","Overview":"Panoramica","Missions":"Attività",
      "Analyzed repositories":"Repository analizzati","ABOUT OAE":"INFORMAZIONI SU OAE","What OAE checks":"Cosa controlla OAE",
      "Security & limits":"Sicurezza e limiti","Human authority stays":"Il controllo resta umano","Controlled beta":"Beta controllata",
      "Repository intelligence, with receipts.":"Intelligenza sui repository, con prove.","Analyze a public GitHub repository and keep the result close to the work.":"Analizza un repository GitHub pubblico e conserva i risultati con il progetto.",
      "Completed":"Completate","Repositories analyzed":"Repository analizzati","Repository changes":"Modifiche al repository","Not enabled":"Non abilitate",
      "FIRST MISSION":"PRIMA ATTIVITÀ","Start with a repository you can inspect.":"Inizia con un repository che puoi ispezionare.",
      "Public GitHub repository URL":"URL del repository GitHub pubblico","Analyze repository":"Analizza repository","Public repositories only":"Solo repository pubblici",
      "Latest mission":"Ultima attività","No missions yet":"Nessuna attività","New engineering session":"Nuova sessione tecnica",
      "RECENT SESSIONS":"SESSIONI RECENTI","What do you want me to build?":"Che cosa vuoi che realizzi?",
      "Fix a bug":"Correggi un bug","Build a feature":"Crea una funzionalità","Review security":"Verifica la sicurezza",
      "Implement a specification":"Implementa una specifica","MODE":"MODALITÀ","REPOSITORY":"REPOSITORY",
      "Describe an engineering task...":"Descrivi un'attività tecnica...","Send":"Invia","Voice input":"Input vocale"
    },
    de: {
      "API documentation":"API-Dokumentation","A clearer picture of any public repository.":"Ein klareres Bild jedes öffentlichen Repositorys.",
      "GOVERNED ENGINEERING WORKSPACE":"KONTROLLIERTER ENGINEERING-ARBEITSBEREICH","Repository context":"Repository-Kontext",
      "Branch, file counts, language surface and project signals.":"Branch, Dateianzahl, Sprachen und Projektsignale.",
      "Evidence that stays":"Nachvollziehbare Belege","Mission status and results remain in your workspace history.":"Aufgabenstatus und Ergebnisse bleiben im Arbeitsbereich gespeichert.",
      "Clear boundaries":"Klare Grenzen","This beta reads public repositories; it does not change them.":"Diese Beta liest öffentliche Repositorys, verändert sie aber nicht.",
      "Install OAE on this device":"OAE auf diesem Gerät installieren","Keep your engineering workspace one tap away.":"Dein Engineering-Arbeitsbereich ist nur einen Tipp entfernt.",
      "Install OAE":"OAE installieren","YOUR WORKSPACE":"DEIN ARBEITSBEREICH","Create or sign in":"Arbeitsbereich erstellen oder anmelden",
      "A workspace keeps your repository analyses and mission history together.":"Ein Arbeitsbereich bündelt Repository-Analysen und Aufgabenverlauf.",
      "Workspace name":"Name des Arbeitsbereichs","Create workspace":"Arbeitsbereich erstellen","Already have a workspace?":"Du hast bereits einen Arbeitsbereich?",
      "Sign in with API key":"Mit API-Schlüssel anmelden","Open workspace":"Arbeitsbereich öffnen","Overview":"Übersicht","Missions":"Aufgaben",
      "Analyzed repositories":"Analysierte Repositorys","ABOUT OAE":"ÜBER OAE","What OAE checks":"Was OAE prüft",
      "Security & limits":"Sicherheit und Grenzen","Human authority stays":"Menschen behalten die Kontrolle","Controlled beta":"Kontrollierte Beta",
      "Repository intelligence, with receipts.":"Repository-Intelligenz mit Nachweisen.","Analyze a public GitHub repository and keep the result close to the work.":"Analysiere ein öffentliches GitHub-Repository und bewahre die Ergebnisse direkt beim Projekt auf.",
      "Completed":"Abgeschlossen","Repositories analyzed":"Analysierte Repositorys","Repository changes":"Repository-Änderungen","Not enabled":"Nicht aktiviert",
      "FIRST MISSION":"ERSTE AUFGABE","Start with a repository you can inspect.":"Beginne mit einem Repository, das du prüfen kannst.",
      "Public GitHub repository URL":"URL eines öffentlichen GitHub-Repositorys","Analyze repository":"Repository analysieren","Public repositories only":"Nur öffentliche Repositorys",
      "Latest mission":"Letzte Aufgabe","No missions yet":"Noch keine Aufgaben","New engineering session":"Neue Engineering-Sitzung",
      "RECENT SESSIONS":"LETZTE SITZUNGEN","What do you want me to build?":"Was soll ich für dich bauen?",
      "Fix a bug":"Fehler beheben","Build a feature":"Funktion entwickeln","Review security":"Sicherheit prüfen",
      "Implement a specification":"Spezifikation umsetzen","MODE":"MODUS","REPOSITORY":"REPOSITORY",
      "Describe an engineering task...":"Beschreibe eine technische Aufgabe...","Send":"Senden","Voice input":"Spracheingabe"
    },
    fr: {
      "API documentation":"Documentation API","A clearer picture of any public repository.":"Une vision plus claire de tout dépôt public.",
      "GOVERNED ENGINEERING WORKSPACE":"ESPACE D’INGÉNIERIE GOUVERNÉ","Repository context":"Contexte du dépôt",
      "Branch, file counts, language surface and project signals.":"Branche, nombre de fichiers, langages et indicateurs du projet.",
      "Evidence that stays":"Des preuves conservées","Mission status and results remain in your workspace history.":"L’état des tâches et les résultats restent dans l’historique de l’espace de travail.",
      "Clear boundaries":"Des limites claires","This beta reads public repositories; it does not change them.":"Cette bêta lit les dépôts publics sans les modifier.",
      "Install OAE on this device":"Installer OAE sur cet appareil","Keep your engineering workspace one tap away.":"Accédez à votre espace d’ingénierie en un seul geste.",
      "Install OAE":"Installer OAE","YOUR WORKSPACE":"VOTRE ESPACE DE TRAVAIL","Create or sign in":"Créer un espace ou se connecter",
      "A workspace keeps your repository analyses and mission history together.":"Un espace regroupe les analyses de dépôts et l’historique des tâches.",
      "Workspace name":"Nom de l’espace","Create workspace":"Créer l’espace","Already have a workspace?":"Vous avez déjà un espace ?",
      "Sign in with API key":"Se connecter avec une clé API","Open workspace":"Ouvrir l’espace","Overview":"Vue d’ensemble","Missions":"Missions",
      "Analyzed repositories":"Dépôts analysés","ABOUT OAE":"À PROPOS D’OAE","What OAE checks":"Ce que vérifie OAE",
      "Security & limits":"Sécurité et limites","Human authority stays":"Le contrôle reste humain","Controlled beta":"Bêta contrôlée",
      "Repository intelligence, with receipts.":"L’intelligence des dépôts, avec des preuves.","Analyze a public GitHub repository and keep the result close to the work.":"Analysez un dépôt GitHub public et conservez les résultats avec le projet.",
      "Completed":"Terminées","Repositories analyzed":"Dépôts analysés","Repository changes":"Modifications du dépôt","Not enabled":"Désactivées",
      "FIRST MISSION":"PREMIÈRE MISSION","Start with a repository you can inspect.":"Commencez par un dépôt que vous pouvez inspecter.",
      "Public GitHub repository URL":"URL d’un dépôt GitHub public","Analyze repository":"Analyser le dépôt","Public repositories only":"Dépôts publics uniquement",
      "Latest mission":"Dernière mission","No missions yet":"Aucune mission","New engineering session":"Nouvelle session d’ingénierie",
      "RECENT SESSIONS":"SESSIONS RÉCENTES","What do you want me to build?":"Que voulez-vous que je construise ?",
      "Fix a bug":"Corriger un bug","Build a feature":"Créer une fonctionnalité","Review security":"Vérifier la sécurité",
      "Implement a specification":"Implémenter une spécification","MODE":"MODE","REPOSITORY":"DÉPÔT",
      "Describe an engineering task...":"Décrivez une tâche d’ingénierie...","Send":"Envoyer","Voice input":"Saisie vocale"
    },
    es: {
      "API documentation":"Documentación de la API","A clearer picture of any public repository.":"Una visión más clara de cualquier repositorio público.",
      "GOVERNED ENGINEERING WORKSPACE":"ESPACIO DE INGENIERÍA CONTROLADO","Repository context":"Contexto del repositorio",
      "Branch, file counts, language surface and project signals.":"Rama, cantidad de archivos, lenguajes e indicadores del proyecto.",
      "Evidence that stays":"Evidencia que permanece","Mission status and results remain in your workspace history.":"El estado de las tareas y sus resultados permanecen en el historial del espacio.",
      "Clear boundaries":"Límites claros","This beta reads public repositories; it does not change them.":"Esta beta lee repositorios públicos, pero no los modifica.",
      "Install OAE on this device":"Instalar OAE en este dispositivo","Keep your engineering workspace one tap away.":"Accede a tu espacio de ingeniería con un solo toque.",
      "Install OAE":"Instalar OAE","YOUR WORKSPACE":"TU ESPACIO DE TRABAJO","Create or sign in":"Crear espacio o iniciar sesión",
      "A workspace keeps your repository analyses and mission history together.":"Un espacio reúne los análisis de repositorios y el historial de tareas.",
      "Workspace name":"Nombre del espacio","Create workspace":"Crear espacio","Already have a workspace?":"¿Ya tienes un espacio?",
      "Sign in with API key":"Entrar con clave API","Open workspace":"Abrir espacio","Overview":"Resumen","Missions":"Tareas",
      "Analyzed repositories":"Repositorios analizados","ABOUT OAE":"ACERCA DE OAE","What OAE checks":"Qué comprueba OAE",
      "Security & limits":"Seguridad y límites","Human authority stays":"Las personas mantienen el control","Controlled beta":"Beta controlada",
      "Repository intelligence, with receipts.":"Inteligencia de repositorios con pruebas.","Analyze a public GitHub repository and keep the result close to the work.":"Analiza un repositorio público de GitHub y guarda los resultados junto al trabajo.",
      "Completed":"Completadas","Repositories analyzed":"Repositorios analizados","Repository changes":"Cambios en el repositorio","Not enabled":"No habilitados",
      "FIRST MISSION":"PRIMERA TAREA","Start with a repository you can inspect.":"Empieza con un repositorio que puedas inspeccionar.",
      "Public GitHub repository URL":"URL de repositorio público de GitHub","Analyze repository":"Analizar repositorio","Public repositories only":"Solo repositorios públicos",
      "Latest mission":"Última tarea","No missions yet":"Aún no hay tareas","New engineering session":"Nueva sesión de ingeniería",
      "RECENT SESSIONS":"SESIONES RECIENTES","What do you want me to build?":"¿Qué quieres que construya?",
      "Fix a bug":"Corregir un error","Build a feature":"Crear una función","Review security":"Revisar seguridad",
      "Implement a specification":"Implementar una especificación","MODE":"MODO","REPOSITORY":"REPOSITORIO",
      "Describe an engineering task...":"Describe una tarea de ingeniería...","Send":"Enviar","Voice input":"Entrada de voz"
    },
    pt: {
      "API documentation":"Documentação da API","A clearer picture of any public repository.":"Uma visão mais clara de qualquer repositório público.",
      "GOVERNED ENGINEERING WORKSPACE":"ESPAÇO DE ENGENHARIA GOVERNADO","Repository context":"Contexto do repositório",
      "Branch, file counts, language surface and project signals.":"Branch, quantidade de arquivos, linguagens e sinais do projeto.",
      "Evidence that stays":"Evidências preservadas","Mission status and results remain in your workspace history.":"O estado das tarefas e os resultados ficam no histórico do espaço de trabalho.",
      "Clear boundaries":"Limites claros","This beta reads public repositories; it does not change them.":"Esta versão beta lê repositórios públicos, mas não os altera.",
      "Install OAE on this device":"Instalar OAE neste dispositivo","Keep your engineering workspace one tap away.":"Acesse seu espaço de engenharia com um toque.",
      "Install OAE":"Instalar OAE","YOUR WORKSPACE":"SEU ESPAÇO DE TRABALHO","Create or sign in":"Criar espaço ou entrar",
      "A workspace keeps your repository analyses and mission history together.":"Um espaço reúne as análises dos repositórios e o histórico de tarefas.",
      "Workspace name":"Nome do espaço","Create workspace":"Criar espaço","Already have a workspace?":"Já tem um espaço?",
      "Sign in with API key":"Entrar com chave de API","Open workspace":"Abrir espaço","Overview":"Visão geral","Missions":"Tarefas",
      "Analyzed repositories":"Repositórios analisados","ABOUT OAE":"SOBRE OAE","What OAE checks":"O que o OAE verifica",
      "Security & limits":"Segurança e limites","Human authority stays":"O controlo permanece humano","Controlled beta":"Beta controlada",
      "Repository intelligence, with receipts.":"Inteligência de repositórios com evidências.","Analyze a public GitHub repository and keep the result close to the work.":"Analise um repositório público do GitHub e mantenha os resultados junto ao trabalho.",
      "Completed":"Concluídas","Repositories analyzed":"Repositórios analisados","Repository changes":"Alterações no repositório","Not enabled":"Não ativadas",
      "FIRST MISSION":"PRIMEIRA TAREFA","Start with a repository you can inspect.":"Comece por um repositório que possa inspecionar.",
      "Public GitHub repository URL":"URL de repositório público do GitHub","Analyze repository":"Analisar repositório","Public repositories only":"Apenas repositórios públicos",
      "Latest mission":"Tarefa mais recente","No missions yet":"Ainda não há tarefas","New engineering session":"Nova sessão de engenharia",
      "RECENT SESSIONS":"SESSÕES RECENTES","What do you want me to build?":"O que você quer que eu construa?",
      "Fix a bug":"Corrigir um erro","Build a feature":"Criar uma funcionalidade","Review security":"Revisar segurança",
      "Implement a specification":"Implementar uma especificação","MODE":"MODO","REPOSITORY":"REPOSITÓRIO",
      "Describe an engineering task...":"Descreva uma tarefa de engenharia...","Send":"Enviar","Voice input":"Entrada de voz"
    },
    ar: {
      "API documentation":"توثيق واجهة API","A clearer picture of any public repository.":"صورة أوضح لأي مستودع عام.",
      "GOVERNED ENGINEERING WORKSPACE":"مساحة هندسية خاضعة للحوكمة","Repository context":"سياق المستودع",
      "Branch, file counts, language surface and project signals.":"الفرع وعدد الملفات واللغات ومؤشرات المشروع.",
      "Evidence that stays":"أدلة محفوظة","Mission status and results remain in your workspace history.":"تبقى حالة المهام ونتائجها في سجل مساحة العمل.",
      "Clear boundaries":"حدود واضحة","This beta reads public repositories; it does not change them.":"تقرأ هذه النسخة التجريبية المستودعات العامة ولا تعدّلها.",
      "Install OAE on this device":"تثبيت OAE على هذا الجهاز","Keep your engineering workspace one tap away.":"افتح مساحة العمل الهندسية بلمسة واحدة.",
      "Install OAE":"تثبيت OAE","YOUR WORKSPACE":"مساحة العمل الخاصة بك","Create or sign in":"إنشاء مساحة أو تسجيل الدخول",
      "A workspace keeps your repository analyses and mission history together.":"تجمع مساحة العمل تحليلات المستودعات وسجل المهام.",
      "Workspace name":"اسم مساحة العمل","Create workspace":"إنشاء مساحة عمل","Already have a workspace?":"هل لديك مساحة عمل بالفعل؟",
      "Sign in with API key":"تسجيل الدخول بمفتاح API","Open workspace":"فتح مساحة العمل","Overview":"نظرة عامة","Missions":"المهام",
      "Analyzed repositories":"المستودعات التي تم تحليلها","ABOUT OAE":"حول OAE","What OAE checks":"ما الذي يفحصه OAE",
      "Security & limits":"الأمان والحدود","Human authority stays":"يبقى التحكم بيد الإنسان","Controlled beta":"نسخة تجريبية خاضعة للرقابة",
      "Repository intelligence, with receipts.":"ذكاء المستودعات مع أدلة واضحة.","Analyze a public GitHub repository and keep the result close to the work.":"حلّل مستودع GitHub عامًا واحتفظ بالنتائج مع العمل.",
      "Completed":"مكتمل","Repositories analyzed":"المستودعات التي تم تحليلها","Repository changes":"تغييرات المستودع","Not enabled":"غير مفعّل",
      "FIRST MISSION":"المهمة الأولى","Start with a repository you can inspect.":"ابدأ بمستودع يمكنك فحصه.",
      "Public GitHub repository URL":"رابط مستودع GitHub عام","Analyze repository":"تحليل المستودع","Public repositories only":"المستودعات العامة فقط",
      "Latest mission":"أحدث مهمة","No missions yet":"لا توجد مهام بعد","New engineering session":"جلسة هندسية جديدة",
      "RECENT SESSIONS":"الجلسات الأخيرة","What do you want me to build?":"ما الذي تريد مني بناءه؟",
      "Fix a bug":"إصلاح خطأ","Build a feature":"إنشاء ميزة","Review security":"مراجعة الأمان",
      "Implement a specification":"تنفيذ مواصفات","MODE":"الوضع","REPOSITORY":"المستودع",
      "Describe an engineering task...":"صف المهمة الهندسية...","Send":"إرسال","Voice input":"إدخال صوتي"
    },
    yo: {
      "API documentation":"Ìwé ìtọ́sọ́nà API","A clearer picture of any public repository.":"Àwòrán tó ṣe kedere sí i ti repository gbogbo ènìyàn.",
      "GOVERNED ENGINEERING WORKSPACE":"ÀYÈ IṢẸ́ Ẹ̀rọ TÍ A Ń ṢÀKÓṢO","Repository context":"Àlàyé repository",
      "Branch, file counts, language surface and project signals.":"Ẹ̀ka, iye fáìlì, èdè àti àmì iṣẹ́ náà.",
      "Evidence that stays":"Ẹ̀rí tó wà níbẹ̀","Mission status and results remain in your workspace history.":"Ipò iṣẹ́ àti àbájáde yóò wà nínú ìtàn àyè iṣẹ́ rẹ.",
      "Clear boundaries":"Ààlà tó ṣe kedere","This beta reads public repositories; it does not change them.":"Ẹ̀dà beta yìí ń ka repository gbogbogbo, kò sì yí wọn padà.",
      "Install OAE on this device":"Fi OAE sí ẹ̀rọ yìí","Keep your engineering workspace one tap away.":"Wọlé sí àyè iṣẹ́ rẹ pẹ̀lú ìfọwọ́kan kan.",
      "Install OAE":"Fi OAE sílẹ̀","YOUR WORKSPACE":"ÀYÈ IṢẸ́ RẸ","Create or sign in":"Ṣẹ̀dá àyè tàbí wọlé",
      "A workspace keeps your repository analyses and mission history together.":"Àyè iṣẹ́ kan ń pa àyẹ̀wò repository àti ìtàn iṣẹ́ mọ́ pọ̀.",
      "Workspace name":"Orúkọ àyè iṣẹ́","Create workspace":"Ṣẹ̀dá àyè iṣẹ́","Already have a workspace?":"Ṣé o ti ní àyè iṣẹ́ tẹ́lẹ̀?",
      "Sign in with API key":"Wọlé pẹ̀lú kọ́kọ́rọ́ API","Open workspace":"Ṣí àyè iṣẹ́","Overview":"Àkótán","Missions":"Àwọn iṣẹ́",
      "Analyzed repositories":"Àwọn repository tí a ṣàyẹ̀wò","ABOUT OAE":"Nípa OAE","What OAE checks":"Ohun tí OAE ń ṣàyẹ̀wò",
      "Security & limits":"Ààbò àti ààlà","Human authority stays":"Ènìyàn ṣì ní àṣẹ","Controlled beta":"Beta tí a ń ṣàkóso",
      "Repository intelligence, with receipts.":"Ọgbọ́n repository pẹ̀lú ẹ̀rí.","Analyze a public GitHub repository and keep the result close to the work.":"Ṣàyẹ̀wò repository GitHub gbogbogbo kí o sì pa àbájáde mọ́ pẹ̀lú iṣẹ́ náà.",
      "Completed":"Ti parí","Repositories analyzed":"Àwọn repository tí a ṣàyẹ̀wò","Repository changes":"Àwọn àyípadà repository","Not enabled":"A kò tíì ṣiṣẹ́",
      "FIRST MISSION":"IṢẸ́ ÀKỌ́KỌ́","Start with a repository you can inspect.":"Bẹ̀rẹ̀ pẹ̀lú repository tí o lè ṣàyẹ̀wò.",
      "Public GitHub repository URL":"URL repository GitHub gbogbogbo","Analyze repository":"Ṣàyẹ̀wò repository","Public repositories only":"Repository gbogbogbo nìkan",
      "Latest mission":"Iṣẹ́ tuntun jù","No missions yet":"Kò sí iṣẹ́ kankan síbẹ̀","New engineering session":"Ìpàdé iṣẹ́ ẹ̀rọ tuntun",
      "RECENT SESSIONS":"ÀWỌN ÌPÀDÉ TUNTUN","What do you want me to build?":"Kí ni o fẹ́ kí n kọ́?",
      "Fix a bug":"Ṣàtúnṣe àṣìṣe","Build a feature":"Kọ́ ẹ̀yà tuntun","Review security":"Ṣàyẹ̀wò ààbò",
      "Implement a specification":"Mú ìlànà ṣiṣẹ́","MODE":"Ọ̀NÀ","REPOSITORY":"REPOSITORY",
      "Describe an engineering task...":"Ṣàlàyé iṣẹ́ ẹ̀rọ kan...","Send":"Fi ránṣẹ́","Voice input":"Ìwọlé ohùn"
    },
    ha: {
      "API documentation":"Takardun API","A clearer picture of any public repository.":"Bayyanannen hoto na kowane ma'ajiyar lamba ta jama'a.",
      "GOVERNED ENGINEERING WORKSPACE":"WURIN AIKIN INJINIYA MAI TSARIN MULKI","Repository context":"Bayanin ma'ajiyar lamba",
      "Branch, file counts, language surface and project signals.":"Reshe, yawan fayiloli, harsuna da alamun aikin.",
      "Evidence that stays":"Shaida da ke nan","Mission status and results remain in your workspace history.":"Matsayin ayyuka da sakamakonsu suna nan a tarihin wurin aikinka.",
      "Clear boundaries":"Iyakoki bayyanannu","This beta reads public repositories; it does not change them.":"Wannan beta tana karanta ma'ajiyoyin jama'a amma ba ta canza su.",
      "Install OAE on this device":"Sanya OAE a wannan na'urar","Keep your engineering workspace one tap away.":"Ka buɗe wurin aikinka da taɓawa ɗaya.",
      "Install OAE":"Sanya OAE","YOUR WORKSPACE":"WURIN AIKINKA","Create or sign in":"Ƙirƙiri wuri ko shiga",
      "A workspace keeps your repository analyses and mission history together.":"Wurin aiki yana haɗa nazarin ma'ajiyar lamba da tarihin ayyuka.",
      "Workspace name":"Sunan wurin aiki","Create workspace":"Ƙirƙiri wurin aiki","Already have a workspace?":"Kana da wurin aiki tuni?",
      "Sign in with API key":"Shiga da maɓallin API","Open workspace":"Buɗe wurin aiki","Overview":"Taƙaitaccen bayani","Missions":"Ayyuka",
      "Analyzed repositories":"Ma'ajiyoyin da aka bincika","ABOUT OAE":"GAME DA OAE","What OAE checks":"Abin da OAE ke dubawa",
      "Security & limits":"Tsaro da iyakoki","Human authority stays":"Mutum ne ke da iko","Controlled beta":"Beta mai kulawa",
      "Repository intelligence, with receipts.":"Fahimtar ma'ajiyar lamba tare da shaida.","Analyze a public GitHub repository and keep the result close to the work.":"Bincika ma'ajiyar GitHub ta jama'a ka adana sakamakon tare da aikin.",
      "Completed":"An kammala","Repositories analyzed":"Ma'ajiyoyin da aka bincika","Repository changes":"Canje-canjen ma'ajiyar lamba","Not enabled":"Ba a kunna ba",
      "FIRST MISSION":"AIKI NA FARKO","Start with a repository you can inspect.":"Fara da ma'ajiyar lamba da za ka iya dubawa.",
      "Public GitHub repository URL":"Adireshin ma'ajiyar GitHub ta jama'a","Analyze repository":"Bincika ma'ajiyar lamba","Public repositories only":"Ma'ajiyoyin jama'a kawai",
      "Latest mission":"Aiki na baya-bayan nan","No missions yet":"Babu ayyuka tukuna","New engineering session":"Sabon zaman injiniya",
      "RECENT SESSIONS":"ZAMUNAN KWANAN NAN","What do you want me to build?":"Me kake so in gina?",
      "Fix a bug":"Gyara kuskure","Build a feature":"Gina sabon fasali","Review security":"Duba tsaro",
      "Implement a specification":"Aiwatar da ƙayyadaddun tsari","MODE":"YANAYI","REPOSITORY":"MA'AJIYAR LAMBA",
      "Describe an engineering task...":"Bayyana aikin injiniya...","Send":"Aika","Voice input":"Shigar da murya"
    },
    ig: {
      "API documentation":"Akwụkwọ ntuziaka API","A clearer picture of any public repository.":"Foto doro anya karịa nke ebe nchekwa ọha ọ bụla.",
      "GOVERNED ENGINEERING WORKSPACE":"OGE ỌRỤ INJINIA A NA-AHỤ NA YA","Repository context":"Ozi ebe nchekwa",
      "Branch, file counts, language surface and project signals.":"Alaka, ọnụọgụ faịlụ, asụsụ na akara ọrụ.",
      "Evidence that stays":"Ihe akaebe na-adịgide","Mission status and results remain in your workspace history.":"Ọnọdụ ọrụ na nsonaazụ ya na-adị n'akụkọ ebe ọrụ gị.",
      "Clear boundaries":"Oke doro anya","This beta reads public repositories; it does not change them.":"Beta a na-agụ ebe nchekwa ọha; ọ naghị agbanwe ha.",
      "Install OAE on this device":"Wụnye OAE na ngwaọrụ a","Keep your engineering workspace one tap away.":"Jiri otu mmetụ mepee ebe ọrụ injinia gị.",
      "Install OAE":"Wụnye OAE","YOUR WORKSPACE":"EBE ỌRỤ GỊ","Create or sign in":"Mepụta ebe ọrụ ma ọ bụ banye",
      "A workspace keeps your repository analyses and mission history together.":"Ebe ọrụ na-ejikọta nyocha ebe nchekwa na akụkọ ọrụ.",
      "Workspace name":"Aha ebe ọrụ","Create workspace":"Mepụta ebe ọrụ","Already have a workspace?":"Ị nwere ebe ọrụ ugbu a?",
      "Sign in with API key":"Jiri igodo API banye","Open workspace":"Mepee ebe ọrụ","Overview":"Nchịkọta","Missions":"Ọrụ",
      "Analyzed repositories":"Ebe nchekwa e nyochara","ABOUT OAE":"GBASARA OAE","What OAE checks":"Ihe OAE na-enyocha",
      "Security & limits":"Nchekwa na oke","Human authority stays":"Mmadụ ka na-achịkwa","Controlled beta":"Beta a na-achịkwa",
      "Repository intelligence, with receipts.":"Amamihe ebe nchekwa nwere ihe akaebe.","Analyze a public GitHub repository and keep the result close to the work.":"Nyochaa ebe nchekwa GitHub ọha ma debe nsonaazụ ya n'akụkụ ọrụ ahụ.",
      "Completed":"Emechara","Repositories analyzed":"Ebe nchekwa e nyochara","Repository changes":"Mgbanwe ebe nchekwa","Not enabled":"Emeghị ka ọ rụọ ọrụ",
      "FIRST MISSION":"ỌRỤ MBỤ","Start with a repository you can inspect.":"Malite na ebe nchekwa ị nwere ike nyochaa.",
      "Public GitHub repository URL":"URL ebe nchekwa GitHub ọha","Analyze repository":"Nyochaa ebe nchekwa","Public repositories only":"Ebe nchekwa ọha naanị",
      "Latest mission":"Ọrụ kacha ọhụrụ","No missions yet":"Enweghị ọrụ ugbu a","New engineering session":"Oge ọrụ injinia ọhụrụ",
      "RECENT SESSIONS":"OGE ỌRỤ ỌHỤRỤ","What do you want me to build?":"Kedu ihe ị chọrọ ka m wuo?",
      "Fix a bug":"Dozie njehie","Build a feature":"Wuo atụmatụ ọhụrụ","Review security":"Nyochaa nchekwa",
      "Implement a specification":"Mejuputa nkọwa ọrụ","MODE":"ỤDỊ","REPOSITORY":"EBE NCHEKWA",
      "Describe an engineering task...":"Kọwaa ọrụ injinia...","Send":"Zipu","Voice input":"Ntinye olu"
    }
  };
  function getLanguage() {
    try {
      const saved = localStorage.getItem(KEY);
      if (Object.prototype.hasOwnProperty.call(SUPPORTED, saved)) return saved;
    } catch {}
    const browser = (navigator.language || "en").toLowerCase();
    return Object.keys(SUPPORTED).find(code => browser.startsWith(code)) || "en";
  }
  function t(value, language = getLanguage()) {
    const source = String(value ?? "").trim();
    return TRANSLATIONS[language]?.[source] || EN[source] || source;
  }
  function apply(root = document) {
    const language = getLanguage();
    root.querySelectorAll("[data-i18n]").forEach(el => {
      const source = el.dataset.i18n;
      if (el.dataset.i18nAttr) el.setAttribute(el.dataset.i18nAttr, t(source, language));
      else el.textContent = t(source, language);
    });
    root.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      el.placeholder = t(el.dataset.i18nPlaceholder, language);
    });
    root.querySelectorAll("[data-oae-language]").forEach(el => { el.value = language; });
    document.documentElement.lang = language;
    document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
  }
  function setLanguage(language) {
    if (!Object.prototype.hasOwnProperty.call(SUPPORTED, language)) return;
    try { localStorage.setItem(KEY, language); } catch {}
    apply();
    window.dispatchEvent(new CustomEvent("oae:language", { detail: { language } }));
  }
  function selector(id = "oae-language") {
    const select = document.createElement("select");
    select.id = id;
    select.className = "oae-language-select";
    select.setAttribute("aria-label", "Language");
    select.dataset.oaeLanguage = "1";
    Object.entries(SUPPORTED).forEach(([code, item]) => {
      const option = document.createElement("option");
      option.value = code;
      option.textContent = item.name;
      select.appendChild(option);
    });
    select.value = getLanguage();
    select.addEventListener("change", () => setLanguage(select.value));
    return select;
  }
  window.OAEI18n = { SUPPORTED, getLanguage, t, apply, setLanguage, selector };
  window.addEventListener("DOMContentLoaded", () => apply());
})();