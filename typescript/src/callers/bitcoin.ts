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
     * Récompense de block du réseau Bitcoin
     * @returns number
     */
    async getBtcBlockReward(): Promise<number> {
        return await fetch(`${this.apiUrl}/v1/bitcoin-block-reward`).then((res) => res.json());
    }
}