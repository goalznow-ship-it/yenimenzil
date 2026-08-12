"use client";

import * as React from "react";
import { Search } from "lucide-react";
import { adminApi } from "@/services/admin-api";
import { AdminPageHeader } from "../layout";

export default function AdminLocationsPage() {
  const [data, setData] = React.useState<{
    cities: { name: string; listings: number }[];
    districts: { name: string; listings: number }[];
    metros: { name: string; listings: number }[];
    unlocated: number;
  } | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let isMounted = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await adminApi.locations();
        if (isMounted) {
          setData(res);
        }
      } catch (e) {
        if (isMounted) {
          setError(e instanceof Error ? e.message : "Xəta");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      isMounted = false;
    };
  }, []);

  if (error) {
    return (
      <div>
        <AdminPageHeader title="Location overview" subtitle="Şəhər, rayon və metro statistikaları" icon={Search} />
        <p className="rounded-xl bg-red-500/10 p-4 text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div>
        <AdminPageHeader title="Location overview" subtitle="Şəhər, rayon və metro statistikaları" icon={Search} />
        <div className="space-y-6">
          <div className="h-20 animate-pulse rounded-2xl bg-foreground/[0.04]" />
          <div className="h-20 animate-pulse rounded-2xl bg-foreground/[0.04]" />
          <div className="h-20 animate-pulse rounded-2xl bg-foreground/[0.04]" />
          <div className="h-20 animate-pulse rounded-2xl bg-foreground/[0.04]" />
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div>
        <AdminPageHeader title="Location overview" subtitle="Şəhər, rayon və metro statistikaları" icon={Search} />
        <p className="text-center text-foreground/50">Heç bir məlumat yoxdur</p>
      </div>
    );
  }

  return (
    <div>
      <AdminPageHeader title="Location overview" subtitle="Şəhər, rayon və metro statistikaları" icon={Search} />
      <>
        <div className="mb-6">
          <h2 className="mb-3 font-semibold">Şəhərlər</h2>
          {data.cities.length === 0 ? (
            <p className="text-sm text-foreground/50">Şəhər tapılmadı</p>
          ) : (
            <div className="space-y-2">
              {data.cities.map((city) => (
                <div key={city.name} className="flex items-center justify-between rounded-xl border border-border/50 p-3">
                  <span>{city.name}</span>
                  <span className="font-medium">{city.listings} elan</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mb-6">
          <h2 className="mb-3 font-semibold">Rayonlar</h2>
          {data.districts.length === 0 ? (
            <p className="text-sm text-foreground/50">Rayon tapılmadı</p>
          ) : (
            <div className="space-y-2">
              {data.districts.map((district) => (
                <div key={district.name} className="flex items-center justify-between rounded-xl border border-border/50 p-3">
                  <span>{district.name}</span>
                  <span className="font-medium">{district.listings} elan</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mb-6">
          <h2 className="mb-3 font-semibold">Metro stansiyaları</h2>
          {data.metros.length === 0 ? (
            <p className="text-sm text-foreground/50">Metro tapılmadı</p>
          ) : (
            <div className="space-y-2">
              {data.metros.map((metro) => (
                <div key={metro.name} className="flex items-center justify-between rounded-xl border border-border/50 p-3">
                  <span>{metro.name}</span>
                  <span className="font-medium">{metro.listings} elan</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-border/60 bg-surface p-4">
          <h2 className="mb-3 font-semibold">Locationı olmayan elanlar</h2>
          <p className="text-sm text-foreground/50">
            {data.unlocated} elan location informationi yoxdur
          </p>
        </div>
      </>
    </div>
  );
}