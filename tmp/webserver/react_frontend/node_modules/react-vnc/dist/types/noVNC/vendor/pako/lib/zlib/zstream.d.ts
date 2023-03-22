export default function ZStream(): void;
export default class ZStream {
    input: any;
    next_in: number;
    avail_in: number;
    total_in: number;
    output: any;
    next_out: number;
    avail_out: number;
    total_out: number;
    msg: string;
    state: any;
    data_type: number;
    adler: number;
}
