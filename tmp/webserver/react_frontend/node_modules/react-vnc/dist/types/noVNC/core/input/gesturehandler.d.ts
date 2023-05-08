export default class GestureHandler {
    _target: any;
    _state: number;
    _tracked: any[];
    _ignored: any[];
    _waitingRelease: boolean;
    _releaseStart: number;
    _longpressTimeoutId: NodeJS.Timeout | null;
    _twoTouchTimeoutId: NodeJS.Timeout | null;
    _boundEventHandler: (e: any) => void;
    attach(target: any): void;
    detach(): void;
    _eventHandler(e: any): void;
    _touchStart(id: any, x: any, y: any): void;
    _touchMove(id: any, x: any, y: any): void;
    _touchEnd(id: any, x: any, y: any): void;
    _hasDetectedGesture(): boolean;
    _startLongpressTimeout(): void;
    _stopLongpressTimeout(): void;
    _longpressTimeout(): void;
    _startTwoTouchTimeout(): void;
    _stopTwoTouchTimeout(): void;
    _isTwoTouchTimeoutRunning(): boolean;
    _twoTouchTimeout(): void;
    _pushEvent(type: any): void;
    _stateToGesture(state: any): "drag" | "onetap" | "twotap" | "threetap" | "longpress" | "twodrag" | "pinch";
    _getPosition(): {
        first: {
            x: number;
            y: number;
        };
        last: {
            x: number;
            y: number;
        };
    };
    _getAverageMovement(): {
        x: number;
        y: number;
    };
    _getAverageDistance(): {
        first: {
            x: number;
            y: number;
        };
        last: {
            x: number;
            y: number;
        };
    };
}
