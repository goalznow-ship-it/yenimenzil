"use client";

import * as React from "react";
import Image from "next/image";
import { ImageIcon } from "lucide-react";

interface ImageWithFallbackProps {
  src: string;
  alt: string;
  fill?: boolean;
  width?: number;
  height?: number;
  sizes?: string;
  priority?: boolean;
  placeholder?: "blur" | "empty";
  blurDataURL?: string;
  className?: string;
}

export function ImageWithFallback({
  src,
  alt,
  fill,
  width,
  height,
  sizes,
  priority,
  placeholder,
  blurDataURL,
  className
}: ImageWithFallbackProps) {
  const [failed, setFailed] = React.useState(false);

  if (failed) {
    return (
      <div
        role="img"
        aria-label={alt}
        className={`flex items-center justify-center bg-brand-soft ${className ?? ""}`}
        style={
          fill
            ? { position: "absolute", inset: 0 }
            : { width: width ?? "100%", height: height ?? "100%" }
        }
      >
        <ImageIcon className="h-8 w-8 text-brand/30" />
      </div>
    );
  }

  const common = {
    src,
    alt,
    onError: () => setFailed(true),
    className,
    placeholder: placeholder === "blur" && blurDataURL ? "blur" : "empty"
  } satisfies React.ComponentProps<typeof Image>;

  if (fill) {
    return (
      <Image
        {...common}
        alt={alt}
        fill
        sizes={sizes}
        priority={priority}
        blurDataURL={blurDataURL}
      />
    );
  }

  return (
    <Image
      {...common}
      alt={alt}
      width={width}
      height={height}
      sizes={sizes}
      priority={priority}
      blurDataURL={blurDataURL}
    />
  );
}
