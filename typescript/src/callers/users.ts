import {logger} from "../logging";

export type AuthUser = {
    id: string;
    pseudo: string;
};

export class UserAPIClient {
    private readonly apiUrl

    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }


    async getUserById(userId: number | string | bigint): Promise<AuthUser | null> {
        const response = await fetch(`${this.apiUrl}/user/${userId}`);
        if (response.status === 404) return null;
        if (!response.ok) throw new Error(`Unable to fetch user ${userId}: ${response.status}`);
        return response.json();
    }


    async getUsersByIds(
        userIds: readonly (number | string | bigint)[],
    ): Promise<AuthUser[]> {
        if (userIds.length === 0) return [];

        const response = await fetch(`${this.apiUrl}/users/by-ids`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            // `JSON.stringify` lève sur un BigInt
            body: JSON.stringify({ids: userIds.map(String)}),
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error(`Unable to fetch users: ${response.status}`);
        }

        return response.json();
    }

    async getPseudosByUserId(
        userIds: readonly (number | string | bigint)[],
    ): Promise<Map<string, string>> {
        const uniqueIds = [...new Set(userIds.map(String))];
        if (uniqueIds.length === 0) return new Map();

        try {
            const users = await this.getUsersByIds(uniqueIds);
            return new Map(users.map((user) => [String(user.id), user.pseudo]));
        } catch (error) {
            logger.error("[users] API unreachable", error);
            return new Map();
        }
    }
}