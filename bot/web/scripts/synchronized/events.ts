namespace synchronized {
    export class Event {
        private readonly resolvers: Array<(value: void | PromiseLike<void>) => void> = new Array();
        private flag: boolean = false;

        public get isSet(): boolean {
            return this.flag;
        }

        public set(): void {
            if (this.flag) return;
            this.flag = true;
            this.resolvers.forEach((resolver) => resolver());
            this.resolvers.length = 0;
        }

        public clear(): void {
            this.flag = false;
        }

        public async wait(): Promise<void> {
            if (!this.flag) {
                const waiter = new Promise<void>((resolve) => this.resolvers.push(resolve));
                await waiter;
            }
        }
    }
}