/// <reference path="../discord/users.ts" />


namespace tic_tac_toe {
    export class Player {
        public readonly user: discord.User | null;

        private constructor(user: discord.User | null) {
            this.user = user;
        }

        public get displayName(): string {
            if (this.user !== null) return this.user.name;
            return "Guest";
        }

        public static fromObject(data: object): Player {
            return new Player(data["user"] !== null ? discord.User.fromObject(data["user"]) : null);
        }
    }
}