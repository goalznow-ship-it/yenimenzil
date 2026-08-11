"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button, Input } from "@yenimenzil/ui";
import { Info, Save, ShieldCheck } from "lucide-react";
import { RequireAuth } from "@/components/auth/auth-provider";
import { authApi } from "@/services/auth-api";
import { useAuth } from "@/store/auth";

const profileSchema = z.object({
  full_name: z.string().min(2, "Ad daxil edin"),
  phone: z
    .string()
    .regex(/^\+994\d{9}$/, "+994XXXXXXXXX formatında daxil edin")
    .or(z.literal("")),
  city: z.string().max(200).optional(),
  bio: z.string().max(1000).optional()
});

type ProfileValues = z.infer<typeof profileSchema>;

export function ProfilePage() {
  const user = useAuth((s) => s.user);
  const setUser = useAuth((s) => s.setUser);
  const [saved, setSaved] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    values: {
      full_name: user?.full_name ?? "",
      phone: user?.phone ?? "",
      city: user?.profile?.city ?? "",
      bio: user?.profile?.bio ?? ""
    }
  });

  const onSubmit = async (values: ProfileValues) => {
    setError(null);
    try {
      const updated = await authApi.updateProfile({
        full_name: values.full_name,
        phone: values.phone || undefined,
        city: values.city || undefined,
        bio: values.bio || undefined
      });
      setUser(updated);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Yeniləmə uğursuz oldu");
    }
  };

  return (
    <RequireAuth>
      <div className="mx-auto w-full max-w-2xl px-4 py-10">
        <h1 className="text-2xl font-semibold tracking-tight">Profil</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Hesab məlumatlarınızı burada yeniləyə bilərsiniz.
        </p>

        <div className="mt-8 rounded-2xl bg-surface p-6 ring-1 ring-border/70">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-soft text-lg font-bold text-brand">
              {user?.full_name
                .split(/\s+/)
                .map((p) => p[0])
                .slice(0, 2)
                .join("")
                .toUpperCase()}
            </div>
            <div>
              <p className="font-semibold">{user?.email}</p>
              <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <ShieldCheck className="h-3.5 w-3.5 text-brand" />
                {user?.role === "user"
                  ? "Standart istifadəçi"
                  : user?.role === "moderator"
                    ? "Moderator"
                    : user?.role === "admin" || user?.role === "super_admin"
                      ? "Administrator"
                      : "Satıcı"}
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-4">
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground/75">
                Ad və soyad
              </label>
              <Input {...register("full_name")} aria-invalid={!!errors.full_name} />
              {errors.full_name ? (
                <p className="mt-1 text-xs text-red-600">
                  {errors.full_name.message}
                </p>
              ) : null}
            </div>
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground/75">
                Telefon
              </label>
              <Input
                {...register("phone")}
                placeholder="+994501234567"
                inputMode="tel"
                aria-invalid={!!errors.phone}
              />
              {errors.phone ? (
                <p className="mt-1 text-xs text-red-600">{errors.phone.message}</p>
              ) : null}
            </div>
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground/75">
                Şəhər
              </label>
              <Input {...register("city")} placeholder="Bakı" />
            </div>
            <div>
              <label className="mb-1.5 block text-[13px] font-medium text-foreground/75">
                Haqqımda
              </label>
              <textarea
                {...register("bio")}
                rows={4}
                placeholder="Özünüz haqqında qısa məlumat…"
                className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm outline-none transition-colors placeholder:text-foreground/35 focus:border-brand/60 focus:ring-2 focus:ring-brand/15"
              />
              {errors.bio ? (
                <p className="mt-1 text-xs text-red-600">{errors.bio.message}</p>
              ) : null}
            </div>

            {error ? (
              <div className="flex items-center gap-2 rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">
                <Info className="h-4 w-4 shrink-0" />
                {error}
              </div>
            ) : null}

            <div className="flex items-center gap-3 pt-1">
              <Button type="submit" disabled={isSubmitting} className="gap-2">
                <Save className="h-4 w-4" />
                {isSubmitting ? "Yadda saxlanılır…" : "Yadda saxla"}
              </Button>
              {saved ? (
                <span className="text-sm text-brand">Yadda saxlanıldı</span>
              ) : null}
            </div>
          </form>
        </div>
      </div>
    </RequireAuth>
  );
}
