import * as React from 'react';
declare type ClockPickerComponent = (<TDate>(props: ClockPickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const ClockPicker: ClockPickerComponent;
export default ClockPicker;
export declare const clockPickerClasses: {};
export declare type ClockPickerProps<TDate> = Record<any, any>;
export declare type ClockPickerView = 'hours' | 'minutes' | 'seconds';
export declare type ClockPickerClasses = any;
export declare type ClockPickerClassKey = any;
