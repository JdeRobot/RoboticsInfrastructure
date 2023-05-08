import * as React from 'react';
declare type DateTimePickerComponent = (<TDate>(props: DateTimePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const DateTimePicker: DateTimePickerComponent;
export default DateTimePicker;
export declare type DateTimePickerProps<TDate> = Record<any, any>;
