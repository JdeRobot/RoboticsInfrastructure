export interface StackClasses {
    /** Styles applied to the root element. */
    root: string;
}
export declare type StackClassKey = keyof StackClasses;
export declare function getStackUtilityClass(slot: string): string;
declare const stackClasses: StackClasses;
export default stackClasses;
