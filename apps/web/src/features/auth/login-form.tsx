"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Input } from "@yenimenzil/ui";
import { Info, KeyRound, Mail, UserRound } from "lucide-react";
import { Logo } from "@/components/layout/logo";
import { useAuth } from "@/store/auth";
import { useI18n } from "@/components/i18n-provider";

interface FormValues {
  email: string;
  password: string;
  name?: string;
  phone?: string;
}

export function LoginForm({ mode }: { mode: "login" | "register" }) {
  const { t } = useI18n();
  const isRegister = mode === "register";
  const schema = React.useMemo(() => {
    const loginSchema = z.object({
      email: z.string().email(t("auth.invalidEmail")),
      password: z.string().min(8, t("auth.shortPassword"))
    });
    return (isRegister
      ? loginSchema.extend({
          name: z.string().min(2, t("auth.nameRequired")),
          phone: z.string().regex(/^\+994\d{9}$/, "+994XXXXXXXXX").or(z.literal(""))
        })
      : loginSchema) as z.ZodType<FormValues, FormValues>;
  }, [isRegister, t]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "", name: "", phone: "" }
  });

  const login = useAuth((s) => s.login);
  const registerAction = useAuth((s) => s.register);
  const loginError = useAuth((s) => s.loginError);
  const registerError = useAuth((s) => s.registerError);
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/";

  const [serverError, setServerError] = React.useState<string | null>(null);

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      if (isRegister) {
        await registerAction({
          email: values.email,
          password: values.password,
          full_name: values.name ?? "",
          phone: values.phone || undefined
        });
      } else {
        await login(values.email, values.password);
      }
      const safeNext = next.startsWith("/") && !next.startsWith("//") ? next : "/";
      router.push(safeNext);
    } catch (err) {
      setServerError(
        err instanceof Error ? err.message : t("auth.genericError")
      );
    }
  };

  return (
    <div className="mx-auto flex min-h-[70dvh] w-full max-w-md flex-col justify-center px-4 py-12">
      <div className="mb-8 flex justify-center">
        <Logo />
      </div>

      <div className="rounded-2xl bg-surface p-6 ring-1 ring-border/70 md:p-8">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          {isRegister ? t("auth.registerTitle") : t("auth.loginTitle")}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {isRegister
            ? t("auth.registerSubtitle")
            : t("auth.loginSubtitle")}
        </p>

        {serverError || loginError || registerError ? (
          <div className="mt-6 flex items-center gap-2 rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">
            <Info className="h-4 w-4 shrink-0" />
            {serverError || loginError || registerError}
          </div>
        ) : null}

        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
            {isRegister ? (
              <>
                <div>
                  <label
                    htmlFor="name"
                    className="mb-1.5 block text-[13px] font-medium text-foreground/75"
                  >
                    {t("auth.name")}
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
                    {t("auth.phone")} <span className="text-foreground/40">({t("auth.optional")})</span>
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
                {t("auth.email")}
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
                {t("auth.password")}
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
              {!isRegister ? (
                <div className="mt-2 text-right">
                  <Link
                    href="/forgot-password"
                    className="text-xs font-medium text-brand hover:underline"
                  >
                    {t("auth.forgot")}
                  </Link>
                </div>
              ) : null}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? t("auth.wait")
                : isRegister
                  ? t("auth.register")
                  : t("auth.login")}
            </Button>
          </form>
        </div>

      <p className="mt-5 text-center text-sm text-muted-foreground">
        {isRegister ? t("auth.haveAccount") : t("auth.noAccount")}{" "}
        <Link
          href={isRegister ? "/login" : "/register"}
          className="font-semibold text-brand hover:underline"
        >
          {isRegister ? t("auth.loginLink") : t("auth.registerLink")}
        </Link>
      </p>
    </div>
  );
}
