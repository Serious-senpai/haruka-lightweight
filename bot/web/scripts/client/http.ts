/// <reference path="authorization.ts" />


namespace client {
    export class HTTPException extends Error { }

    class HTTP {
        public get(url: string, datatype?: string): JQuery.jqXHR<any> {
            return $.get(
                {
                    "url": url,
                    "headers": authorization.header,
                    "dataType": datatype,
                }
            );
        }
    }

    export const http = new HTTP();
}