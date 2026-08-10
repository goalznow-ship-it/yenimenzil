"use client";

import * as React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Input } from "@yenimenzil/ui";
import { Info, KeyRound, Mail, UserRound } from "lucide-react";
import { Logo } from "@/components/layout/logo";

const loginSchema = z.object({
  email: z.string().email("Düzgün e-poçt daxil edin"),
  password: z.string().min(8, "Şifrə ən azı 8 simvol olmalıdır")
});

const registerSchema = loginSchema.extend({
  name: z.string().min(2, "Ad daxil edin"),
  phone: z
    .string()
    .regex(/^\+994\d{9}$/, "+994XXXXXXXXX formatında daxil edin")
    .or(z.literal(""))
});

interface FormValues {
  email: string;
  password: string;
  name?: string;
  phone?: string;
}

export function LoginForm({ mode }: { mode: "login" | "register" }) {
  const isRegister = mode === "register";
  const schema = (
    isRegister ? registerSchema : loginSchema
  ) as z.ZodType<FormValues, FormValues>;

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "", name: "", phone: "" }
  });

  const [submitted, setSubmitted] = React.useState(false);

  const onSubmit = () => {
    setSubmitted(true);
  };

  return (
    <div className="mx-auto flex min-h-[70dvh] w-full max-w-md flex-col justify-center px-4 py-12">
      <div className="mb-8 flex justify-center">
        <Logo />
      </div>

      <div className="rounded-2xl bg-surface p-6 ring-1 ring-border/70 md:p-8">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          {isRegister ? "Hesab yaradın" : "Daxil olun"}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {isRegister
            ? "Elan yerləşdirmək və seçilmişləri saxlamaq üçün qeydiyyatdan keçin."
            : "Hesabınıza daxil olaraq davam edin."}
        </p>

        {submitted ? (
          <div className="mt-6 rounded-xl bg-brand-soft p-4 text-sm leading-relaxed text-brand">
            <p className="font-semibold">
              {isRegister ? "Qeydiyyat üçün təşəkkürlər!" : "Giriş uğurlu olacaq!"}
            </p>
            <p className="mt-1 text-brand/80">
              Demo rejimi: autentifikasiya servisi backend ilə birlikdə
              aktivləşəcək (Phase 2). Bu vaxt elanlara baxmaq üçün{" "}
              <Link href="/search" className="font-semibold underline">
                axtarışdan
              </Link>{" "}
              istifadə edin.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
            {isRegister ? (
              <>
                <div>
                  <label
                    htmlFor="name"
                    className="mb-1.5 block text-[13px] font-medium text-foreground/75"
                  >
                    Ad və soyad
                  </label>
                  <div className="relative">
                    <UserRound className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/35" />
                    <Input
                      id="name"
                      className="pl-9"
                      placeholder="Ad Soyad"
                      aria-invalid={!!errors.name}
                      {...register("name")}
                    />
                  </div>
                  {errors.name ? (
                    <p className="mt-1 text-xs text-red-600">
                      {errors.name.message}
                    </p>
                  ) : null}
                </div>
                <div>
                  <label
                    htmlFor="phone"
                    className="mb-1.5 block text-[13px] font-medium text-foreground/75"
                  >
                    Telefon <span className="text-foreground/40">(könüllü)</span>
                  </label>
                  <div className="relative">
                    <UserRound className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/35" />
                    <Input
                      id="phone"
                      className="pl-9"
                      placeholder="+994501234567"
                      inputMode="tel"
                      aria-invalid={!!errors.phone}
                      {...register("phone")}
                    />
                  </div>
                  {errors.phone ? (
                    <p className="mt-1 text-xs text-red-600">
                      {errors.phone.message}
                    </p>
                  ) : null}
                </div>
              </>
            ) : null}

            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-[13px] font-medium text-foreground/75"
              >
                E-poçt
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/35" />
                <Input
                  id="email"
                  type="email"
                  className="pl-9"
                  placeholder="ad@example.com"
                  autoComplete="email"
                  aria-invalid={!!errors.email}
                  {...register("email")}
                />
              </div>
              {errors.email ? (
                <p className="mt-1 text-xs text-red-600">
                  {errors.email.message}
                </p>
              ) : null}
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-[13px] font-medium text-foreground/75"
              >
                Şifrə
              </label>
              <div className="relative">
                <KeyRound className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground/35" />
                <Input
                  id="password"
                  type="password"
                  className="pl-9"
                  placeholder="••••••••"
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  aria-invalid={!!errors.password}
                  {...register("password")}
                />
              </div>
              {errors.password ? (
                <p className="mt-1 text-xs text-red-600">
                  {errors.password.message}
                </p>
              ) : null}
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isRegister ? "Qeydiyyatdan keç" : "Daxil ol"}
            </Button>
          </form>
        )}

        <div className="mt-5 flex items-center gap-2 rounded-xl bg-foreground/[0.03] px-3.5 py-2.5 text-[12px] text-foreground/60">
          <Info className="h-4 w-4 shrink-0" />
          Demo rejimi — məlumatlar serverə göndərilmir.
        </div>
      </div>

      <p className="mt-5 text-center text-sm text-muted-foreground">
        {isRegister ? "Artıq hesabınız var?" : "Hesabınız yoxdur?"}{" "}
        <Link
          href={isRegister ? "/login" : "/register"}
          className="font-semibold text-brand hover:underline"
        >
          {isRegister ? "Daxil olun" : "Qeydiyyatdan keçin"}
        </Link>
      </p>
    </div>
  );
}
