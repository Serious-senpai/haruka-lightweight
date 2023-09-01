namespace discord {
    export class Asset {
        public readonly key: string;
        public readonly url: string;

        private constructor(key: string, url: string) {
            this.key = key;
            this.url = url;
        }

        public static fromObject(data: object): Asset {
            return new Asset(data["key"], data["url"]);
        }
    }
}