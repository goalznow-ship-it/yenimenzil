"use client";

import * as React from "react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Badge, Skeleton } from "@yenimenzil/ui";
import { Phone, Mail, ShieldCheck, BadgeCheck } from "lucide-react";
import { fetchAgentProfile } from "@/services/property-api";
import { PropertyCard } from "@/features/properties/property-card";
import { formatPhoneDisplay } from "@/lib/format";

export function AgentProfilePage({ agentId }: { agentId: string }) {
  const [data, setData] = React.useState<Awaited<ReturnType<typeof fetchAgentProfile>>>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let cancelled = false;
    fetchAgentProfile(agentId)
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
  }, [agentId]);

  if (loading) {
    return (
      <div className="mx-auto max-w-[1200px] px-4 py-8 lg:px-6">
        <Skeleton className="h-40 rounded-2xl" />
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

  const { agent, listings, is_mine } = data;

  return (
    <div className="mx-auto max-w-[1200px] px-4 py-8 lg:px-6">
      <div className="rounded-2xl bg-surface p-6 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 md:p-8">
        <div className="flex flex-wrap items-center gap-5">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-brand-soft text-2xl font-bold text-brand">
            {agent.name
              .split(/\s+/)
              .map((p) => p[0])
              .slice(0, 2)
              .join("")
              .toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold tracking-tight">{agent.name}</h1>
              {agent.verified_identity ? (
                <Badge variant="green">
                  <BadgeCheck className="h-3 w-3" />
                  Kimlik təsdiqlənib
                </Badge>
              ) : null}
              {agent.verified_phone ? (
                <Badge variant="brand">
                  <ShieldCheck className="h-3 w-3" />
                  Telefon təsdiqlənib
                </Badge>
              ) : null}
              {is_mine ? <Badge variant="gold">Bu sizsiniz</Badge> : null}
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {listings.length} aktiv elan
              {agent.member_since
                ? ` · ${new Date(agent.member_since).getFullYear()}-ci ildən`
                : ""}
            </p>
            {agent.phone ? (
              <p className="mt-2 flex items-center gap-1.5 text-sm text-foreground/75">
                <Phone className="h-4 w-4 text-foreground/40" />
                {formatPhoneDisplay(agent.phone)}
              </p>
            ) : null}
            {agent.email ? (
              <p className="mt-1 flex items-center gap-1.5 text-sm text-foreground/75">
                <Mail className="h-4 w-4 text-foreground/40" />
                {agent.email}
              </p>
            ) : null}
          </div>
        </div>
      </div>

      <h2 className="mt-8 mb-4 text-xl font-semibold tracking-tight">Agentin elanları</h2>
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
