namespace collections {
    class _DequeNode<T>{
        public readonly value: T | null;
        public previous: _DequeNode<T> | null;
        public next: _DequeNode<T> | null;

        public readonly isHead: boolean;

        public constructor(value: T | null, previous: _DequeNode<T> | null, next: _DequeNode<T> | null, isHead: boolean = false) {
            this.value = value;
            this.previous = previous;
            this.next = next;
            this.isHead = isHead;
        }
    }

    export class Deque<T> {
        public readonly head: _DequeNode<T> = new _DequeNode<T>(null, null, null, true);
        public tail: _DequeNode<T> = this.head;

        private _length: number = 0;

        public constructor(array?: Array<T>) {
            array?.forEach((e) => this.pushRight(e));
        }

        public get length(): number {
            return this._length;
        }

        public get isEmpty(): boolean {
            return this._length === 0;
        }

        public pushLeft(value: T): void {
            const next = this.head.next,
                insert = new _DequeNode<T>(value, this.head, next);

            this.head.next = insert;
            if (next !== null) next.previous = insert;

            this._length++;
        }

        public pushRight(value: T): void {
            const tail = this.tail,
                insert = new _DequeNode<T>(value, tail, null);

            this.tail = tail.next = insert;

            this._length++;
        }

        public popLeft(): T {
            const pop = this.head.next;
            if (pop === null) throw RangeError("Empty deque");

            const next = pop.next;
            this.head.next = next;
            if (next !== null) next.previous = this.head;

            this._length--;
            return pop.value!;
        }

        public popRight(): T {
            const pop = this.tail;
            if (pop.isHead) throw RangeError("Empty deque");

            this.tail = pop.previous!;
            this.tail.next = null;

            this._length--;
            return pop.value!;
        }
    }
}