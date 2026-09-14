import {components} from "../models";

export class PoolAPIClient {
    private readonly apiUrl
    private readonly apiKey

    constructor(apiUrl: string, apiKey?: string) {
        this.apiUrl = apiUrl;
        this.apiKey = apiKey;
    }


    /**
     * Statistiques instantanées d'une pool
     * @param address Adresse de la pool
     */
    async getPoolStats(address: string): Promise<components["schemas"]["PoolStats"]> {
        return await fetch(`${this.apiUrl}/api/stats/${address}`).then((res) => res.json());
    }


}

