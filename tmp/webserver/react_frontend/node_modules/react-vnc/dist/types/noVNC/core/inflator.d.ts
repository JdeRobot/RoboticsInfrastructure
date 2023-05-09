export default class Inflate {
    strm: ZStream;
    chunkSize: number;
    windowBits: number;
    setInput(data: any): void;
    inflate(expected: any): Uint8Array;
    reset(): void;
}
import ZStream from "../vendor/pako/lib/zlib/zstream.js";
