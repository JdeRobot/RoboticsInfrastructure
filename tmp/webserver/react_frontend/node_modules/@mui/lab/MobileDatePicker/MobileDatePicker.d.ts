import * as React from 'react';
declare type MobileDatePickerComponent = (<TDate>(props: MobileDatePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const MobileDatePicker: MobileDatePickerComponent;
export default MobileDatePicker;
export declare type MobileDatePickerProps<TDate> = Record<any, any>;
