import * as React from 'react';
declare type YearPickerComponent = (<TDate>(props: YearPickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const YearPicker: YearPickerComponent;
export default YearPicker;
export declare const yearPickerClasses: {};
export declare const getYearPickerUtilityClass: (slot: string) => string;
export declare type YearPickerClasses = any;
export declare type YearPickerClassKey = any;
export declare type YearPickerProps<TDate> = Record<any, any>;
