import {tracedFetch} from "../logging/fetch";

type TransferParams = {
    fromUserId: number;
    toUserId: number;
    amount: number;
    currency: string;
    idempotencyKey: string;
    reason: string;
};

type burnParams = {
    userId: number,
    currency: string,
    amount: number,
    reason: string,
    idempotencyKey: string
}

export class InsufficientCoinsError extends Error {
}

export class WalletAPIClient {
    private readonly apiUrl
    private readonly apiKey

    constructor(apiUrl: string, apiKey: string) {
        this.apiUrl = apiUrl;
        this.apiKey = apiKey;
    }

    async getUserCoins(access_token: string, currency: string): Promise<{ "balance": number }> {
        return await (tracedFetch(`${this.apiUrl}/balance?currency=${currency}`, {
            headers: {
                "Authorization": access_token,
                "X-Api-Key": this.apiKey,
            }
        }).then(res => res.json()));
    }

    async transferCoins(params: TransferParams): Promise<void> {
        let resp: Response;
        try {
            resp = await tracedFetch(`${this.apiUrl}/transfer`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Api-Key": this.apiKey,
                },
                body: JSON.stringify({
                    amount: params.amount,
                    currency: params.currency,
                    fromUserId: params.fromUserId,
                    toUserId: params.toUserId,
                    reason: params.reason,
                    idempotencyKey: params.idempotencyKey,
                }),
                signal: AbortSignal.timeout(5_000),
            });
        } catch (e) {
            throw new Error("Transfer request failed", {cause: e});
        }

        if (resp.status === 204) return;
        if (resp.status === 400) throw new InsufficientCoinsError();
        throw new Error(`Unexpected wallet response: ${resp.status}`);
    }

    async getSystemAccountBalance(userId: number, currency: string): Promise<number> {
        const resp = await tracedFetch(
            `${this.apiUrl}/internal/balance?currency=${currency}&userId=${userId}`,
            {headers: {"X-Api-Key": this.apiKey}},
        );
        if (!resp.ok) throw new Error(`Unexpected wallet response: ${resp.status}`);
        const {balance} = await resp.json();
        return balance;
    }


    async burnUserCoins({params}: { params: burnParams }): Promise<void> {
        let resp: Response;
        try {
            resp = await tracedFetch(`${this.apiUrl}/v2/burn`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-Api-Key": this.apiKey,
                },
                body: JSON.stringify({
                    userId: params.userId,
                    currency: params.currency,
                    amount: params.amount,
                    reason: params.reason,
                    idempotencyKey: params.idempotencyKey,
                }),
                signal: AbortSignal.timeout(5_000),
            });
        } catch (e) {
            throw new Error("Burn request failed", {cause: e});
        }

        if (resp.status === 204) return;
        if (resp.status === 400) throw new InsufficientCoinsError();
        throw new Error(`Unexpected wallet response: ${resp.status}`);
    }

}