"use client";

import { Skeleton } from "@yenimenzil/ui";

export function PropertyCardSkeleton() {
  return (
    <div className="overflow-hidden rounded-2xl bg-surface ring-1 ring-border/70">
      <Skeleton className="aspect-[4/3] w-full rounded-none" />
      <div className="space-y-2.5 p-3.5">
        <Skeleton className="h-5 w-2/5" />
        <Skeleton className="h-4 w-4/5" />
        <Skeleton className="h-3.5 w-1/2" />
        <Skeleton className="h-3.5 w-3/5" />
      </div>
    </div>
  );
}

export function PropertyListRowSkeleton() {
  return (
    <div className="flex gap-4 rounded-2xl bg-surface p-3 ring-1 ring-border/70">
      <Skeleton className="h-40 w-44 rounded-xl sm:w-56" />
      <div className="flex-1 space-y-2.5 py-1">
        <Skeleton className="h-5 w-1/3" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3.5 w-1/2" />
      </div>
    </div>
  );
}

export function PropertyDetailSkeleton() {
  return (
    <div className="mx-auto max-w-[1200px] px-4 py-5 lg:px-6 lg:py-7 space-y-6">
      <div className="aspect-[16/9] w-full rounded-2xl bg-foreground/[0.03] animate-pulse" />
      <div className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70 md:p-6">
        <Skeleton className="h-8 w-3/5 mb-3" />
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <div className="mt-4 grid grid-cols-2 gap-x-6 md:grid-cols-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
      <div className="space-y-5">
        <div className="rounded-2xl bg-surface p-5">
          <Skeleton className="h-6 w-1/4 mb-3" />
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </div>
        <div className="rounded-2xl bg-surface p-5">
          <Skeleton className="h-6 w-1/4 mb-3" />
          <div className="flex flex-wrap gap-2">
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-32 rounded-full" />
            <Skeleton className="h-8 w-28 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function SearchResultsSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="flex gap-4 rounded-2xl bg-surface p-3 ring-1 ring-border/70"
        >
          <Skeleton className="h-40 w-44 rounded-xl sm:w-56" />
          <div className="flex-1 space-y-2.5 py-1">
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3.5 w-1/2" />
            <Skeleton className="h-3.5 w-2/3" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function MapSkeleton() {
  return (
    <div className="absolute inset-0 bg-foreground/[0.03] animate-pulse" />
  );
}

export function DashboardCardSkeleton() {
  return (
    <div className="rounded-2xl bg-surface p-5 shadow-[0_1px_2px_rgba(20,23,22,0.04)] ring-1 ring-border/70">
      <Skeleton className="h-5 w-1/3 mb-2" />
      <Skeleton className="h-10 w-1/4" />
    </div>
  );
}

export function ListingWizardSkeleton() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-8 space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-7 w-1/3" />
        <Skeleton className="h-5 w-1/2" />
      </div>
      <div className="rounded-2xl bg-surface p-6 space-y-5">
        <div className="flex items-center justify-between">
          <Skeleton className="h-5 w-1/4" />
          <Skeleton className="h-8 w-20" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
        </div>
        <div className="flex gap-3">
          <Skeleton className="h-11 flex-1" />
          <Skeleton className="h-11 flex-1" />
        </div>
      </div>
    </div>
  );
}