import { describe, expect, it, vi } from "vitest";
import { trace } from "@opentelemetry/api";
import { configure, logger } from "./index";

const tracer = trace.getTracer("test");

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
    expect(payload.trace_id).toBeNull();
    expect(payload.span_id).toBeNull();

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

  it("trace_id/span_id proviennent du span OTel actif", () => {
    configure({ service: "test-service" });
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);

    tracer.startActiveSpan("test-span", (span) => {
      logger.info("hello");
      const spanContext = span.spanContext();

      const line = write.mock.calls.at(-1)?.[0] as string;
      const payload = JSON.parse(line);

      expect(payload.trace_id).toBe(spanContext.traceId);
      expect(payload.span_id).toBe(spanContext.spanId);

      span.end();
    });

    write.mockRestore();
  });
});
