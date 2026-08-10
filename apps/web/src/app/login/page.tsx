import type { Metadata } from "next";
import { LoginForm } from "@/features/auth/login-form";

export const metadata: Metadata = {
  title: "Giriş",
  description: "YeniMenzil.az hesabınıza daxil olun."
};

export default function LoginPage() {
  return <LoginForm mode="login" />;
}
