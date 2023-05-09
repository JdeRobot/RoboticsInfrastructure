import * as React from 'react';
declare type MobileTimePickerComponent = (<TDate>(props: MobileTimePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const MobileTimePicker: MobileTimePickerComponent;
export default MobileTimePicker;
export declare type MobileTimePickerProps<TDate> = Record<any, any>;
