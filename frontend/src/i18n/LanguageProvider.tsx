import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { dictionaries, type Dict, type Lang } from "./dictionary";

const Ctx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: Dict }>({ lang: "vi", setLang: () => {}, t: dictionaries.vi });

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("vi");
  useEffect(() => {
    const s = localStorage.getItem("hvn-lang");
    if (s === "vi" || s === "en") setLang(s);
  }, []);
  useEffect(() => {
    localStorage.setItem("hvn-lang", lang);
    document.documentElement.lang = lang;
  }, [lang]);
  return <Ctx.Provider value={{ lang, setLang, t: dictionaries[lang] }}>{children}</Ctx.Provider>;
}
export const useI18n = () => useContext(Ctx);
