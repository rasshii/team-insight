/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // 一時的に無効化（本番環境では有効にすること）
  swcMinify: true,
  output: "standalone",
  poweredByHeader: false,
  generateBuildId: async () => {
    return "build-" + Date.now();
  },
  experimental: {
    serverComponentsExternalPackages: ["react-redux"],
  },
  // 開発時のリライトルール
  // フロントエンドからのAPIアクセスをlocalhost（Nginx）経由に統一
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost/api/:path*',
      },
    ]
  },
  staticPageGenerationTimeout: 0,
  // 開発環境でのWebSocket設定
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
