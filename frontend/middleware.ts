import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { env } from "@/config/env";

// 認証が必要なパスのパターン
const protectedPaths = ["/dashboard", "/projects", "/team", "/organization"];

// 認証不要なパス（公開ページ）
const publicPaths = ["/", "/auth/login", "/auth/callback", "/about", "/contact"];

/**
 * 認証トークンの有効性をバックエンドAPIで確認
 */
async function verifyAuthToken(token: string): Promise<boolean> {
  try {
    const response = await fetch(`${env.get("NEXT_PUBLIC_API_URL")}/api/v1/auth/verify`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    return response.ok;
  } catch (error) {
    console.error("認証確認エラー:", error);
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // 公開パスへのアクセスは常に許可
  const isPublicPath = publicPaths.some((path) => pathname === path || pathname.startsWith(`${path}/`));
  if (isPublicPath) {
    return NextResponse.next();
  }

  // 保護されたパスかどうかを確認
  const isProtectedPath = protectedPaths.some((path) =>
    pathname.startsWith(path)
  );

  // 保護されたパスへのアクセスの場合、認証チェック
  if (isProtectedPath) {
    const authToken = request.cookies.get("auth_token")?.value;

    if (!authToken) {
      // 認証トークンが存在しない場合はログインページへリダイレクト
      const url = new URL("/auth/login", request.url);
      url.searchParams.set("from", pathname);
      return NextResponse.redirect(url);
    }

    // バックエンドAPIでトークンの有効性を確認
    const isValidToken = await verifyAuthToken(authToken);
    
    if (!isValidToken) {
      // トークンが無効な場合はログインページへリダイレクト
      const response = NextResponse.redirect(
        new URL("/auth/login", request.url)
      );
      // 無効なトークンを削除
      response.cookies.delete("auth_token");
      return response;
    }
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
     * - public folder
     */
    "/((?!api|_next/static|_next/image|favicon.ico|public).*)",
  ],
};