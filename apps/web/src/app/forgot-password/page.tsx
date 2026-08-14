import type { Metadata } from "next";
import { Suspense } from "react";
import { AccountRecovery } from "@/features/auth/account-recovery";

export const metadata: Metadata = { title: "Şifrəni bərpa et" };

export default function ForgotPasswordPage() {
  return (
    <Suspense fallback={null}>
      <AccountRecovery mode="forgot" />
    </Suspense>
  );
}
