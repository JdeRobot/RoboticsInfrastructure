"use strict";
(self["webpackChunkreact_frontend"] = self["webpackChunkreact_frontend"] || []).push([["src_helpers_global_js"],{

/***/ "./src/constants/index.js":
/*!********************************!*\
  !*** ./src/constants/index.js ***!
  \********************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "GlobalVariable": () => (/* binding */ GlobalVariable),
/* harmony export */   "address_code": () => (/* binding */ address_code),
/* harmony export */   "address_gui": () => (/* binding */ address_gui),
/* harmony export */   "websocket_address": () => (/* binding */ websocket_address)
/* harmony export */ });
var websocket_address = "127.0.0.1";
var address_code = "ws://" + websocket_address + ":1905";
var address_gui = "ws://" + websocket_address + ":2303";
var GlobalVariable = {
  simStop: "simStop",
  sendCode: "sendCode",
  running: "running",
  firstAttempt: "firstAttempt",
  simReset: "simReset",
  simResume: "simResume",
  resetRequested: "resetRequested",
  firstCodeSent: "firstCodeSent",
  swapping: "swapping",
  gazeboOn: "gazeboOn",
  gazeboToggle: "gazeboToggle",
  teleOpMode: "teleOpMode"
};


/***/ }),

/***/ "./src/helpers/global.js":
/*!*******************************!*\
  !*** ./src/helpers/global.js ***!
  \*******************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "animation_id": () => (/* binding */ animation_id),
/* harmony export */   "brainFreqAck": () => (/* binding */ brainFreqAck),
/* harmony export */   "command_input": () => (/* binding */ command_input),
/* harmony export */   "content": () => (/* binding */ content),
/* harmony export */   "firstAttempt": () => (/* binding */ firstAttempt),
/* harmony export */   "firstCodeSent": () => (/* binding */ firstCodeSent),
/* harmony export */   "gazeboOn": () => (/* binding */ gazeboOn),
/* harmony export */   "gazeboToggle": () => (/* binding */ gazeboToggle),
/* harmony export */   "getValue": () => (/* binding */ getValue),
/* harmony export */   "guiFreqAck": () => (/* binding */ guiFreqAck),
/* harmony export */   "image_data": () => (/* binding */ image_data),
/* harmony export */   "lap_time": () => (/* binding */ lap_time),
/* harmony export */   "pose": () => (/* binding */ pose),
/* harmony export */   "resetRequested": () => (/* binding */ resetRequested),
/* harmony export */   "running": () => (/* binding */ running),
/* harmony export */   "sendCode": () => (/* binding */ sendCode),
/* harmony export */   "setValue": () => (/* binding */ setValue),
/* harmony export */   "shape": () => (/* binding */ shape),
/* harmony export */   "simReset": () => (/* binding */ simReset),
/* harmony export */   "simResume": () => (/* binding */ simResume),
/* harmony export */   "simStop": () => (/* binding */ simStop),
/* harmony export */   "source": () => (/* binding */ source),
/* harmony export */   "swapping": () => (/* binding */ swapping),
/* harmony export */   "teleOpMode": () => (/* binding */ teleOpMode),
/* harmony export */   "v": () => (/* binding */ v),
/* harmony export */   "w": () => (/* binding */ w)
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../constants */ "./src/constants/index.js");

var brainFreqAck = 12,
  guiFreqAck = 12;
var simStop = false,
  sendCode = false,
  running = true,
  firstAttempt = true,
  simReset = false,
  simResume = false,
  resetRequested = false,
  firstCodeSent = false,
  swapping = false,
  gazeboOn = false,
  gazeboToggle = false,
  teleOpMode = false;
var animation_id, image_data, source, shape, lap_time, pose, content, command_input;
function getValue(x) {
  switch (x) {
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.simStop:
      return simStop;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.running:
      return running;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.sendCode:
      return sendCode;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.firstAttempt:
      return firstAttempt;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.simReset:
      return simReset;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.simResume:
      return simResume;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.resetRequested:
      return resetRequested;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.firstCodeSent:
      return firstCodeSent;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.swapping:
      return swapping;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.gazeboOn:
      return gazeboOn;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.gazeboToggle:
      return gazeboToggle;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.teleOpMode:
      return teleOpMode;
    default:
      console.log(x);
      console.error("Unassigned Value");
  }
}
function setValue(x, val) {
  switch (x) {
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.simStop:
      simStop = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.running:
      running = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.sendCode:
      sendCode = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.firstAttempt:
      firstAttempt = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.simReset:
      simReset = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.simResume:
      simResume = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.resetRequested:
      resetRequested = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.firstCodeSent:
      firstCodeSent = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.swapping:
      swapping = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.gazeboOn:
      gazeboOn = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.gazeboToggle:
      gazeboToggle = val;
      break;
    case _constants__WEBPACK_IMPORTED_MODULE_0__.GlobalVariable.teleOpMode:
      teleOpMode = val;
      break;
    default:
      console.log(x);
  }
}
// Car variables
var v = 0;
var w = 0;


