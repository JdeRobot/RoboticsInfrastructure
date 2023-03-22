export default class TightDecoder {
    _ctl: any;
    _filter: any;
    _numColors: number;
    _palette: Uint8Array;
    _len: number;
    _zlibs: Inflator[];
    decodeRect(x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): boolean | void;
    _fillRect(x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): boolean;
    _jpegRect(x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): boolean;
    _pngRect(x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): void;
    _basicRect(ctl: any, x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): boolean | void;
    _copyFilter(streamId: any, x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): boolean;
    _paletteFilter(streamId: any, x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): boolean;
    _monoRect(x: any, y: any, width: any, height: any, data: any, palette: any, display: any): void;
    _paletteRect(x: any, y: any, width: any, height: any, data: any, palette: any, display: any): void;
    _gradientFilter(streamId: any, x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): void;
    _readData(sock: any): any;
    _getScratchBuffer(size: any): Uint8Array;
    _scratchBuffer: Uint8Array | undefined;
}
import Inflator from "../inflator.js";
