"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Button, ErrorState } from "@yenimenzil/ui";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";

export default function RootError({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const router = useRouter();

  React.useEffect(() => {
    console.error("[root-error]", error);
    // Could send to Sentry here
  }, [error]);

  return (
    <html lang="az">
      <head>
        <title>Xəta - YeniMenzil.az</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="robots" content="noindex" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var script = document.createElement('script');
                  script.src = 'https://cdn.tailwindcss.com';
                  document.head.appendChild(script);
                } catch (e) {}
              })();
            `
          }}
        />
      </head>
      <body className="bg-gray-50 min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <ErrorState
            variant="destructive"
            icon={
              <span className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-red-50 text-red-600">
                <AlertTriangle className="h-8 w-8" />
              </span>
            }
            title="Qlobal xəta baş verdi"
            description="Tətbiq yüklənərkən xəta baş verdi. Səhifəni yeniləyin."
            action={
              <div className="mt-5 flex justify-center gap-2">
                <Button onClick={reset} variant="primary">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Yenidən cəhd et
                </Button>
                <Button variant="secondary" onClick={() => router.push("/")}>
                  <Home className="h-4 w-4 mr-2" />
                  Ana səhifə
                </Button>
              </div>
            }
          />
        </div>
      </body>
    </html>
  );
}