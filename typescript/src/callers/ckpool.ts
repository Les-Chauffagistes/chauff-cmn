import {components} from "../models";

export class CKPoolAPIClient {
    private readonly apiUrl: string;

    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }

    async getPoolShareRepartition(address: string, window_days: number = 14): Promise<components["schemas"]["PoolDistributionElement"]> {
        return await fetch(`${this.apiUrl}/v1/distribution/${address}?window_days=${window_days}`).then((res) => res.json());
    }

}