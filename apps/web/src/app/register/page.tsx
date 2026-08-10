import type { Metadata } from "next";
import { LoginForm } from "@/features/auth/login-form";

export const metadata: Metadata = {
  title: "Qeydiyyat",
  description: "YeniMenzil.az-da yeni hesab yaradın."
};

export default function RegisterPage() {
  return <LoginForm mode="register" />;
}
