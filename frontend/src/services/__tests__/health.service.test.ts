import axios from "axios";
import { healthService, HealthStatus, HealthCheckError } from "../health.service";

// axiosをモック化
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// 環境変数のモック
jest.mock("@/config/env", () => ({
  env: {
    get: jest.fn().mockReturnValue("http://localhost:8000"),
  },
}));

describe("HealthService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("checkHealth", () => {
    it("正常なレスポンスを処理できる", async () => {
      // モックレスポンス
      const mockResponse: HealthStatus = {
        status: "healthy",
        services: {
          api: "healthy",
          database: "healthy",
          redis: "healthy",
        },
        message: "Team Insight API is running",
        timestamp: "2024-01-01T00:00:00Z",
      };

      mockedAxios.get.mockResolvedValueOnce({
        data: mockResponse,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {} as any,
      });

      // テスト実行
      const result = await healthService.checkHealth();

      // 検証
      expect(mockedAxios.get).toHaveBeenCalledWith(
        "http://localhost:8000/health",
        { timeout: 5000 }
      );
      expect(result).toEqual(mockResponse);
    });

    it("Redisが異常な場合のレスポンスを処理できる", async () => {
      // モックレスポンス
      const mockResponse: HealthStatus = {
        status: "unhealthy",
        services: {
          api: "healthy",
          database: "healthy",
          redis: "unhealthy",
        },
        message: "Team Insight API is running",
        timestamp: "2024-01-01T00:00:00Z",
      };

      mockedAxios.get.mockResolvedValueOnce({
        data: mockResponse,
        status: 200,
        statusText: "OK",
        headers: {},
        config: {} as any,
      });

      // テスト実行
      const result = await healthService.checkHealth();

      // 検証
      expect(result).toEqual(mockResponse);
      expect(result.status).toBe("unhealthy");
      expect(result.services.redis).toBe("unhealthy");
    });

    it("ネットワークエラーをHealthCheckError型に変換する", async () => {
      // axiosエラーのモック
      const axiosError = new Error("Network Error");
      (axiosError as any).isAxiosError = true;
      (axiosError as any).message = "Network Error";

      mockedAxios.get.mockRejectedValueOnce(axiosError);
      mockedAxios.isAxiosError = jest.fn(() => true) as any;

      // テスト実行とエラー検証
      await expect(healthService.checkHealth()).rejects.toEqual({
        error: "API_ERROR",
        message: "Network Error",
      } as HealthCheckError);
    });

    it("タイムアウトエラーを適切に処理する", async () => {
      // タイムアウトエラーのモック
      const timeoutError = new Error("timeout of 5000ms exceeded");
      (timeoutError as any).isAxiosError = true;
      (timeoutError as any).code = "ECONNABORTED";

      mockedAxios.get.mockRejectedValueOnce(timeoutError);
      mockedAxios.isAxiosError = jest.fn(() => true) as any;

      // テスト実行とエラー検証
      await expect(healthService.checkHealth()).rejects.toEqual({
        error: "API_ERROR",
        message: "timeout of 5000ms exceeded",
      } as HealthCheckError);
    });

    it("予期しないエラーを処理する", async () => {
      // 非axiosエラーのモック
      const unexpectedError = new Error("Unexpected error");

      mockedAxios.get.mockRejectedValueOnce(unexpectedError);
      mockedAxios.isAxiosError = jest.fn(() => false) as any;

      // テスト実行とエラー検証
      await expect(healthService.checkHealth()).rejects.toEqual({
        error: "UNKNOWN_ERROR",
        message: "予期しないエラーが発生しました",
      } as HealthCheckError);
    });
  });

  describe("isHealthy", () => {
    it("全てのサービスが正常な場合にtrueを返す", () => {
      const status: HealthStatus = {
        status: "healthy",
        services: {
          api: "healthy",
          database: "healthy",
          redis: "healthy",
        },
        message: "All services are running",
        timestamp: "2024-01-01T00:00:00Z",
      };

      expect(healthService.isHealthy(status)).toBe(true);
    });

    it("いずれかのサービスが異常な場合にfalseを返す", () => {
      const status: HealthStatus = {
        status: "unhealthy",
        services: {
          api: "healthy",
          database: "healthy",
          redis: "unhealthy",
        },
        message: "Some services are down",
        timestamp: "2024-01-01T00:00:00Z",
      };

      expect(healthService.isHealthy(status)).toBe(false);
    });

    it("APIが異常な場合にfalseを返す", () => {
      const status: HealthStatus = {
        status: "unhealthy",
        services: {
          api: "unhealthy",
          database: "healthy",
          redis: "healthy",
        },
        message: "API is down",
        timestamp: "2024-01-01T00:00:00Z",
      };

      expect(healthService.isHealthy(status)).toBe(false);
    });

    it("データベースが異常な場合にfalseを返す", () => {
      const status: HealthStatus = {
        status: "unhealthy",
        services: {
          api: "healthy",
          database: "unhealthy",
          redis: "healthy",
        },
        message: "Database is down",
        timestamp: "2024-01-01T00:00:00Z",
      };

      expect(healthService.isHealthy(status)).toBe(false);
    });
  });

  describe("getStatusMessage", () => {
    it("healthyステータスを日本語に変換する", () => {
      expect(healthService.getStatusMessage("healthy")).toBe("正常");
    });

    it("unhealthyステータスを日本語に変換する", () => {
      expect(healthService.getStatusMessage("unhealthy")).toBe("異常");
    });
  });

  describe("getErrorMessage", () => {
    it("API_ERRORを適切なメッセージに変換する", () => {
      const error: HealthCheckError = {
        error: "API_ERROR",
        message: "Connection failed",
      };

      expect(healthService.getErrorMessage(error)).toBe("APIサーバーに接続できません");
    });

    it("UNKNOWN_ERRORを適切なメッセージに変換する", () => {
      const error: HealthCheckError = {
        error: "UNKNOWN_ERROR",
        message: "Something went wrong",
      };

      expect(healthService.getErrorMessage(error)).toBe("システムエラーが発生しました");
    });

    it("未知のエラータイプの場合は元のメッセージを返す", () => {
      const error: HealthCheckError = {
        error: "CUSTOM_ERROR",
        message: "Custom error message",
      };

      expect(healthService.getErrorMessage(error)).toBe("Custom error message");
    });
  });
});
