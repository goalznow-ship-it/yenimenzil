"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button, Input } from "@yenimenzil/ui";
import { CheckCircle2, Info } from "lucide-react";
import { authApi } from "@/services/auth-api";

type Mode = "forgot" | "reset" | "verify";

export function AccountRecovery({ mode }: { mode: Mode }) {
  const params = useSearchParams();
  const token = params.get("token")?.trim() ?? "";
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [loading, setLoading] = React.useState(mode === "verify" && !!token);
  const [success, setSuccess] = React.useState(false);
  const [error, setError] = React.useState<string | null>(
    mode !== "forgot" && !token ? "Link etibarsızdır və ya token yoxdur." : null
  );

  React.useEffect(() => {
    if (mode !== "verify" || !token) return;
    let active = true;
    authApi
      .verifyEmail(token)
      .then(() => active && setSuccess(true))
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : "Təsdiqləmə alınmadı.");
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [mode, token]);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    if (mode === "reset" && password !== confirmPassword) {
      setError("Şifrələr eyni deyil.");
      return;
    }

    setLoading(true);
    try {
      if (mode === "forgot") await authApi.forgotPassword(email);
      if (mode === "reset") await authApi.resetPassword(token, password);
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta baş verdi, yenidən cəhd edin.");
    } finally {
      setLoading(false);
    }
  };

  const title =
    mode === "forgot"
      ? "Şifrəni bərpa et"
      : mode === "reset"
        ? "Yeni şifrə təyin et"
        : "E-poçtu təsdiqlə";

  return (
    <div className="mx-auto flex min-h-[65dvh] w-full max-w-md items-center px-4 py-12">
      <div className="w-full rounded-2xl bg-surface p-6 ring-1 ring-border/70 md:p-8">
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>

        {loading && mode === "verify" ? (
          <p className="mt-4 text-sm text-muted-foreground">Təsdiqlənir…</p>
        ) : success ? (
          <div className="mt-5">
            <div className="flex items-start gap-2 rounded-xl bg-emerald-500/10 p-3 text-sm text-emerald-700">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                {mode === "forgot"
                  ? "Bu e-poçtla hesab varsa, bərpa linki göndərildi."
                  : mode === "reset"
                    ? "Şifrəniz uğurla yeniləndi."
                    : "E-poçt ünvanınız təsdiqləndi."}
              </span>
            </div>
            <Button asChild className="mt-5 w-full">
              <Link href="/login">Daxil ol</Link>
            </Button>
          </div>
        ) : (
          <form className="mt-5 space-y-4" onSubmit={submit}>
            {mode === "forgot" ? (
              <div>
                <label htmlFor="recovery-email" className="mb-1.5 block text-sm font-medium">
                  E-poçt
                </label>
                <Input
                  id="recovery-email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
            ) : null}

            {mode === "reset" ? (
              <>
                <div>
                  <label htmlFor="new-password" className="mb-1.5 block text-sm font-medium">
                    Yeni şifrə
                  </label>
                  <Input
                    id="new-password"
                    type="password"
                    minLength={8}
                    maxLength={128}
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor="confirm-password" className="mb-1.5 block text-sm font-medium">
                    Şifrəni təkrarla
                  </label>
                  <Input
                    id="confirm-password"
                    type="password"
                    minLength={8}
                    maxLength={128}
                    autoComplete="new-password"
                    required
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                  />
                </div>
              </>
            ) : null}

            {error ? (
              <div role="alert" className="flex items-start gap-2 rounded-xl bg-red-500/10 p-3 text-sm text-red-600">
                <Info className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            ) : null}

            {mode !== "verify" ? (
              <Button type="submit" className="w-full" disabled={loading || (mode === "reset" && !token)}>
                {loading ? "Gözləyin…" : mode === "forgot" ? "Bərpa linki göndər" : "Şifrəni yenilə"}
              </Button>
            ) : null}
          </form>
        )}
      </div>
    </div>
  );
}
