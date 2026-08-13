"use client";

import * as React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge, Skeleton } from "@yenimenzil/ui";
import { Phone, Mail, Globe, BadgeCheck } from "lucide-react";
import { fetchAgencyProfile } from "@/services/property-api";
import { PropertyCard } from "@/features/properties/property-card";
import { formatPhoneDisplay } from "@/lib/format";

export function AgencyProfilePage({ agencyId }: { agencyId: string }) {
  const [data, setData] = React.useState<Awaited<ReturnType<typeof fetchAgencyProfile>>>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;
    fetchAgencyProfile(agencyId)
      .then((result) => {
        if (cancelled) return;
        setData(result);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [agencyId]);

  if (loading) {
    return (
      <div className="mx-auto max-w-[1200px] px-4 py-8 lg:px-6">
        <Skeleton className="h-44 rounded-2xl" />
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="aspect-[4/3] rounded-2xl" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    notFound();
  }

  const { agency, listings, agents } = data;

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-8 lg:px-6">
      <div className="rounded-2xl bg-surface p-6 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 md:p-8">
        <div className="flex flex-wrap items-center gap-5">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-brand-soft text-2xl font-bold text-brand">
            {agency.name
              .split(/\s+/)
              .map((p) => p[0])
              .slice(0, 2)
              .join("")
              .toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">{agency.name}</h1>
              {agency.verified ? (
                <Badge variant="green">
                  <BadgeCheck className="h-3 w-3" />
                  Təsdiqlənmiş agentlik
                </Badge>
              ) : null}
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {listings.length} aktiv elan · {agents.length} agent
              {agency.member_since
                ? ` · ${new Date(agency.member_since).getFullYear()}-ci ildən`
                : ""}
            </p>
            {agency.description ? (
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-foreground/75">
                {agency.description}
              </p>
            ) : null}
            <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-foreground/75">
              {agency.phone ? (
                <span className="flex items-center gap-1.5">
                  <Phone className="h-4 w-4 text-foreground/40" />
                  {formatPhoneDisplay(agency.phone)}
                </span>
              ) : null}
              {agency.email ? (
                <span className="flex items-center gap-1.5">
                  <Mail className="h-4 w-4 text-foreground/40" />
                  {agency.email}
                </span>
              ) : null}
              {agency.website ? (
                <span className="flex items-center gap-1.5">
                  <Globe className="h-4 w-4 text-foreground/40" />
                  {agency.website}
                </span>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      {agents.length > 0 ? (
        <>
          <h2 className="mt-8 mb-4 text-xl font-semibold tracking-tight">Agentlər</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {agents.map((agent) => (
              <Link
                key={agent.id}
                href={`/agents/${agent.id}`}
                className="rounded-2xl bg-surface p-4 ring-1 ring-border/70 transition-all hover:-translate-y-0.5 hover:shadow-card hover:ring-brand/20"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-brand-soft text-sm font-bold text-brand">
                    {agent.name
                      .split(/\s+/)
                      .map((p) => p[0])
                      .slice(0, 2)
                      .join("")
                      .toUpperCase()}
                  </div>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold">{agent.name}</p>
                    {agent.verified_phone ? (
                      <p className="text-xs text-emerald-600">Telefon təsdiqlənib</p>
                    ) : null}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </>
      ) : null}

      <h2 className="mt-8 mb-4 text-xl font-semibold tracking-tight">Agentliyin elanları</h2>
      {listings.length === 0 ? (
        <p className="rounded-2xl bg-surface p-10 text-center text-sm text-muted-foreground ring-1 ring-border/70">
          Aktiv elan yoxdur.
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {listings.map((listing) => (
            <PropertyCard key={listing.id} property={listing} />
          ))}
        </div>
      )}

      <Link
        href="/search"
        className="mt-6 inline-block text-sm font-medium text-muted-foreground transition-colors hover:text-brand"
      >
        ← Axtarışa qayıt
      </Link>
    </div>
  );
}
