export default class EventTargetMixin {
    _listeners: Map<any, any>;
    addEventListener(type: any, callback: any): void;
    removeEventListener(type: any, callback: any): void;
    dispatchEvent(event: any): boolean;
}
