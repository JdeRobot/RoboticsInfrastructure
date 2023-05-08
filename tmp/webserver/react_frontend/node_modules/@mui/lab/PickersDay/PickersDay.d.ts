import * as React from 'react';
declare type PickersDayComponent = (<TDate>(props: PickersDayProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const PickersDay: PickersDayComponent;
export default PickersDay;
export declare const pickersDayClasses: {};
export declare const getPickersDayUtilityClass: (slot: string) => string;
export declare type PickersDayProps<TDate> = Record<any, any>;
export declare type PickersDayClassKey = any;
