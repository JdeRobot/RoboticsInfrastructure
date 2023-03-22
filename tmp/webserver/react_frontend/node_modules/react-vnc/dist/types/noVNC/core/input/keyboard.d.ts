export default class Keyboard {
    constructor(target: any);
    _target: any;
    _keyDownList: {};
    _altGrArmed: boolean;
    _eventHandlers: {
        keyup: (e: any) => void;
        keydown: (e: any) => void;
        blur: () => void;
    };
    onkeyevent: () => void;
    _sendKeyEvent(keysym: any, code: any, down: any): void;
    _getKeyCode(e: any): any;
    _handleKeyDown(e: any): void;
    _altGrTimeout: NodeJS.Timeout | undefined;
    _altGrCtrlTime: any;
    _handleKeyUp(e: any): void;
    _handleAltGrTimeout(): void;
    _allKeysUp(): void;
    grab(): void;
    ungrab(): void;
}
