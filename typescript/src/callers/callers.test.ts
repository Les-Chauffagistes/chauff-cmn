import { afterEach, describe, expect, it, vi } from "vitest";
import { BitcoinAPIClient } from "./bitcoin";
import { HistoryAPIClient } from "./histories";

function mockFetch(body: unknown, status = 200) {
    const fn = vi.fn().mockResolvedValue(
        new Response(typeof body === "string" ? body : JSON.stringify(body), { status }),
    );
    vi.stubGlobal("fetch", fn);
    return fn;
}

afterEach(() => vi.unstubAllGlobals());

describe("BitcoinAPIClient.getBtcBlockReward", () => {
    const client = new BitcoinAPIClient("http://btc");

    it("sans paramètre : URL inchangée", async () => {
        const fn = mockFetch(3.125);
        expect(await client.getBtcBlockReward()).toBe(3.125);
        expect(fn).toHaveBeenCalledWith("http://btc/v1/bitcoin-block-reward");
    });

    it("avec une hauteur", async () => {
        const fn = mockFetch(6.25);
        expect(await client.getBtcBlockReward(839999)).toBe(6.25);
        expect(fn).toHaveBeenCalledWith("http://btc/v1/bitcoin-block-reward?height=839999");
    });

    it("avec une date ISO (le + est encodé)", async () => {
        const fn = mockFetch(3.125);
        await client.getBtcBlockReward("2026-11-04T18:09:23+01:00");
        expect(fn).toHaveBeenCalledWith("http://btc/v1/bitcoin-block-reward?at=2026-11-04T18%3A09%3A23%2B01%3A00");
    });

    it("avec un objet Date", async () => {
        const fn = mockFetch(3.125);
        await client.getBtcBlockReward(new Date("2026-11-04T17:09:23Z"));
        expect(fn).toHaveBeenCalledWith("http://btc/v1/bitcoin-block-reward?at=2026-11-04T17%3A09%3A23.000Z");
    });

    it("lève sur une réponse non 2xx", async () => {
        mockFetch({ error: "at must be a valid ISO 8601 date" }, 400);
        await expect(client.getBtcBlockReward("nope")).rejects.toThrow(/400/);
    });
});

describe("HistoryAPIClient.getPoolDistributionAt", () => {
    const client = new HistoryAPIClient("http://hist");
    const payload = [{ workername: "asic1", part: 1, sampled_at: "2026-11-04T16:59:23+00:00" }];

    it("appelle la route avec at encodé", async () => {
        const fn = mockFetch(payload);
        expect(await client.getPoolDistributionAt("bc1qabc", "2026-11-04T17:09:23Z")).toEqual(payload);
        expect(fn).toHaveBeenCalledWith("http://hist/v1/bc1qabc/distribution?at=2026-11-04T17%3A09%3A23Z");
    });

    it("accepte un objet Date", async () => {
        const fn = mockFetch(payload);
        await client.getPoolDistributionAt("bc1qabc", new Date("2026-11-04T17:09:23Z"));
        expect(fn.mock.calls[0][0]).toContain("at=2026-11-04T17%3A09%3A23.000Z");
    });

    it("lève sur 404", async () => {
        mockFetch({ error: "no data at or before the requested date" }, 404);
        await expect(client.getPoolDistributionAt("bc1qabc", "2020-01-01T00:00:00Z")).rejects.toThrow(/404/);
    });
});
