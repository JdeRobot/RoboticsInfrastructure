import * as React from 'react';
declare type LocalizationProviderComponent = ((props: LocalizationProviderProps & React.RefAttributes<HTMLDivElement>) => JSX.Element) & {
    propTypes?: any;
};
/**
 * @ignore - do not document.
 */
declare const LocalizationProvider: LocalizationProviderComponent;
export default LocalizationProvider;
export declare type LocalizationProviderProps = Record<any, any>;
