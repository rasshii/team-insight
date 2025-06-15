import { jwtVerify } from "jose";
import { NextRequest, NextResponse } from "next/server";

// 認証が必要なパス
const protectedPaths = ["/dashboard", "/projects", "/team"];

// JWTの検証関数
async function verifyAuthToken(token: string): Promise<boolean> {
  try {
    // 環境変数からシークレットキーを取得
    const secret = new TextEncoder().encode(
      process.env.JWT_SECRET_KEY || "your-secret-key-here"
    );

    // JWTを検証
    await jwtVerify(token, secret);
    return true;
  } catch (error) {
    console.error("JWT検証エラー:", error);
    return false;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtectedPath = protectedPaths.some((path) =>
    pathname.startsWith(path)
  );

  // 保護されたパスへのアクセスの場合のみ認証チェック
  if (isProtectedPath) {
    const authToken = request.cookies.get("auth_token")?.value;

    if (!authToken) {
      // 認証トークンが存在しない場合はログインページへリダイレクト
      const url = new URL("/auth/login", request.url);
      url.searchParams.set("from", pathname);
      return NextResponse.redirect(url);
    }

    // トークンの検証
    const isValid = await verifyAuthToken(authToken);
    if (!isValid) {
      // トークンが無効な場合はログインページへリダイレクト
      const url = new URL("/auth/login", request.url);
      url.searchParams.set("from", pathname);
      return NextResponse.redirect(url);
    }
  }

  return NextResponse.next();
}

// ミドルウェアの設定
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
