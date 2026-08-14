import type { Metadata } from "next";
import { Suspense } from "react";
import { AccountRecovery } from "@/features/auth/account-recovery";

export const metadata: Metadata = { title: "E-poçtu təsdiqlə" };

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <AccountRecovery mode="verify" />
    </Suspense>
  );
}
