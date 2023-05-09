import * as React from 'react';
declare type CalendarPickerComponent = (<TDate>(props: CalendarPickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const CalendarPicker: CalendarPickerComponent;
export default CalendarPicker;
export declare const calendarPickerClasses: {};
export declare type CalendarPickerClassKey = any;
export declare type CalendarPickerClasses = any;
export declare type CalendarPickerProps<TDate> = Record<any, any>;
export declare type CalendarPickerView = 'year' | 'day' | 'month';
