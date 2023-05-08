export default class JPEGDecoder {
    _quantTables: any[];
    _huffmanTables: any[];
    _cachedQuantTables: any[];
    _cachedHuffmanTables: any[];
    _jpegLength: number;
    _segments: any[];
    decodeRect(x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): boolean;
    _parseJPEG(buffer: any): boolean;
}
