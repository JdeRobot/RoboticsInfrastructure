import * as React from 'react';
declare type MobileDateTimePickerComponent = (<TDate>(props: MobileDateTimePickerProps<TDate> & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const MobileDateTimePicker: MobileDateTimePickerComponent;
export default MobileDateTimePicker;
export declare type MobileDateTimePickerProps<TDate> = Record<any, any>;
