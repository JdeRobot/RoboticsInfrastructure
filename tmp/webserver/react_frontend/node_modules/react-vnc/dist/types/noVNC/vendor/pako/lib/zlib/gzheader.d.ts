export default function GZheader(): void;
export default class GZheader {
    text: number;
    time: number;
    xflags: number;
    os: number;
    extra: any;
    extra_len: number;
    name: string;
    comment: string;
    hcrc: number;
    done: boolean;
}
