export class Localizer {
    language: string;
    dictionary: any;
    setup(supportedLanguages: any): void;
    get(id: any): any;
    translateDOM(): void;
}
export const l10n: Localizer;
declare function _default(id: any): any;
export default _default;
