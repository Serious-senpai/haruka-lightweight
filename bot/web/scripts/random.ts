namespace random {
    export function randInt(min: number, max: number): number {
        min = Math.ceil(min);
        max = Math.floor(max);
        return Math.floor(Math.random() * (max - min) + min);
    }

    export function choice<T>(...args: T[]): T {
        return args[randInt(0, args.length)];
    }
}
