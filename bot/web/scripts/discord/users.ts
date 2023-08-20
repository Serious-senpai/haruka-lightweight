namespace discord {
    export class User {
        public readonly id: bigint;
        public readonly name: string;
        public readonly avatar: Asset;

        private constructor(id: bigint, name: string, avatar: Asset) {
            this.id = id;
            this.name = name;
            this.avatar = avatar;
        }

        public static fromObject(data: object): User {
            return new User(data["id"], data["name"], Asset.fromObject(data["avatar"]));
        }
    }
}