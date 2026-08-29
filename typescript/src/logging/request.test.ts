import { describe, expect, it, vi } from "vitest";
import { withRequestLogging } from "./request";
import { REQUEST_ID_HEADER } from "./_correlation";

describe("withRequestLogging", () => {
  it("propage l'id de corrélation entrant et logge method/path/status/duration_ms", async () => {
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);

    const handler = vi.fn(async () => new Response("ok", { status: 201 }));
    const wrapped = withRequestLogging(handler);

    const request = new Request("http://localhost/api/user", {
      method: "POST",
      headers: { [REQUEST_ID_HEADER]: "incoming-id" },
    });
    const response = await wrapped(request);

    expect(response.headers.get(REQUEST_ID_HEADER)).toBe("incoming-id");

    const line = write.mock.calls.at(-1)?.[0] as string;
    const payload = JSON.parse(line);
    expect(payload.message).toBe("requête traitée");
    expect(payload.correlation_id).toBe("incoming-id");
    expect(payload.meta).toMatchObject({ method: "POST", path: "/api/user", status: 201 });

    write.mockRestore();
  });

  it("génère un id de corrélation et logge quand même en cas d'erreur du handler", async () => {
    const write = vi.spyOn(process.stdout, "write").mockImplementation(() => true);

    const handler = vi.fn(async () => {
      throw new Error("boom");
    });
    const wrapped = withRequestLogging(handler);
    const request = new Request("http://localhost/api/user");

    await expect(wrapped(request)).rejects.toThrow("boom");

    const line = write.mock.calls.at(-1)?.[0] as string;
    const payload = JSON.parse(line);
    expect(payload.meta.status).toBe(500);
    expect(typeof payload.correlation_id).toBe("string");

    write.mockRestore();
  });
});
