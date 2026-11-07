import { useI18n } from "@/i18n/LanguageProvider";

export function LanguageToggle() {
  const { lang, setLang } = useI18n();
  return (
    <div className="num inline-flex rounded-full border bg-panel/60 p-0.5 text-[11px] font-semibold" role="group" aria-label="Language">
      {(["vi", "en"] as const).map((l) => (
        <button key={l} aria-pressed={lang === l} onClick={() => setLang(l)}
          className={`rounded-full px-3 py-1 uppercase transition-colors ${lang === l ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}>
          {l}
        </button>
      ))}
    </div>
  );
}
