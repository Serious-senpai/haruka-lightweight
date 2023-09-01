/// <reference path="../collections/deque.ts" />


namespace synchronized {
    export class Lock {
        private readonly resolvers: collections.Deque<(value: void | PromiseLike<void>) => void> = new collections.Deque();
        private locked: boolean = false;

        public get isLocked(): boolean {
            return this.locked;
        }

        public async acquire(): Promise<void> {
            if (!this.locked && this.resolvers.length === 0) {
                this.locked = true;
            } else {
                const waiter = new Promise<void>((resolve) => this.resolvers.pushRight(resolve));
                await waiter;
            }
        }

        public release(): void {
            if (this.locked) {
                if (this.resolvers.length === 0) {
                    this.locked = false;
                } else {
                    const resolver = this.resolvers.popLeft();
                    resolver!();
                }
            }
        }

        public async run<T>(func: () => Promise<T>): Promise<T> {
            await this.acquire();
            try {
                return await func();
            } finally {
                this.release();
            }
        }
    }
}