import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState } from "@yenimenzil/ui";
import { MessageCircle } from "lucide-react";

export const metadata: Metadata = {
  title: "Mesajlar",
  description: "Elanlarla bağlı mesajlarınız."
};

export default function MessagesPage() {
  return (
    <div className="mx-auto max-w-2xl px-4 py-16 lg:px-6">
      <EmptyState
        icon={<MessageCircle className="h-7 w-7" />}
        title="Mesajlarınız burada olacaq"
        description="Satıcılar və alıcılarla əlaqə mesajları burada toplanacaq. Demo rejimində messencer xidməti hələ aktiv deyil."
        action={
          <Link
            href="/search"
            className="inline-flex h-11 items-center justify-center rounded-[10px] bg-brand px-6 text-sm font-medium text-white hover:bg-brand-hover"
          >
            Elanlara bax
          </Link>
        }
      />
    </div>
  );
}
