"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Button, ErrorState } from "@yenimenzil/ui";
import { WifiOff } from "lucide-react";

export default function GlobalError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  React.useEffect(() => {
    console.error("[global-error]", error);
  }, [error]);

  return (
    <div className="mx-auto max-w-xl px-4 py-20">
      <ErrorState
        variant="destructive"
        icon={
          <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-600">
            <WifiOff className="h-7 w-7" />
          </span>
        }
        title="Nəsə səhv getdi"
        description="Gözlənilməz xəta baş verdi. Yenidən cəhd edin və ya ana səhifəyə qayıdın."
        action={
          <div className="mt-5 flex justify-center gap-2">
            <Button onClick={reset} variant="primary">
              Yenidən cəhd et
            </Button>
            <Button variant="secondary" onClick={() => router.push("/")}>
              Ana səhifə
            </Button>
          </div>
        }
      />
    </div>
  );
}
