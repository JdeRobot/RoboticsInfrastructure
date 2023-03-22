import * as React from 'react';
declare type StaticTimePickerComponent = (<TDate>(props: StaticTimePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const StaticTimePicker: StaticTimePickerComponent;
export default StaticTimePicker;
export declare type StaticTimePickerProps<TDate> = Record<any, any>;
