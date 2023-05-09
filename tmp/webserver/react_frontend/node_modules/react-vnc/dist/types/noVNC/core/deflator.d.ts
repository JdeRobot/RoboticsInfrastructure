export default class Deflator {
    strm: ZStream;
    chunkSize: number;
    outputBuffer: Uint8Array;
    windowBits: number;
    deflate(inData: any): Uint8Array;
}
import ZStream from "../vendor/pako/lib/zlib/zstream.js";
