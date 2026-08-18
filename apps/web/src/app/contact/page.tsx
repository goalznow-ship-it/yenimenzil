import type { Metadata } from "next";
import { Mail, Phone, MapPin } from "lucide-react";

export const metadata: Metadata = {
  title: "Əlaqə",
  description: "aidealEv.az ilə əlaqə."
};

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12 lg:px-6">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">
        Əlaqə
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Suallarınız və ya təklifləriniz üçün bizimlə əlaqə saxlayın.
      </p>
      <div className="mt-6 space-y-4">
        {[
          {
            icon: Mail,
            label: "E-poçt",
            value: "info@idealev.az"
          },
          {
            icon: Phone,
            label: "Telefon",
            value: "+994 50 000 00 00"
          },
          {
            icon: MapPin,
            label: "Ünvan",
            value: "Bakı, Azərbaycan"
          }
        ].map((item) => (
          <div
            key={item.label}
            className="flex items-center gap-3.5 rounded-2xl bg-surface px-5 py-4 ring-1 ring-border/70"
          >
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-brand">
              <item.icon className="h-5 w-5" />
            </span>
            <div>
              <p className="text-xs text-muted-foreground">{item.label}</p>
              <p className="text-sm font-medium text-foreground">
                {item.value}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
