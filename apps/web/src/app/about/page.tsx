import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Haqqımızda",
  description: "IdealEv.az haqqında."
};

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12 lg:px-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">
        Haqqımızda
      </h1>
      <div className="mt-4 space-y-4 text-[14.5px] leading-relaxed text-foreground/80">
        <p>
          IdealEv.az — Azərbaycanın daşınmaz əmlak bazarı üçün müasir
          platforma. Biz inanırıq ki, ev axtarışı sadə, şəffaf və rahat
          olmalıdır.
        </p>
        <p>
          Platformamız mənzil, yeni tikililər, həyət evləri, villalar, torpaq
          sahələri, ofis və kommersiya obyektlərini bir yerdə toplayır. Al və
          kirayə elanları xəritədə kəşf edin, qiymət analizindən istifadə edin
          və qiymət tarixçəsinə baxın.
        </p>
        <p>
          Demo mərhələsində platformanın bütün funksiyaları nümunəvi
          məlumatlarla işləyir.
        </p>
      </div>
    </div>
  );
}
