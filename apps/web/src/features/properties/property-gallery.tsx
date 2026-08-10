"use client";

import * as React from "react";
import type { Property } from "@yenimenzil/types";
import { Camera, X } from "lucide-react";
import { ImageWithFallback } from "@/components/common/image-with-fallback";

export function PropertyGallery({ property }: { property: Property }) {
  const [lightboxOpen, setLightboxOpen] = React.useState(false);
  const [activeIndex, setActiveIndex] = React.useState(0);
  const images = property.images;
  if (images.length === 0) return null;

  const hero = images[0]!;
  const thumbs = images.slice(1, 5);

  const openLightbox = (index: number) => {
    setActiveIndex(index);
    setLightboxOpen(true);
  };

  return (
    <>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-[2fr_1fr] md:gap-2.5">
        <div className="relative col-span-2 aspect-[4/3] overflow-hidden rounded-2xl bg-foreground/[0.03] ring-1 ring-border/60 md:col-span-1 md:aspect-auto md:min-h-[420px]">
          <button
            type="button"
            className="absolute inset-0 z-10 cursor-zoom-in"
            aria-label="Şəkli böyüt"
            onClick={() => openLightbox(0)}
          />
          <ImageWithFallback
            src={hero.src}
            alt={hero.alt}
            fill
            priority
            sizes="(max-width: 768px) 100vw, 60vw"
            placeholder="blur"
            blurDataURL={hero.placeholder}
            className="object-cover"
          />
        </div>
        <div className="hidden md:grid grid-rows-2 gap-2.5">
          {thumbs.map((img, i) => (
            <button
              key={img.src + i}
              type="button"
              className="relative overflow-hidden rounded-2xl bg-foreground/[0.03] ring-1 ring-border/60 transition-all hover:ring-brand/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40"
              onClick={() => openLightbox(i + 1)}
            >
              <ImageWithFallback
                src={img.src}
                alt={img.alt}
                fill
                sizes="25vw"
                placeholder="blur"
                blurDataURL={img.placeholder}
                className="object-cover transition-transform duration-300 hover:scale-[1.03]"
              />
            </button>
          ))}
          {thumbs.length === 1 ? (
            <div className="relative overflow-hidden rounded-2xl bg-foreground/[0.03]" />
          ) : null}
          {thumbs.length === 0 ? (
            <div className="relative overflow-hidden rounded-2xl bg-foreground/[0.03]" />
          ) : null}
        </div>
      </div>

      <div className="mt-2.5 flex items-center justify-between gap-2 md:hidden">
        <div className="flex gap-1.5 overflow-x-auto">
          {images.map((img, i) => (
            <button
              key={img.src + i}
              type="button"
              className="relative h-16 w-20 shrink-0 overflow-hidden rounded-lg bg-foreground/[0.03]"
              onClick={() => openLightbox(i)}
            >
              <ImageWithFallback
                src={img.src}
                alt={img.alt}
                fill
                sizes="80px"
                className="object-cover"
              />
            </button>
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={() => openLightbox(0)}
        className="mt-3 hidden items-center gap-2 rounded-xl border border-border bg-surface px-4 py-2.5 text-sm font-medium text-foreground/80 shadow-sm transition-colors hover:border-brand/30 hover:text-brand md:inline-flex"
      >
        <Camera className="h-4 w-4" />
        Bütün şəkillərə bax ({images.length})
      </button>

      {lightboxOpen ? (
        <div className="fixed inset-0 z-50 bg-black/95">
          <button
            type="button"
            onClick={() => setLightboxOpen(false)}
            className="absolute right-4 top-4 z-20 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white transition-colors hover:bg-white/20"
            aria-label="Bağla"
          >
            <X className="h-5 w-5" />
          </button>
          <span className="absolute left-1/2 top-4 z-20 -translate-x-1/2 rounded-full bg-white/10 px-4 py-1.5 text-sm text-white">
            {activeIndex + 1} / {images.length}
          </span>
          <div className="relative flex h-full items-center justify-center p-4">
            <ImageWithFallback
              src={images[activeIndex]!.src}
              alt={images[activeIndex]!.alt}
              width={1200}
              height={900}
              className="max-h-[80dvh] w-auto rounded-xl object-contain"
            />
          </div>
          <div className="absolute inset-x-0 bottom-4 flex justify-center gap-2">
            <button
              type="button"
              onClick={() =>
                setActiveIndex((i) => (i - 1 + images.length) % images.length)
              }
              className="rounded-full bg-white/10 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-white/20"
            >
              ← Əvvəl
            </button>
            <button
              type="button"
              onClick={() =>
                setActiveIndex((i) => (i + 1) % images.length)
              }
              className="rounded-full bg-white/10 px-5 py-2 text-sm font-medium text-white transition-colors hover:bg-white/20"
            >
              Sonrakı →
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
}
