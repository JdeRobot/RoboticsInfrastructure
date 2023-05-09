import * as React from 'react';
declare type DesktopTimePickerComponent = (<TDate>(props: DesktopTimePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const DesktopTimePicker: DesktopTimePickerComponent;
export default DesktopTimePicker;
export declare type DesktopTimePickerProps<TDate> = Record<any, any>;
