import type { Metadata } from "next";
import { LoginForm } from "@/features/auth/login-form";
import { Suspense } from "react";

export const metadata: Metadata = {
  title: "Giriş",
  description: "aidealEv.az hesabınıza daxil olun."
};

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginForm mode="login" />
    </Suspense>
  );
}