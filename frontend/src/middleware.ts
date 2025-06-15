import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

// 認証が必要なパスのパターン
const protectedPaths = ["/dashboard", "/projects", "/team"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtectedPath = protectedPaths.some((path) =>
    pathname.startsWith(path)
  );

  // 認証状態を確認（実際の実装では、セッションやJWTトークンを確認）
  // const isAuthenticated = request.cookies.has("auth_token");
  const isAuthenticated = true;
  // 保護されたパスにアクセスしようとしているが、認証されていない場合
  if (isProtectedPath && !isAuthenticated) {
    const url = new URL("/auth/login", request.url);
    url.searchParams.set("from", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
