import { describe, expect, it, vi } from "vitest";
import { withRequestLogging } from "./request";
import { TRACEPARENT_HEADER } from "./_trace";

const VALID_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01";

describe("withRequestLogging", () => {
  it("réutilise le trace-id du traceparent entrant et logge method/path/status/duration_ms", async () => {
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);

    const handler = vi.fn(async () => new Response("ok", { status: 201 }));
    const wrapped = withRequestLogging(handler);

    const request = new Request("http://localhost/api/user", {
      method: "POST",
      headers: { [TRACEPARENT_HEADER]: VALID_TRACEPARENT },
    });
    const response = await wrapped(request);

    expect(response.headers.get(TRACEPARENT_HEADER)).toBeNull();

    const line = write.mock.calls.at(-1)?.[0] as string;
    const payload = JSON.parse(line);
    expect(payload.message).toBe("requête traitée");
    expect(payload.trace_id).toBe("4bf92f3577b34da6a3ce929d0e0e4736");
    expect(payload).toMatchObject({ method: "POST", path: "/api/user", status: 201 });

    write.mockRestore();
  });

  it("génère un nouveau trace_id quand le traceparent est absent", async () => {
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);

    const handler = vi.fn(async () => new Response("ok", { status: 200 }));
    const wrapped = withRequestLogging(handler);
    const request = new Request("http://localhost/api/user");

    await wrapped(request);

    const line = write.mock.calls.at(-1)?.[0] as string;
    const payload = JSON.parse(line);
    expect(typeof payload.trace_id).toBe("string");
    expect(payload.trace_id).toHaveLength(32);

    write.mockRestore();
  });

  it("génère un nouveau trace_id quand le traceparent est malformé", async () => {
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);

    const handler = vi.fn(async () => new Response("ok", { status: 200 }));
    const wrapped = withRequestLogging(handler);
    const request = new Request("http://localhost/api/user", {
      headers: { [TRACEPARENT_HEADER]: "00-not-hex-at-all" },
    });

    await wrapped(request);

    const line = write.mock.calls.at(-1)?.[0] as string;
    const payload = JSON.parse(line);
    expect(typeof payload.trace_id).toBe("string");
    expect(payload.trace_id).not.toBe("not-hex-at-all");

    write.mockRestore();
  });

  it("génère un trace_id et logge quand même en cas d'erreur du handler, sans header sur la réponse", async () => {
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);

    const handler = vi.fn(async () => {
      throw new Error("boom");
    });
    const wrapped = withRequestLogging(handler);
    const request = new Request("http://localhost/api/user");

    await expect(wrapped(request)).rejects.toThrow("boom");

    const line = write.mock.calls.at(-1)?.[0] as string;
    const payload = JSON.parse(line);
    expect(payload.status).toBe(500);
    expect(typeof payload.trace_id).toBe("string");

    write.mockRestore();
  });
});
