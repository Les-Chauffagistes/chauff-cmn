import {components} from "../models";

export class BitcoinAPIClient {
    private readonly apiUrl

    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }

    /**
     * Prix du Bitcoin
     * @returns BitcoinPrice
     */
    async getBtcPrice(): Promise<components["schemas"]["BitcoinPrice"]> {
        return await fetch(`${this.apiUrl}/v1/bitcoin-price`).then((res) => res.json());
    }

    /**
     * Récompense de block (subsidy, SANS les frais de transaction) du réseau Bitcoin, en BTC.
     * @param at Optionnel. Sans paramètre : récompense du block courant.
     * - number : hauteur de block (calcul direct depuis les halvings, sans appel au noeud)
     * - string : date ISO 8601 avec fuseau (résolue en hauteur via le noeud Bitcoin)
     * Lève une Error si la réponse n'est pas 2xx lorsque `at` est fourni.
     * @returns number
     */
    async getBtcBlockReward(at?: string | number | Date): Promise<number> {
        if (at === undefined) {
            return await fetch(`${this.apiUrl}/v1/bitcoin-block-reward`).then((res) => res.json());
        }
        const query = typeof at === "number"
            ? `height=${encodeURIComponent(String(at))}`
            : `at=${encodeURIComponent(at instanceof Date ? at.toISOString() : at)}`;
        const res = await fetch(`${this.apiUrl}/v1/bitcoin-block-reward?${query}`);
        if (!res.ok) {
            throw new Error(`bitcoin-service block reward request failed: ${res.status} ${await res.text()}`);
        }
        return await res.json();
    }
}
