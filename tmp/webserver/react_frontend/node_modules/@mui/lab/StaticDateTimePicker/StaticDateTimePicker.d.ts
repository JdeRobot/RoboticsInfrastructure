import * as React from 'react';
declare type StaticDateTimePickerComponent = (<TDate>(props: StaticDateTimePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const StaticDateTimePicker: StaticDateTimePickerComponent;
export default StaticDateTimePicker;
export declare type StaticDateTimePickerProps<TDate> = Record<any, any>;
