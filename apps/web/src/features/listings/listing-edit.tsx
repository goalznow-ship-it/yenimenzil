"use client";

import * as React from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { listingWriteApi } from "@/services/listing-write-api";
import { ListingWizard } from "./listing-wizard";

export function ListingEdit() {
  const params = useParams<{ id: string }>();
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [initial, setInitial] = React.useState<Awaited<
    ReturnType<typeof listingWriteApi.get>
  > | null>(null);

  React.useEffect(() => {
    if (!params?.id) return;
    listingWriteApi
      .get(params.id)
      .then((detail) => {
        setInitial(detail);
        setError(null);
      })
      .catch((err) =>
        setError(
          err instanceof Error
            ? err.message
            : "Elan yüklənə bilmədi. Daxil olub olmadığınızı yoxlayın."
        )
      )
      .finally(() => setLoading(false));
  }, [params?.id]);

  if (loading) {
    return (
      <div className="mx-auto w-full max-w-2xl px-4 py-10 text-sm text-muted-foreground">
        Elan yüklənir…
      </div>
    );
  }

  if (error || !initial) {
    return (
      <div className="mx-auto w-full max-w-2xl px-4 py-16 text-center">
        <p className="rounded-xl bg-red-500/10 px-3.5 py-2.5 text-[13px] text-red-600">
          {error ?? "Elan tapılmadı"}
        </p>
        <Link
          href="/profile"
          className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-brand hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          İdarə panelinə qayıt
        </Link>
      </div>
    );
  }

  return <ListingWizard listingId={initial.id} initialListing={initial} />;
}