/***/ })

}]);
//# sourceMappingURL=data:application/json;charset=utf-8;base64,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QUFLN0IsK0RBQXVCO01BQzFCSyxRQUFRLEdBQUd3QixHQUFHO01BQ2Q7SUFDRixLQUFLN0IsZ0VBQXdCO01BQzNCTSxTQUFTLEdBQUd1QixHQUFHO01BQ2Y7SUFDRixLQUFLN0IscUVBQTZCO01BQ2hDTyxjQUFjLEdBQUdzQixHQUFHO01BQ3BCO0lBQ0YsS0FBSzdCLG9FQUE0QjtNQUMvQlEsYUFBYSxHQUFHcUIsR0FBRztNQUNuQjtJQUNGLEtBQUs3QiwrREFBdUI7TUFDMUJTLFFBQVEsR0FBR29CLEdBQUc7TUFDZDtJQUNGLEtBQUs3QiwrREFBdUI7TUFDMUJVLFFBQVEsR0FBR21CLEdBQUc7TUFDZDtJQUNGLEtBQUs3QixtRUFBMkI7TUFDOUJXLFlBQVksR0FBR2tCLEdBQUc7TUFDbEI7SUFDRixLQUFLN0IsaUVBQXlCO01BQzVCWSxVQUFVLEdBQUdpQixHQUFHO01BQ2hCO0lBQ0Y7TUFDRUosT0FBTyxDQUFDQyxHQUFHLENBQUNGLENBQUMsQ0FBQztFQUFDO0FBRXJCO0FBQ0E7QUFDQSxJQUFJTSxDQUFDLEdBQUcsQ0FBQztBQUNULElBQUlDLENBQUMsR0FBRyxDQUFDIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vcmVhY3RfZnJvbnRlbmQvLi9zcmMvY29uc3RhbnRzL2luZGV4LmpzIiwid2VicGFjazovL3JlYWN0X2Zyb250ZW5kLy4vc3JjL2hlbHBlcnMvZ2xvYmFsLmpzIl0sInNvdXJjZXNDb250ZW50IjpbImNvbnN0IHdlYnNvY2tldF9hZGRyZXNzID0gXCIxMjcuMC4wLjFcIjtcbmNvbnN0IGFkZHJlc3NfY29kZSA9IFwid3M6Ly9cIiArIHdlYnNvY2tldF9hZGRyZXNzICsgXCI6MTkwNVwiO1xuY29uc3QgYWRkcmVzc19ndWkgPSBcIndzOi8vXCIgKyB3ZWJzb2NrZXRfYWRkcmVzcyArIFwiOjIzMDNcIjtcblxuY29uc3QgR2xvYmFsVmFyaWFibGUgPSB7XG4gIHNpbVN0b3A6IFwic2ltU3RvcFwiLFxuICBzZW5kQ29kZTogXCJzZW5kQ29kZVwiLFxuICBydW5uaW5nOiBcInJ1bm5pbmdcIixcbiAgZmlyc3RBdHRlbXB0OiBcImZpcnN0QXR0ZW1wdFwiLFxuICBzaW1SZXNldDogXCJzaW1SZXNldFwiLFxuICBzaW1SZXN1bWU6IFwic2ltUmVzdW1lXCIsXG4gIHJlc2V0UmVxdWVzdGVkOiBcInJlc2V0UmVxdWVzdGVkXCIsXG4gIGZpcnN0Q29kZVNlbnQ6IFwiZmlyc3RDb2RlU2VudFwiLFxuICBzd2FwcGluZzogXCJzd2FwcGluZ1wiLFxuICBnYXplYm9PbjogXCJnYXplYm9PblwiLFxuICBnYXplYm9Ub2dnbGU6IFwiZ2F6ZWJvVG9nZ2xlXCIsXG4gIHRlbGVPcE1vZGU6IFwidGVsZU9wTW9kZVwiLFxufTtcbmV4cG9ydCB7IHdlYnNvY2tldF9hZGRyZXNzLCBhZGRyZXNzX2NvZGUsIGFkZHJlc3NfZ3VpLCBHbG9iYWxWYXJpYWJsZSB9O1xuIiwiaW1wb3J0IHsgR2xvYmFsVmFyaWFibGUgfSBmcm9tIFwiLi4vY29uc3RhbnRzXCI7XG5sZXQgYnJhaW5GcmVxQWNrID0gMTIsXG4gIGd1aUZyZXFBY2sgPSAxMjtcbmxldCBzaW1TdG9wID0gZmFsc2UsXG4gIHNlbmRDb2RlID0gZmFsc2UsXG4gIHJ1bm5pbmcgPSB0cnVlLFxuICBmaXJzdEF0dGVtcHQgPSB0cnVlLFxuICBzaW1SZXNldCA9IGZhbHNlLFxuICBzaW1SZXN1bWUgPSBmYWxzZSxcbiAgcmVzZXRSZXF1ZXN0ZWQgPSBmYWxzZSxcbiAgZmlyc3RDb2RlU2VudCA9IGZhbHNlLFxuICBzd2FwcGluZyA9IGZhbHNlLFxuICBnYXplYm9PbiA9IGZhbHNlLFxuICBnYXplYm9Ub2dnbGUgPSBmYWxzZSxcbiAgdGVsZU9wTW9kZSA9IGZhbHNlO1xubGV0IGFuaW1hdGlvbl9pZCxcbiAgaW1hZ2VfZGF0YSxcbiAgc291cmNlLFxuICBzaGFwZSxcbiAgbGFwX3RpbWUsXG4gIHBvc2UsXG4gIGNvbnRlbnQsXG4gIGNvbW1hbmRfaW5wdXQ7XG5cbmZ1bmN0aW9uIGdldFZhbHVlKHgpIHtcbiAgc3dpdGNoICh4KSB7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5zaW1TdG9wOlxuICAgICAgcmV0dXJuIHNpbVN0b3A7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5ydW5uaW5nOlxuICAgICAgcmV0dXJuIHJ1bm5pbmc7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5zZW5kQ29kZTpcbiAgICAgIHJldHVybiBzZW5kQ29kZTtcbiAgICBjYXNlIEdsb2JhbFZhcmlhYmxlLmZpcnN0QXR0ZW1wdDpcbiAgICAgIHJldHVybiBmaXJzdEF0dGVtcHQ7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5zaW1SZXNldDpcbiAgICAgIHJldHVybiBzaW1SZXNldDtcbiAgICBjYXNlIEdsb2JhbFZhcmlhYmxlLnNpbVJlc3VtZTpcbiAgICAgIHJldHVybiBzaW1SZXN1bWU7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5yZXNldFJlcXVlc3RlZDpcbiAgICAgIHJldHVybiByZXNldFJlcXVlc3RlZDtcbiAgICBjYXNlIEdsb2JhbFZhcmlhYmxlLmZpcnN0Q29kZVNlbnQ6XG4gICAgICByZXR1cm4gZmlyc3RDb2RlU2VudDtcbiAgICBjYXNlIEdsb2JhbFZhcmlhYmxlLnN3YXBwaW5nOlxuICAgICAgcmV0dXJuIHN3YXBwaW5nO1xuICAgIGNhc2UgR2xvYmFsVmFyaWFibGUuZ2F6ZWJvT246XG4gICAgICByZXR1cm4gZ2F6ZWJvT247XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5nYXplYm9Ub2dnbGU6XG4gICAgICByZXR1cm4gZ2F6ZWJvVG9nZ2xlO1xuICAgIGNhc2UgR2xvYmFsVmFyaWFibGUudGVsZU9wTW9kZTpcbiAgICAgIHJldHVybiB0ZWxlT3BNb2RlO1xuICAgIGRlZmF1bHQ6XG4gICAgICBjb25zb2xlLmxvZyh4KTtcbiAgICAgIGNvbnNvbGUuZXJyb3IoXCJVbmFzc2lnbmVkIFZhbHVlXCIpO1xuICB9XG59XG5cbmZ1bmN0aW9uIHNldFZhbHVlKHgsIHZhbCkge1xuICBzd2l0Y2ggKHgpIHtcbiAgICBjYXNlIEdsb2JhbFZhcmlhYmxlLnNpbVN0b3A6XG4gICAgICBzaW1TdG9wID0gdmFsO1xuICAgICAgYnJlYWs7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5ydW5uaW5nOlxuICAgICAgcnVubmluZyA9IHZhbDtcbiAgICAgIGJyZWFrO1xuICAgIGNhc2UgR2xvYmFsVmFyaWFibGUuc2VuZENvZGU6XG4gICAgICBzZW5kQ29kZSA9IHZhbDtcbiAgICAgIGJyZWFrO1xuICAgIGNhc2UgR2xvYmFsVmFyaWFibGUuZmlyc3RBdHRlbXB0OlxuICAgICAgZmlyc3RBdHRlbXB0ID0gdmFsO1xuICAgICAgYnJlYWs7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5zaW1SZXNldDpcbiAgICAgIHNpbVJlc2V0ID0gdmFsO1xuICAgICAgYnJlYWs7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5zaW1SZXN1bWU6XG4gICAgICBzaW1SZXN1bWUgPSB2YWw7XG4gICAgICBicmVhaztcbiAgICBjYXNlIEdsb2JhbFZhcmlhYmxlLnJlc2V0UmVxdWVzdGVkOlxuICAgICAgcmVzZXRSZXF1ZXN0ZWQgPSB2YWw7XG4gICAgICBicmVhaztcbiAgICBjYXNlIEdsb2JhbFZhcmlhYmxlLmZpcnN0Q29kZVNlbnQ6XG4gICAgICBmaXJzdENvZGVTZW50ID0gdmFsO1xuICAgICAgYnJlYWs7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5zd2FwcGluZzpcbiAgICAgIHN3YXBwaW5nID0gdmFsO1xuICAgICAgYnJlYWs7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5nYXplYm9PbjpcbiAgICAgIGdhemVib09uID0gdmFsO1xuICAgICAgYnJlYWs7XG4gICAgY2FzZSBHbG9iYWxWYXJpYWJsZS5nYXplYm9Ub2dnbGU6XG4gICAgICBnYXplYm9Ub2dnbGUgPSB2YWw7XG4gICAgICBicmVhaztcbiAgICBjYXNlIEdsb2JhbFZhcmlhYmxlLnRlbGVPcE1vZGU6XG4gICAgICB0ZWxlT3BNb2RlID0gdmFsO1xuICAgICAgYnJlYWs7XG4gICAgZGVmYXVsdDpcbiAgICAgIGNvbnNvbGUubG9nKHgpO1xuICB9XG59XG4vLyBDYXIgdmFyaWFibGVzXG5sZXQgdiA9IDA7XG5sZXQgdyA9IDA7XG5cbmV4cG9ydCB7XG4gIGJyYWluRnJlcUFjayxcbiAgZ3VpRnJlcUFjayxcbiAgc2ltU3RvcCxcbiAgc2VuZENvZGUsXG4gIHJ1bm5pbmcsXG4gIGZpcnN0QXR0ZW1wdCxcbiAgc2ltUmVzZXQsXG4gIHNpbVJlc3VtZSxcbiAgcmVzZXRSZXF1ZXN0ZWQsXG4gIGZpcnN0Q29kZVNlbnQsXG4gIHN3YXBwaW5nLFxuICBnYXplYm9PbixcbiAgZ2F6ZWJvVG9nZ2xlLFxuICB0ZWxlT3BNb2RlLFxuICBhbmltYXRpb25faWQsXG4gIGltYWdlX2RhdGEsXG4gIHNvdXJjZSxcbiAgc2hhcGUsXG4gIGxhcF90aW1lLFxuICBwb3NlLFxuICBjb250ZW50LFxuICBjb21tYW5kX2lucHV0LFxuICB2LFxuICB3LFxuICBzZXRWYWx1ZSxcbiAgZ2V0VmFsdWUsXG59O1xuIl0sIm5hbWVzIjpbIndlYnNvY2tldF9hZGRyZXNzIiwiYWRkcmVzc19jb2RlIiwiYWRkcmVzc19ndWkiLCJHbG9iYWxWYXJpYWJsZSIsInNpbVN0b3AiLCJzZW5kQ29kZSIsInJ1bm5pbmciLCJmaXJzdEF0dGVtcHQiLCJzaW1SZXNldCIsInNpbVJlc3VtZSIsInJlc2V0UmVxdWVzdGVkIiwiZmlyc3RDb2RlU2VudCIsInN3YXBwaW5nIiwiZ2F6ZWJvT24iLCJnYXplYm9Ub2dnbGUiLCJ0ZWxlT3BNb2RlIiwiYnJhaW5GcmVxQWNrIiwiZ3VpRnJlcUFjayIsImFuaW1hdGlvbl9pZCIsImltYWdlX2RhdGEiLCJzb3VyY2UiLCJzaGFwZSIsImxhcF90aW1lIiwicG9zZSIsImNvbnRlbnQiLCJjb21tYW5kX2lucHV0IiwiZ2V0VmFsdWUiLCJ4IiwiY29uc29sZSIsImxvZyIsImVycm9yIiwic2V0VmFsdWUiLCJ2YWwiLCJ2IiwidyJdLCJzb3VyY2VSb290IjoiIn0=