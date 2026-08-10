import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-[60dvh] max-w-xl flex-col items-center justify-center px-4 text-center">
      <p className="text-5xl font-semibold tracking-tight text-foreground/15">
        404
      </p>
      <h1 className="mt-4 text-xl font-semibold text-foreground">
        Səhifə tapılmadı
      </h1>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        Axtardığınız səhifə mövcud deyil və ya ünvanı dəyişib.
      </p>
      <Link
        href="/"
        className="mt-6 inline-flex h-11 items-center justify-center rounded-[10px] bg-brand px-6 text-sm font-medium text-white transition-colors hover:bg-brand-hover"
      >
        Ana səhifəyə qayıt
      </Link>
    </div>
  );
}
