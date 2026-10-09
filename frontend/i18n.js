(() => {
  "use strict";
  const KEY = "oae.language";
  const SUPPORTED = {
    en: { name: "English", flag: "EN" },
    it: { name: "Italiano", flag: "IT" },
    de: { name: "Deutsch", flag: "DE" },
    fr: { name: "Français", flag: "FR" },
    es: { name: "Español", flag: "ES" },
    pt: { name: "Português", flag: "PT" },
    ar: { name: "العربية", flag: "AR" },
    yo: { name: "Yorùbá", flag: "YO" },
    ha: { name: "Hausa", flag: "HA" },
    ig: { name: "Igbo", flag: "IG" }
  };
  const translations = {
    it: {
      "ENGINEERING AGENT":"AGENTE DI INGEGNERIA","New engineering session":"Nuova sessione","RECENT SESSIONS":"SESSIONI RECENTI",
      "Governed control plane":"Piano di controllo governato","Ready":"Pronto","No repository selected":"Nessun repository selezionato",
      "What do you want me to build?":"Cosa vuoi che costruisca?","Fix a bug":"Correggi un bug","Build a feature":"Costruisci una funzionalità",
      "Review security":"Controlla la sicurezza","Implement a specification":"Implementa una specifica","Send":"Invia","Voice input":"Input vocale",
      "Describe an engineering task...":"Descrivi un'attività tecnica...","Opening engineering session…":"Apertura della sessione tecnica…",
      "I prepared an isolated engineering workspace. No repository has been changed.":"Ho preparato un'area di lavoro tecnica isolata. Nessun repository è stato modificato."
    },
    de: {
      "ENGINEERING AGENT":"ENGINEERING-AGENT","New engineering session":"Neue Engineering-Sitzung","RECENT SESSIONS":"LETZTE SITZUNGEN",
      "Governed control plane":"Kontrollierte Steuerungsebene","Ready":"Bereit","No repository selected":"Kein Repository ausgewählt",
      "What do you want me to build?":"Was soll ich für dich bauen?","Fix a bug":"Fehler beheben","Build a feature":"Funktion bauen",
      "Review security":"Sicherheit prüfen","Implement a specification":"Spezifikation umsetzen","Send":"Senden","Voice input":"Spracheingabe",
      "Describe an engineering task...":"Beschreibe eine technische Aufgabe...","Opening engineering session…":"Technische Sitzung wird geöffnet…",
      "I prepared an isolated engineering workspace. No repository has been changed.":"Ich habe einen isolierten technischen Arbeitsbereich vorbereitet. Kein Repository wurde geändert."
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
    return translations[language]?.[value] || value;
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