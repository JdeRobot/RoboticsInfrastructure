import * as React from 'react';
declare type CalendarPickerSkeletonComponent = ((props: CalendarPickerSkeletonProps & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const CalendarPickerSkeleton: CalendarPickerSkeletonComponent;
export default CalendarPickerSkeleton;
export declare const calendarPickerSkeletonClasses: {};
export declare const getCalendarPickerSkeletonUtilityClass: (slot: string) => string;
export declare type CalendarPickerSkeletonProps = Record<any, any>;
export declare type CalendarPickerSkeletonClassKey = any;
