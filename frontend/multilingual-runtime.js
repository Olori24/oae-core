(() => {
  const SOURCE = "data-oae-source";
  const exact = (value) => value && value.trim() ? value.trim() : "";
  function translateTextNode(node) {
    const parent=node.parentElement;
    if (!parent || ["SCRIPT","STYLE","CODE","PRE"].includes(parent.tagName)) return;
    const original=node.getAttribute?.(SOURCE) || exact(node.nodeValue);
    if (!original || original.length > 180) return;
    if (!node.getAttribute(SOURCE)) node.setAttribute(SOURCE, original);
    const translated=window.OAEI18n?.t(original);
    if (translated && translated !== original) node.nodeValue=node.nodeValue.replace(original, translated);
  }
  function translateTree(root=document) {
    if (!window.OAEI18n) return;
    const walker=document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes=[];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(translateTextNode);
    root.querySelectorAll?.("input,textarea").forEach(el => {
      const source=el.getAttribute("data-oae-source-placeholder") || el.placeholder;
      if (source) {
        if (!el.hasAttribute("data-oae-source-placeholder")) el.setAttribute("data-oae-source-placeholder", source);
        el.placeholder=window.OAEI18n.t(source);
      }
    });
  }
  function addLanguageSelectors() {
    if (!window.OAEI18n) return;
    const targets=[
      document.querySelector(".welcome-header"),
      document.querySelector(".app-header .header-actions"),
      document.querySelector("#oae-command-center .oae-command-header")
    ];
    targets.filter(Boolean).forEach((target,index) => {
      if (target.querySelector(".oae-runtime-language")) return;
      const select=window.OAEI18n.selector("oae-runtime-language-"+index);
      select.classList.add("oae-runtime-language");
      target.appendChild(select);
    });
  }
  const originalFetch=window.fetch;
  window.fetch=async (input,init={}) => {
    const url=typeof input==="string" ? input : input?.url || "";
    if (["/v1/ai/respond","/v1/product/brief"].some(path => url.includes(path)) && init.body && typeof init.body==="string") {
      try {
        const body=JSON.parse(init.body);
        body.language=window.OAEI18n?.getLanguage?.() || "en";
        init={...init,body:JSON.stringify(body)};
      } catch {}
    }
    return originalFetch(input,init);
  };
  const observer=new MutationObserver(() => { addLanguageSelectors(); translateTree(document); });
  window.addEventListener("oae:language", () => { addLanguageSelectors(); translateTree(document); });
  window.addEventListener("DOMContentLoaded", () => {
    addLanguageSelectors();
    translateTree(document);
    observer.observe(document.body,{subtree:true,childList:true});
  });
})();