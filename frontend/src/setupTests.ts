import "@testing-library/jest-dom";

// Next.js Routerのモック
jest.mock("next/navigation", () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
    };
  },
  useSearchParams() {
    return new URLSearchParams();
  },
  usePathname() {
    return "";
  },
}));

// Next.js Linkのモック
jest.mock("next/link", () => {
  const React = require("react");
  return ({ children, href }: { children: React.ReactNode; href: string }) => {
    return React.createElement("a", { href }, children);
  };
});
