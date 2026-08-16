"use client";

import * as React from "react";
import Link from "next/link";
import type { Property } from "@yenimenzil/types";
import { useFavoritesStore } from "@/stores/favorites-store";
import { fetchPropertyById } from "@/services/property-api";
import { PropertyCard } from "@/features/properties/property-card";
import { EmptyState, SectionHeading, Skeleton, Button } from "@yenimenzil/ui";
import { Heart, FolderPlus, Folder, Trash2, Pencil, Check, X } from "lucide-react";
import { dashboardApi, type FavoriteCollection } from "@/services/dashboard-api";
import { useAuth } from "@/store/auth";
import { cn } from "@yenimenzil/ui";

interface MoveMenuProps {
  propertyId: string;
  collections: FavoriteCollection[];
  onMoved: () => void;
}

function MoveMenu({ propertyId, collections, onMoved }: MoveMenuProps) {
  const [open, setOpen] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) return;
    const onClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, [open]);

  const move = async (collectionId: string | null) => {
    setBusy(true);
    try {
      await dashboardApi.moveFavorite(propertyId, collectionId);
      onMoved();
    } finally {
      setBusy(false);
      setOpen(false);
    }
  };

  return (
    <div className="relative" ref={menuRef}>
      <Button
        size="sm"
        variant="secondary"
        className="gap-1.5"
        disabled={busy}
        onClick={() => setOpen((v) => !v)}
      >
        <Folder className="h-3.5 w-3.5" />
        Koleksiyona köçür
      </Button>
      {open ? (
        <div className="absolute right-0 top-full z-30 mt-1 w-56 rounded-xl border border-border bg-surface p-1 shadow-panel">
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[13px] hover:bg-brand-soft"
            onClick={() => move(null)}
          >
            <Heart className="h-3.5 w-3.5" /> Seçilmişlər (əsas)
          </button>
          {collections.map((c) => (
            <button
              key={c.id}
              type="button"
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-[13px] hover:bg-brand-soft"
              onClick={() => move(c.id)}
            >
              <Folder className="h-3.5 w-3.5" /> {c.name}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function FavoritesList() {
  const status = useAuth((s) => s.status);
  const hydrate = useFavoritesStore((s) => s.hydrate);
  const ids = useFavoritesStore((s) => s.ids);

  const [collections, setCollections] = React.useState<FavoriteCollection[]>([]);
  const [active, setActive] = React.useState<string | null>(null); // null = default list
  const [serverListings, setServerListings] = React.useState<Property[] | null>(null);
  const [creating, setCreating] = React.useState(false);
  const [newName, setNewName] = React.useState("");
  const [renaming, setRenaming] = React.useState<string | null>(null);
  const [renameValue, setRenameValue] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);

  const authed = status === "authenticated";

  const loadCollections = React.useCallback(() => {
    dashboardApi
      .favoriteCollections()
      .then(setCollections)
      .catch(() => {});
  }, []);

  const loadServer = React.useCallback(
    (collectionId: string | null) => {
      dashboardApi
        .favorites(collectionId ?? undefined)
        .then(setServerListings)
        .catch(() => setServerListings([]));
    },
    []
  );

  React.useEffect(() => {
    void (async () => {
      await Promise.resolve();
      if (authed) {
        hydrate();
        loadCollections();
        loadServer(active);
      } else {
        setServerListings(null);
      }
    })();
  }, [authed, active, hydrate, loadCollections, loadServer]);

  const visibleIds = authed && serverListings ? serverListings.map((p) => p.id) : ids;
  const [listings, setListings] = React.useState<Property[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    void (async () => {
      await Promise.resolve();
      if (authed && serverListings) {
        setListings(serverListings);
        setLoading(false);
        return;
      }
      const found = await Promise.all(visibleIds.map((id) => fetchPropertyById(id)));
      setListings(found.filter((p) => p != null));
      setLoading(false);
    })().catch(() => {
      setListings([]);
      setLoading(false);
    });
  }, [visibleIds, authed, serverListings]);

  const createCollection = async () => {
    const name = newName.trim();
    if (!name) return;
    try {
      await dashboardApi.createFavoriteCollection(name);
      setNewName("");
      setCreating(false);
      loadCollections();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    }
  };

  const renameCollection = async (id: string) => {
    try {
      await dashboardApi.renameFavoriteCollection(id, renameValue.trim());
      setRenaming(null);
      loadCollections();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Xəta");
    }
  };

  const deleteCollection = async (id: string) => {
    await dashboardApi.deleteFavoriteCollection(id);
    if (active === id) setActive(null);
    loadCollections();
    loadServer(null);
  };

  const refreshActive = () => {
    loadServer(active);
    loadCollections();
  };

  const empty = listings.length === 0;

  return (
    <div>
      <SectionHeading
        title="Seçilmişlər"
        subtitle="Sizə uyğun elanları koleksiyonlarda saxlayın"
      />

      {/* Collection tabs */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => setActive(null)}
          className={cn(
            "flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-[13px] font-medium transition-colors",
            active === null
              ? "border-brand/30 bg-brand-soft text-brand"
              : "border-border text-foreground/70 hover:bg-foreground/[0.04]"
          )}
        >
          <Heart className="h-3.5 w-3.5" />
          Əsas ({authed && serverListings ? serverListings.length : ids.length})
        </button>
        {collections.map((c) => (
          <div key={c.id} className="group flex items-center gap-1">
            <button
              type="button"
              onClick={() => setActive(c.id)}
              className={cn(
                "flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-[13px] font-medium transition-colors",
                active === c.id
                  ? "border-brand/30 bg-brand-soft text-brand"
                  : "border-border text-foreground/70 hover:bg-foreground/[0.04]"
              )}
            >
              <Folder className="h-3.5 w-3.5" />
              {c.name} ({c.favorite_count})
            </button>
            <div className="hidden items-center gap-0.5 group-hover:flex">
              <button
                type="button"
                aria-label="Rename"
                className="rounded-md p-1 text-foreground/50 hover:text-foreground"
                onClick={() => {
                  setRenaming(c.id);
                  setRenameValue(c.name);
                }}
              >
                <Pencil className="h-3 w-3" />
              </button>
              <button
                type="button"
                aria-label="Delete"
                className="rounded-md p-1 text-foreground/50 hover:text-red-500"
                onClick={() => void deleteCollection(c.id)}
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </div>
          </div>
        ))}

        {authed ? (
          creating ? (
            <div className="flex items-center gap-1.5">
              <input
                autoFocus
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && void createCollection()}
                placeholder="Koleksiya adı"
                className="h-8 w-40 rounded-lg border border-border bg-surface px-2.5 text-[13px] outline-none focus:border-brand"
              />
              <button
                type="button"
                aria-label="Save"
                className="rounded-md p-1 text-brand"
                onClick={() => void createCollection()}
              >
                <Check className="h-4 w-4" />
              </button>
              <button
                type="button"
                aria-label="Cancel"
                className="rounded-md p-1 text-foreground/50"
                onClick={() => setCreating(false)}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setCreating(true)}
              className="flex items-center gap-1.5 rounded-full border border-dashed border-border px-3.5 py-1.5 text-[13px] font-medium text-foreground/60 transition-colors hover:border-brand/40 hover:text-brand"
            >
              <FolderPlus className="h-3.5 w-3.5" /> Yeni koleksiya
            </button>
          )
        ) : null}
      </div>

      {renaming ? (
        <div className="mt-3 flex items-center gap-2">
          <input
            autoFocus
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void renameCollection(renaming)}
            className="h-9 w-56 rounded-lg border border-border bg-surface px-3 text-sm outline-none focus:border-brand"
          />
          <Button size="sm" onClick={() => void renameCollection(renaming)}>
            Yadda saxla
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setRenaming(null)}>
            Ləğv et
          </Button>
        </div>
      ) : null}

      {error ? <p className="mt-2 text-sm text-red-500">{error}</p> : null}

      {empty && !loading ? (
        <div className="mt-6">
          <EmptyState
            icon={<Heart className="h-7 w-7" />}
            title="Seçilmişlər boşdur"
            description="Elanlarda ürək işarəsinə klikləyin — seçdiyiniz elanlar burada toplanacaq."
            action={
              <Link
                href="/search"
                className="inline-flex h-11 items-center justify-center rounded-[10px] bg-brand px-6 text-sm font-medium text-white hover:bg-brand-hover"
              >
                Elanlara bax
              </Link>
            }
          />
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="overflow-hidden rounded-2xl bg-surface ring-1 ring-border/70"
                >
                  <Skeleton className="aspect-[4/3] w-full rounded-none" />
                  <div className="space-y-2.5 p-3.5">
                    <Skeleton className="h-5 w-2/5" />
                    <Skeleton className="h-4 w-4/5" />
                  </div>
                </div>
              ))
            : listings.map((listing) => (
                <div key={listing.id} className="flex flex-col gap-2">
                  <PropertyCard property={listing} />
                  {authed ? (
                    <div className="flex justify-end">
                      <MoveMenu
                        propertyId={listing.id}
                        collections={collections.filter((c) => c.id !== active)}
                        onMoved={refreshActive}
                      />
                    </div>
                  ) : null}
                </div>
              ))}
        </div>
      )}
    </div>
  );
}