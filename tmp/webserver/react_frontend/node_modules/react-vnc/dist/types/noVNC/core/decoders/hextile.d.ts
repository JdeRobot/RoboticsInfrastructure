export default class HextileDecoder {
    _tiles: number;
    _lastsubencoding: number;
    _tileBuffer: Uint8Array;
    decodeRect(x: any, y: any, width: any, height: any, sock: any, display: any, depth: any): boolean;
    _tilesX: number | undefined;
    _tilesY: number | undefined;
    _totalTiles: number | undefined;
    _background: any[] | undefined;
    _foreground: any[] | undefined;
    _startTile(x: any, y: any, width: any, height: any, color: any): void;
    _tileX: any;
    _tileY: any;
    _tileW: any;
    _tileH: any;
    _subTile(x: any, y: any, w: any, h: any, color: any): void;
    _finishTile(display: any): void;
}
