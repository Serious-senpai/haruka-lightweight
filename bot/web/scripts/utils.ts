function concatCSSStyles(styles: object): string {
    var result: string = "";
    for (var key of Object.keys(styles)) {
        if (styles[key] !== undefined) {
            result += `${key}: ${styles[key]};`;
        }
    }

    return result;
}


function captialize(value: string): string {
    var result: string = "";
    for (var index = 0; index < value.length; index++) {
        if (index === 0 || value[index - 1] === " ") {
            result += value[index].toUpperCase();
        } else {
            result += value[index];
        }
    }

    return result;
}


function construct2DArray<T>(row: number, column: number, value: T): Array<Array<T>> {
    const result: Array<Array<T>> = new Array<Array<T>>();
    for (var r = 0; r < row; r++) {
        const arr = new Array<T>();
        arr.length = column;
        arr.fill(value, 0, column);

        result.push(arr);
    }

    return result;
}


// https://stackoverflow.com/a/12034334
var entityMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "\'": "&#39;",
    "/": "&#x2F;",
    "`": "&#x60;",
    "=": "&#x3D;",
};


function escapeHtml(string) {
    return String(string).replace(/[&<>"'`=\/]/g, function (s) {
        return entityMap[s];
    });
}


function splitPath(path: string): Array<string> {
    return path.split("/").filter((value) => value.length > 0);
}