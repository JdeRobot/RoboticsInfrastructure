import * as React from 'react';
declare type StaticDatePickerComponent = (<TDate>(props: StaticDatePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const StaticDatePicker: StaticDatePickerComponent;
export default StaticDatePicker;
export declare type StaticDatePickerProps<TDate> = Record<any, any>;
