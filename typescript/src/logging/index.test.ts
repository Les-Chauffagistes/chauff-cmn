import { describe, expect, it, vi } from "vitest";
import { configure, logger } from "./index";

describe("logger", () => {
  it("emits a JSON line with the configured service name", () => {
    configure({ service: "test-service" });
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);

    logger.info("hello");

    const line = write.mock.calls[0][0] as string;
    const payload = JSON.parse(line);

    expect(payload.service).toBe("test-service");
    expect(payload.message).toBe("hello");
    expect(payload.level).toBe("INFO");
    expect(payload.correlation_id).toBeNull();

    write.mockRestore();
  });

  it("extrait message et stack d'une Error au lieu de sérialiser en '{}'", () => {
    configure({ service: "test-service" });
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);

    logger.error(new Error("boom"));

    const line = write.mock.calls[0][0] as string;
    const payload = JSON.parse(line);

    expect(payload.message).toBe("boom");
    expect(payload.exception).toContain("Error: boom");

    write.mockRestore();
  });
});
