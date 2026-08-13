import type { Metadata } from "next";
import { Suspense } from "react";
import { MessagesTab } from "@/features/dashboard/messages-tab";
import { RequireAuth } from "@/components/auth/auth-provider";

export const metadata: Metadata = {
  title: "Mesajlar",
  description: "Elanlarla bağlı mesajlarınız."
};

export default function MessagesPage() {
  return (
    <RequireAuth>
      <div className="mx-auto max-w-5xl px-4 py-8 lg:px-6">
        <h1 className="text-2xl font-semibold tracking-tight">Mesajlar</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Satıcılar və alıcılarla yazışmalarınız.
        </p>
        <div className="mt-6">
          <Suspense fallback={null}>
            <MessagesTab />
          </Suspense>
        </div>
      </div>
    </RequireAuth>
  );
}
