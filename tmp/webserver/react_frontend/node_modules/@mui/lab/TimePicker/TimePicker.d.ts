import * as React from 'react';
declare type TimePickerComponent = (<TDate>(props: TimePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const TimePicker: TimePickerComponent;
export default TimePicker;
export declare type TimePickerProps<TDate> = Record<any, any>;
