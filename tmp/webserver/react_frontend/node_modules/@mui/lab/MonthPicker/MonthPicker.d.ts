import * as React from 'react';
declare type MonthPickerComponent = (<TDate>(props: MonthPickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const MonthPicker: MonthPickerComponent;
export default MonthPicker;
export declare const monthPickerClasses: {};
export declare const getMonthPickerUtilityClass: (slot: string) => string;
export declare type MonthPickerProps<TDate> = Record<any, any>;
export declare type MonthPickerClassKey = any;
