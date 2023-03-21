"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.default = void 0;
let warnedOnce = false;

const warn = () => {
  if (!warnedOnce) {
    console.warn(['MUI: The AdapterLuxon class was moved from `@mui/lab` to `@mui/x-date-pickers`', '', "You should use `import { AdapterLuxon } from '@mui/x-date-pickers/AdapterLuxon'`", '', 'More information about this migration on our blog: https://mui.com/blog/lab-date-pickers-to-mui-x/.'].join('\n'));
    warnedOnce = true;
  }
}; // tslint:disable-next-line:no-unnecessary-class


class AdapterLuxon {
  constructor() {
    warn();
  }

}

exports.default = AdapterLuxon;