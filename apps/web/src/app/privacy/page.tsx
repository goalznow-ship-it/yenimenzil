import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Gizlilik siyasəti",
  description: "IdealEv.az gizlilik siyasəti."
};

const SECTIONS = [
  {
    title: "Məlumat toplanması",
    body: "Platforma yalnız xidmətin işləməsi üçün zəruri olan məlumatları toplayır: hesab məlumatları, elanlar, seçilmişlər və axtarış üstünlükləri."
  },
  {
    title: "Analitika",
    body: "Axtarış, baxış və filtr hadisələri anonim şəkildə toplanır və yalnız məhsulu yaxşılaşdırmaq üçün istifadə olunur."
  },
  {
    title: "Məlumatların qorunması",
    body: "Məlumatlarınız üçüncü şəxslərə satılmır. Giriş məlumatları şifrələnir və mühafizə olunur."
  },
  {
    title: "Demo rejimi",
    body: "Platformanın demo mərhələsində heç bir şəxsi məlumat serverə göndərilmir."
  }
];

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12 lg:px-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">
        Gizlilik siyasəti
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Son yenilənmə: avqust 2026
      </p>
      <div className="mt-6 space-y-6">
        {SECTIONS.map((section) => (
          <section key={section.title}>
            <h2 className="text-base font-semibold text-foreground">
              {section.title}
            </h2>
            <p className="mt-2 text-[14.5px] leading-relaxed text-foreground/80">
              {section.body}
            </p>
          </section>
        ))}
      </div>
    </div>
  );
}
