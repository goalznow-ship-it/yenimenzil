import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "İstifadəçi razılaşması",
  description: "IdealEv.az istifadəçi razılaşması."
};

const SECTIONS = [
  {
    title: "Xidmətdən istifadə",
    body: "IdealEv.az platformasından istifadə etməklə siz bu razılaşmanın şərtlərini qəbul edirsiniz. Elan yerləşdirərkən dəqiq və həqiqi məlumat təqdim etməlisiniz."
  },
  {
    title: "Elanlar",
    body: "Elanlardakı məlumatlar satıcılar tərəfindən təqdim olunur. Platforma məlumatların tam dəqiqliyinə zəmanət vermir və yalnız əlaqə vasitəsi kimi çıxış edir."
  },
  {
    title: "Qadağan olunan fəaliyyətlər",
    body: "Saxta elanlar, müəllif hüquqları pozulmuş şəkillər, yanıltıcı qiymət məlumatları və platformanın işinə müdaxilə qadağandır."
  },
  {
    title: "Qiymət analizi",
    body: "Qiymət analizi və təxminlər yalnız məlumatlandırma məqsədi daşıyır və rəsmi qiymətləndirmə kimi qəbul edilə bilməz."
  }
];

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12 lg:px-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">
        İstifadəçi razılaşması
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
