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

    /**
     * Répartition du travail des workers d'une pool à une date donnée (ex. date de minage d'un block).
     * Les `part` sont des fractions 0-1 dont la somme vaut 1.
     * Lève une Error si la réponse n'est pas 2xx : 400 (date invalide/sans fuseau/future),
     * 404 (aucun échantillon à cette date : données purgées ou trou de collecte).
     * @param poolAddress Adresse de la pool
     * @param at Date ISO 8601 avec fuseau (string ou Date)
     */
    async getPoolDistributionAt(poolAddress: string, at: string | Date): Promise<components["schemas"]["PoolDistributionAtElement"][]> {
        const iso = at instanceof Date ? at.toISOString() : at;
        const res = await fetch(`${this.apiUrl}/v1/${encodeURIComponent(poolAddress)}/distribution?at=${encodeURIComponent(iso)}`);
        if (!res.ok) {
            throw new Error(`history-server distribution request failed: ${res.status} ${await res.text()}`);
        }
        return await res.json();
    }
}
