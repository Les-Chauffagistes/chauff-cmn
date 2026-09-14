import { components } from "../models"


export class AuthClient {
    private readonly apiUrl

    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }


    async getMe(): Promise<components["schemas"]["User"] | null> {
        const res = await this.authFetch(`${this.apiUrl}/me`);
        if (!res.ok) return null;
        return res.json();
    }


    async authFetch(input: RequestInfo, init?: RequestInit) {
        let res = await fetch(input, {
            ...init,
            credentials: "include"
        });

        if (res.status === 401) {
            const refreshed = await this.refreshToken();
            if (!refreshed.ok) return res;

            res = await fetch(input, {
                ...init,
                credentials: "include"
            });
        }

        return res;
    }


    async refreshToken() {
        return await fetch(`${this.apiUrl}/refresh`, {credentials: "include", method: "POST"});
    }


    async logOut() {
        await fetch(`${this.apiUrl}/logout`, {
            method: "DELETE",
            credentials: "include",
            mode: "cors"
        })
    }
}