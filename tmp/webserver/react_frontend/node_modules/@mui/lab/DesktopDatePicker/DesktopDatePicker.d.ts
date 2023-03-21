import * as React from 'react';
declare type DesktopDatePickerComponent = (<TDate>(props: DesktopDatePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const DesktopDatePicker: DesktopDatePickerComponent;
export default DesktopDatePicker;
export declare type DesktopDatePickerProps<TDate> = Record<any, any>;
