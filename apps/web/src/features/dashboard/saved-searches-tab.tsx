"use client";

import * as React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Skeleton, EmptyState, Button, Input, Badge } from "@yenimenzil/ui";
import { Search, Bell, BellOff, Mail, MailX, Trash2, Plus } from "lucide-react";
import { dashboardApi, type SavedSearch } from "@/services/dashboard-api";
import { formatDate } from "@/lib/format";

const searchSchema = z.object({
  name: z.string().min(2, "Axtarış adı daxil edin").max(150)
});

type SearchValues = z.infer<typeof searchSchema>;

function filtersToQuery(filters: Record<string, unknown>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      for (const item of value) params.append(key, String(item));
    } else {
      params.set(key, String(value));
    }
  }
  return `/search?${params.toString()}`;
}

function filtersSummary(filters: Record<string, unknown>): string {
  const parts: string[] = [];
  if (filters.deal_type) {
    parts.push(
      filters.deal_type === "sale" ? "Alış" : filters.deal_type === "rent" ? "Kirayə" : "Günlük"
    );
  }
  if (filters.city || filters.location_city) {
    parts.push(String(filters.city ?? filters.location_city));
  }
  if (filters.property_type) parts.push(String(filters.property_type));
  if (typeof filters.price_min === "number") parts.push(`${filters.price_min}+ AZN`);
  return parts.join(" · ") || "Bütün elanlar";
}

export function SavedSearchesTab() {
  const [searches, setSearches] = React.useState<SavedSearch[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [adding, setAdding] = React.useState(false);
  const [busyId, setBusyId] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting }
  } = useForm<SearchValues>({
    resolver: zodResolver(searchSchema)
  });

  const load = React.useCallback(() => {
    dashboardApi
      .listSavedSearches()
      .then((data) => {
        setSearches(data);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Xəta"));
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const create = async (values: SearchValues) => {
    setError(null);
    try {
      const created = await dashboardApi.createSavedSearch({
        name: values.name,
        filters: { deal_type: "sale" }
      });
      setSearches((prev) => (prev ? [...prev, created] : [created]));
      reset();
      setAdding(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    }
  };

  const toggle = async (search: SavedSearch) => {
    if (!searches) return;
    setBusyId(search.id);
    setError(null);
    try {
      const updated = await dashboardApi.updateSavedSearch(search.id, {
        is_active: !search.is_active
      });
      setSearches(searches.map((s) => (s.id === search.id ? updated : s)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setBusyId(null);
    }
  };

  const toggleEmail = async (search: SavedSearch) => {
    if (!searches) return;
    setBusyId(search.id);
    setError(null);
    try {
      const updated = await dashboardApi.updateSavedSearch(search.id, {
        email_enabled: !search.email_enabled
      });
      setSearches(searches.map((s) => (s.id === search.id ? updated : s)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (id: string) => {
    if (!window.confirm("Saxlanılmış axtarışı silmək istəyirsiniz?")) return;
    if (!searches) return;
    setBusyId(id);
    setError(null);
    try {
      await dashboardApi.deleteSavedSearch(id);
      setSearches(searches.filter((s) => s.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    } finally {
      setBusyId(null);
    }
  };

  if (!searches && !error) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-2xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error ? (
        <p className="rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">{error}</p>
      ) : null}

      {adding ? (
        <form
          onSubmit={handleSubmit(create)}
          className="rounded-2xl bg-surface p-4 ring-1 ring-border/70"
        >
          <label className="mb-1.5 block text-[13px] font-medium text-foreground/75">
            Axtarış adı
          </label>
          <div className="flex gap-2">
            <Input {...register("name")} placeholder="Məs: Bakı, 2 otaqlı, 100k AZN" className="flex-1" />
            <Button type="submit" disabled={isSubmitting} className="shrink-0">
              {isSubmitting ? "Saxlanılır…" : "Saxla"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="shrink-0"
              onClick={() => {
                setAdding(false);
                reset();
              }}
            >
              Ləğv et
            </Button>
          </div>
          {errors.name ? (
            <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>
          ) : null}
        </form>
      ) : (
        <Button onClick={() => setAdding(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Yeni axtarış
        </Button>
      )}

      {!searches || searches.length === 0 ? (
        <EmptyState
          icon={<Search className="h-7 w-7" />}
          title="Saxlanılmış axtarış yoxdur"
          description="Axtarış filtrinizi saxlayın — yeni uyğun elanlar çıxanda sizə bildiriş gələcək."
        />
      ) : (
        <div className="space-y-3">
          {searches.map((search) => (
            <div
              key={search.id}
              className="flex flex-wrap items-center gap-3 rounded-2xl bg-surface p-4 ring-1 ring-border/70"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="font-semibold">{search.name}</p>
                  <Badge variant={search.is_active ? "green" : "neutral"}>
                    {search.is_active ? (
                      <Bell className="h-3 w-3" />
                    ) : (
                      <BellOff className="h-3 w-3" />
                    )}
                    {search.is_active ? "Aktiv" : "Deaktiv"}
                  </Badge>
                </div>
                <p className="mt-0.5 text-[13px] text-muted-foreground">
                  {filtersSummary(search.filters)} · {formatDate(search.created_at)}
                </p>
              </div>
              <div className="flex gap-2">
                <Link
                  href={filtersToQuery(search.filters)}
                  className="rounded-xl bg-brand px-3.5 py-2 text-[13px] font-semibold text-white transition-colors hover:bg-brand/90"
                >
                  Bax
                </Link>
                <button
                  onClick={() => toggle(search)}
                  disabled={busyId === search.id}
                  className="rounded-xl bg-foreground/[0.05] px-3 py-2 text-[13px] font-medium transition-colors hover:bg-foreground/[0.09] disabled:opacity-50"
                >
                  {search.is_active ? "Deaktiv et" : "Aktiv et"}
                </button>
                <button
                  onClick={() => toggleEmail(search)}
                  disabled={busyId === search.id}
                  title={search.email_enabled ? "E-poçt xəbərdarlığı açıqdır" : "E-poçt xəbərdarlığı bağlıdır"}
                  className={
                    "rounded-xl px-3 py-2 text-[13px] font-medium transition-colors disabled:opacity-50 " +
                    (search.email_enabled
                      ? "bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/15"
                      : "bg-foreground/[0.05] text-foreground/60 hover:bg-foreground/[0.09]")
                  }
                >
                  {search.email_enabled ? (
                    <Mail className="h-4 w-4" />
                  ) : (
                    <MailX className="h-4 w-4" />
                  )}
                </button>
                <button
                  onClick={() => remove(search.id)}
                  disabled={busyId === search.id}
                  aria-label="Axtarışı sil"
                  className="rounded-xl bg-red-500/10 px-3 py-2 text-red-600 transition-colors hover:bg-red-500/15 disabled:opacity-50"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
