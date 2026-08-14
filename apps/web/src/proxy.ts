import { NextResponse, type NextRequest } from "next/server";

const MAINTENANCE_ENABLED = process.env.NEXT_PUBLIC_MAINTENANCE_MODE === "1";

const ALLOWED_PATHS = [
  "/maintenance",
  "/api",
  "/_next",
  "/favicon.ico",
  "/robots.txt",
  "/sitemap.xml"
];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (!MAINTENANCE_ENABLED) {
    return NextResponse.next();
  }

  if (ALLOWED_PATHS.some((path) => pathname.startsWith(path))) {
    return NextResponse.next();
  }

  if (pathname !== "/maintenance") {
    return NextResponse.redirect(new URL("/maintenance", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|images).*)"]
};
