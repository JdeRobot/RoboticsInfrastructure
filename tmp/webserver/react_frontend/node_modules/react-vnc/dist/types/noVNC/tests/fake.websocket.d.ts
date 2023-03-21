declare class FakeWebSocket {
    constructor(uri: any, protocols: any);
    url: any;
    binaryType: string;
    extensions: string;
    onerror: any;
    onmessage: any;
    onopen: any;
    protocol: any;
    _sendQueue: Uint8Array;
    readyState: number;
    bufferedAmount: number;
    _isFake: boolean;
    close(code: any, reason: any): void;
    send(data: any): void;
    _getSentData(): Uint8Array;
    _open(): void;
    _receiveData(data: any): void;
}
declare namespace FakeWebSocket {
    const OPEN: number;
    const CONNECTING: number;
    const CLOSING: number;
    const CLOSED: number;
    const _isFake: boolean;
    function replace(): void;
    function restore(): void;
}
export default FakeWebSocket;
