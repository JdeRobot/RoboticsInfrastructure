import * as React from 'react';
declare type DatePickerComponent = (<TDate>(props: DatePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const DatePicker: DatePickerComponent;
export default DatePicker;
export declare type DatePickerProps<TDate> = Record<any, any>;
