namespace collections {
    export class Pair<T1, T2>{
        public first: T1;
        public second: T2;

        public constructor(first: T1, second: T2) {
            this.first = first;
            this.second = second;
        }
    }
}