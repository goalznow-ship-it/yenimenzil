import type { Metadata } from "next";
import { LoginForm } from "@/features/auth/login-form";
import { Suspense } from "react";

export const metadata: Metadata = {
  title: "Qeydiyyat",
  description: "YeniMenzil.az-da yeni hesab yaradın."
};

export default function RegisterPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginForm mode="register" />
    </Suspense>
  );
}