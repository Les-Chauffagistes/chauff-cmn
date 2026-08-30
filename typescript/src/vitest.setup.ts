import { beforeEach } from "vitest";
import { InMemorySpanExporter } from "@opentelemetry/sdk-trace-base";
import { setupTracing } from "./tracing";

export const testSpanExporter = new InMemorySpanExporter();
setupTracing({ service: "test-service", exporter: testSpanExporter });

beforeEach(() => {
  testSpanExporter.reset();
});
