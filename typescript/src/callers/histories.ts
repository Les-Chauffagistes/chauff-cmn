import {components} from "../models";


export class HistoryAPIClient {
    private readonly apiUrl

    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }

    /**
     * Historique des statistiques d'un unique worker au sein d'une pool
     * @param poolAddress Adresse de la pool
     * @param workerName Nom du worker
     * @param period daily ou forever.
     * - Si daily: 1 point toutes les 30 mins via hypertable
     * - Si forever: 1 point tous les jours via hypertable
     */
    async getWorkerStatsHistory(poolAddress: string, workerName: string, period: "daily" | "forever"): Promise<components["schemas"]["WorkerStatsHistory"][]> {
        return await fetch(`${this.apiUrl}/v1/${poolAddress}/worker/${workerName}/${period}`).then((res) => res.json());
    }

    /**
     * Historique sur 30j du hashrate 1h, du hashrate 24h et du poids du pool
     * @param poolAddress Adresse de la pool
     */
    async getPoolStatsHistory(poolAddress: string): Promise<components["schemas"]["PoolStatsHistory"][]> {
        return await fetch(`${this.apiUrl}/v1/${poolAddress}/pool`).then((res) => res.json());
    }

    /**
     * Poids de tous les workers d'une pool
     * @param poolAddress Adresse de la pool
     */
    async getPoolWeight(poolAddress: string): Promise<components["schemas"]["WorkersWeights"][]> {
        return await fetch(`${this.apiUrl}/v1/${poolAddress}/weights`).then((res) => res.json());
    }
}