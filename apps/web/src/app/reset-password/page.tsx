import type { Metadata } from "next";
import { Suspense } from "react";
import { AccountRecovery } from "@/features/auth/account-recovery";

export const metadata: Metadata = { title: "Yeni şifrə" };

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <AccountRecovery mode="reset" />
    </Suspense>
  );
}
