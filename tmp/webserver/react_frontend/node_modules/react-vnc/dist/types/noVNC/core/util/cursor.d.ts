export default class Cursor {
    _target: any;
    _canvas: HTMLCanvasElement;
    _position: {
        x: number;
        y: number;
    };
    _hotSpot: {
        x: number;
        y: number;
    };
    _eventHandlers: {
        mouseover: (event: any) => void;
        mouseleave: (event: any) => void;
        mousemove: (event: any) => void;
        mouseup: (event: any) => void;
    };
    attach(target: any): void;
    detach(): void;
    change(rgba: any, hotx: any, hoty: any, w: any, h: any): void;
    clear(): void;
    move(clientX: any, clientY: any): void;
    _handleMouseOver(event: any): void;
    _handleMouseLeave(event: any): void;
    _handleMouseMove(event: any): void;
    _handleMouseUp(event: any): void;
    _showCursor(): void;
    _hideCursor(): void;
    _shouldShowCursor(target: any): boolean;
    _updateVisibility(target: any): void;
    _updatePosition(): void;
    _captureIsActive(): any;
}
