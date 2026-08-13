import type { Metadata } from "next";
import { Wrench } from "lucide-react";

export const metadata: Metadata = {
  title: "Texniki işlər",
  description: "Sayt hazırda texniki işlər səbəbindən müvəqqəti olaraq bağlıdır.",
  robots: { index: false, follow: false }
};

export default function MaintenancePage() {
  return (
    <div className="flex min-h-[70dvh] flex-col items-center justify-center px-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-soft text-brand">
        <Wrench className="h-8 w-8" />
      </div>
      <h1 className="mt-6 text-2xl font-semibold tracking-tight">
        Texniki işlər gedir
      </h1>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
        Saytımızda müvəqqəti texniki işlər aparılır. Qısa zamanda yenidən
        xidmətinizdə olacağıq. Anlayışınız üçün təşəkkür edirik.
      </p>
    </div>
  );
}
