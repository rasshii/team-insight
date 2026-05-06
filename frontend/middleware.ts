import type { NextRequest } from "next/server"
import { NextResponse } from "next/server"

// 認証が必要なパスのパターン
const protectedPaths = ["/dashboard", "/projects", "/team", "/organization", "/admin", "/settings"]

// 認証不要なパス（公開ページ）
const publicPaths = [
  "/",
  "/auth/login",
  "/auth/accept-invitation",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/about",
  "/contact",
]

interface JwtPayload {
  exp?: number
  sub?: string
  type?: string
}

/**
 * JWT を base64url 部分から payload を取り出して有効期限を判定する。
 * 署名検証は backend が API リクエスト時に必ず行うため、middleware では
 * 「JWT が存在し、明らかに期限切れでない」かのみを確認する (Edge runtime
 * での同期 fetch を避ける目的)。
 */
function isJwtValid(token: string): boolean {
  try {
    const parts = token.split(".")
    if (parts.length !== 3) return false
    const padded = parts[1].replace(/-/g, "+").replace(/_/g, "/")
    const payload = JSON.parse(atob(padded)) as JwtPayload
    if (typeof payload.exp !== "number") return false
    return payload.exp * 1000 > Date.now()
  } catch {
    return false
  }
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // 公開パスへのアクセスは常に許可
  const isPublicPath = publicPaths.some((path) => pathname === path || pathname.startsWith(`${path}/`))
  if (isPublicPath) {
    return NextResponse.next()
  }

  // 保護されたパスかどうかを確認
  const isProtectedPath = protectedPaths.some((path) => pathname.startsWith(path))
  if (!isProtectedPath) {
    return NextResponse.next()
  }

  const authToken = request.cookies.get("auth_token")?.value

  if (!authToken || !isJwtValid(authToken)) {
    const url = new URL("/auth/login", request.url)
    url.searchParams.set("from", pathname)
    const response = NextResponse.redirect(url)
    if (authToken) response.cookies.delete("auth_token")
    return response
  }

  return NextResponse.next()
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
}
