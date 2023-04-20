"use strict";
(self["webpackChunkreact_frontend"] = self["webpackChunkreact_frontend"] || []).push([["src_constants_index_js"],{

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


/***/ })

}]);
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvc3JjX2NvbnN0YW50c19pbmRleF9qcy5jOWE4NzIyZi5qcyIsIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7O0FBQUEsSUFBTUEsaUJBQWlCLEdBQUcsV0FBVztBQUNyQyxJQUFNQyxZQUFZLEdBQUcsT0FBTyxHQUFHRCxpQkFBaUIsR0FBRyxPQUFPO0FBQzFELElBQU1FLFdBQVcsR0FBRyxPQUFPLEdBQUdGLGlCQUFpQixHQUFHLE9BQU87QUFFekQsSUFBTUcsY0FBYyxHQUFHO0VBQ3JCQyxPQUFPLEVBQUUsU0FBUztFQUNsQkMsUUFBUSxFQUFFLFVBQVU7RUFDcEJDLE9BQU8sRUFBRSxTQUFTO0VBQ2xCQyxZQUFZLEVBQUUsY0FBYztFQUM1QkMsUUFBUSxFQUFFLFVBQVU7RUFDcEJDLFNBQVMsRUFBRSxXQUFXO0VBQ3RCQyxjQUFjLEVBQUUsZ0JBQWdCO0VBQ2hDQyxhQUFhLEVBQUUsZUFBZTtFQUM5QkMsUUFBUSxFQUFFLFVBQVU7RUFDcEJDLFFBQVEsRUFBRSxVQUFVO0VBQ3BCQyxZQUFZLEVBQUUsY0FBYztFQUM1QkMsVUFBVSxFQUFFO0FBQ2QsQ0FBQyIsInNvdXJjZXMiOlsid2VicGFjazovL3JlYWN0X2Zyb250ZW5kLy4vc3JjL2NvbnN0YW50cy9pbmRleC5qcyJdLCJzb3VyY2VzQ29udGVudCI6WyJjb25zdCB3ZWJzb2NrZXRfYWRkcmVzcyA9IFwiMTI3LjAuMC4xXCI7XG5jb25zdCBhZGRyZXNzX2NvZGUgPSBcIndzOi8vXCIgKyB3ZWJzb2NrZXRfYWRkcmVzcyArIFwiOjE5MDVcIjtcbmNvbnN0IGFkZHJlc3NfZ3VpID0gXCJ3czovL1wiICsgd2Vic29ja2V0X2FkZHJlc3MgKyBcIjoyMzAzXCI7XG5cbmNvbnN0IEdsb2JhbFZhcmlhYmxlID0ge1xuICBzaW1TdG9wOiBcInNpbVN0b3BcIixcbiAgc2VuZENvZGU6IFwic2VuZENvZGVcIixcbiAgcnVubmluZzogXCJydW5uaW5nXCIsXG4gIGZpcnN0QXR0ZW1wdDogXCJmaXJzdEF0dGVtcHRcIixcbiAgc2ltUmVzZXQ6IFwic2ltUmVzZXRcIixcbiAgc2ltUmVzdW1lOiBcInNpbVJlc3VtZVwiLFxuICByZXNldFJlcXVlc3RlZDogXCJyZXNldFJlcXVlc3RlZFwiLFxuICBmaXJzdENvZGVTZW50OiBcImZpcnN0Q29kZVNlbnRcIixcbiAgc3dhcHBpbmc6IFwic3dhcHBpbmdcIixcbiAgZ2F6ZWJvT246IFwiZ2F6ZWJvT25cIixcbiAgZ2F6ZWJvVG9nZ2xlOiBcImdhemVib1RvZ2dsZVwiLFxuICB0ZWxlT3BNb2RlOiBcInRlbGVPcE1vZGVcIixcbn07XG5leHBvcnQgeyB3ZWJzb2NrZXRfYWRkcmVzcywgYWRkcmVzc19jb2RlLCBhZGRyZXNzX2d1aSwgR2xvYmFsVmFyaWFibGUgfTtcbiJdLCJuYW1lcyI6WyJ3ZWJzb2NrZXRfYWRkcmVzcyIsImFkZHJlc3NfY29kZSIsImFkZHJlc3NfZ3VpIiwiR2xvYmFsVmFyaWFibGUiLCJzaW1TdG9wIiwic2VuZENvZGUiLCJydW5uaW5nIiwiZmlyc3RBdHRlbXB0Iiwic2ltUmVzZXQiLCJzaW1SZXN1bWUiLCJyZXNldFJlcXVlc3RlZCIsImZpcnN0Q29kZVNlbnQiLCJzd2FwcGluZyIsImdhemVib09uIiwiZ2F6ZWJvVG9nZ2xlIiwidGVsZU9wTW9kZSJdLCJzb3VyY2VSb290IjoiIn0=