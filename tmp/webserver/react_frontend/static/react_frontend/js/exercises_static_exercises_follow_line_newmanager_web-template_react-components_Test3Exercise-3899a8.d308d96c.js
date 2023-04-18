(self["webpackChunkreact_frontend"] = self["webpackChunkreact_frontend"] || []).push([["exercises_static_exercises_follow_line_newmanager_web-template_react-components_Test3Exercise-3899a8"],{

/***/ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/Test3ExerciseManager.js":
/*!******************************************************************************************************************!*\
  !*** ../exercises/static/exercises/follow_line_newmanager/web-template/react-components/Test3ExerciseManager.js ***!
  \******************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! react */ "./node_modules/react/index.js");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var classnames__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! classnames */ "./node_modules/classnames/index.js");
/* harmony import */ var classnames__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(classnames__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _css_TestExerciseManager3_css__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./css/TestExerciseManager3.css */ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestExerciseManager3.css");
/* harmony import */ var react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! react/jsx-runtime */ "./node_modules/react/jsx-runtime.js");
function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }
function _iterableToArrayLimit(arr, i) { var _i = arr == null ? null : typeof Symbol !== "undefined" && arr[Symbol.iterator] || arr["@@iterator"]; if (_i == null) return; var _arr = []; var _n = true; var _d = false; var _s, _e; try { for (_i = _i.call(arr); !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"] != null) _i["return"](); } finally { if (_d) throw _e; } } return _arr; }
function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }






var Test3ExerciseManager = function Test3ExerciseManager() {
  var _React$useState = react__WEBPACK_IMPORTED_MODULE_0__.useState("Idle"),
    _React$useState2 = _slicedToArray(_React$useState, 2),
    state = _React$useState2[0],
    setState = _React$useState2[1];
  var classes = classnames__WEBPACK_IMPORTED_MODULE_1___default()({
    "test-exercise-manager-state": true
  });
  react__WEBPACK_IMPORTED_MODULE_0__.useEffect(function () {
    console.log("Test3ExerciseManager subscribing to ['state-change'] events");
    var callback = function callback(message) {
      setState(message.data.state);
      console.log(message);
    };
    RoboticsExerciseComponents.commsManager.subscribe([RoboticsExerciseComponents.commsManager.events.STATE_CHANGED], callback);
    return function () {
      console.log("Test2ExerciseManager unsubscribing from ['state-changed'] events");
      RoboticsExerciseComponents.commsManager.unsubscribe([RoboticsExerciseComponents.commsManager.events.STATE_CHANGED], callback);
    };
  }, []);
  return /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsxs)(react__WEBPACK_IMPORTED_MODULE_0__.Fragment, {
    children: [/*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsx)("hr", {}), /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsxs)("div", {
      className: classes,
      children: ["CURRENT STATE: ", state]
    })]
  });
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (Test3ExerciseManager);

/***/ }),

/***/ "./node_modules/classnames/index.js":
/*!******************************************!*\
  !*** ./node_modules/classnames/index.js ***!
  \******************************************/
/***/ ((module, exports) => {

var __WEBPACK_AMD_DEFINE_ARRAY__, __WEBPACK_AMD_DEFINE_RESULT__;/*!
	Copyright (c) 2018 Jed Watson.
	Licensed under the MIT License (MIT), see
	http://jedwatson.github.io/classnames
*/
/* global define */

(function () {
	'use strict';

	var hasOwn = {}.hasOwnProperty;
	var nativeCodeString = '[native code]';

	function classNames() {
		var classes = [];

		for (var i = 0; i < arguments.length; i++) {
			var arg = arguments[i];
			if (!arg) continue;

			var argType = typeof arg;

			if (argType === 'string' || argType === 'number') {
				classes.push(arg);
			} else if (Array.isArray(arg)) {
				if (arg.length) {
					var inner = classNames.apply(null, arg);
					if (inner) {
						classes.push(inner);
					}
				}
			} else if (argType === 'object') {
				if (arg.toString !== Object.prototype.toString && !arg.toString.toString().includes('[native code]')) {
					classes.push(arg.toString());
					continue;
				}

				for (var key in arg) {
					if (hasOwn.call(arg, key) && arg[key]) {
						classes.push(key);
					}
				}
			}
		}

		return classes.join(' ');
	}

	if ( true && module.exports) {
		classNames.default = classNames;
		module.exports = classNames;
	} else if (true) {
		// register as 'classnames', consistent with npm package name
		!(__WEBPACK_AMD_DEFINE_ARRAY__ = [], __WEBPACK_AMD_DEFINE_RESULT__ = (function () {
			return classNames;
		}).apply(exports, __WEBPACK_AMD_DEFINE_ARRAY__),
		__WEBPACK_AMD_DEFINE_RESULT__ !== undefined && (module.exports = __WEBPACK_AMD_DEFINE_RESULT__));
	} else {}
}());


/***/ }),

/***/ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestExerciseManager3.css":
/*!***********************************************************************************************************************!*\
  !*** ../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestExerciseManager3.css ***!
  \***********************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ })

}]);
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvZXhlcmNpc2VzX3N0YXRpY19leGVyY2lzZXNfZm9sbG93X2xpbmVfbmV3bWFuYWdlcl93ZWItdGVtcGxhdGVfcmVhY3QtY29tcG9uZW50c19UZXN0M0V4ZXJjaXNlLTM4OTlhOC5kMzA4ZDk2Yy5qcyIsIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQStCO0FBQ0s7QUFFSTtBQUNUO0FBQUE7QUFBQTtBQUUvQixJQUFNRyxvQkFBb0IsR0FBRyxTQUF2QkEsb0JBQW9CLEdBQVM7RUFDakMsc0JBQTBCSCwyQ0FBYyxDQUFDLE1BQU0sQ0FBQztJQUFBO0lBQXpDSyxLQUFLO0lBQUVDLFFBQVE7RUFFdEIsSUFBTUMsT0FBTyxHQUFHTixpREFBVSxDQUFDO0lBQ3pCLDZCQUE2QixFQUFFO0VBQ2pDLENBQUMsQ0FBQztFQUVGRCw0Q0FBZSxDQUFDLFlBQU07SUFDcEJTLE9BQU8sQ0FBQ0MsR0FBRyxDQUFDLDZEQUE2RCxDQUFDO0lBRTFFLElBQU1DLFFBQVEsR0FBRyxTQUFYQSxRQUFRLENBQUlDLE9BQU8sRUFBSztNQUN4Qk4sUUFBUSxDQUFDTSxPQUFPLENBQUNDLElBQUksQ0FBQ1IsS0FBSyxDQUFDO01BQzVCSSxPQUFPLENBQUNDLEdBQUcsQ0FBQ0UsT0FBTyxDQUFDO0lBQzFCLENBQUM7SUFFREUsMEJBQTBCLENBQUNDLFlBQVksQ0FBQ0MsU0FBUyxDQUFDLENBQzVDRiwwQkFBMEIsQ0FBQ0MsWUFBWSxDQUFDRSxNQUFNLENBQUNDLGFBQWEsQ0FDN0QsRUFDRFAsUUFBUSxDQUFDO0lBRWIsT0FBTyxZQUFNO01BQ1hGLE9BQU8sQ0FBQ0MsR0FBRyxDQUFDLGtFQUFrRSxDQUFDO01BQy9FSSwwQkFBMEIsQ0FBQ0MsWUFBWSxDQUFDSSxXQUFXLENBQUMsQ0FDOUNMLDBCQUEwQixDQUFDQyxZQUFZLENBQUNFLE1BQU0sQ0FBQ0MsYUFBYSxDQUM3RCxFQUNIUCxRQUFRLENBQUM7SUFDYixDQUFDO0VBQ0gsQ0FBQyxFQUFFLEVBQUUsQ0FBQztFQUVOLG9CQUNFLHdEQUFDLDJDQUFRO0lBQUEsd0JBQ0wsZ0VBQU0sZUFDTjtNQUFLLFNBQVMsRUFBRUosT0FBUTtNQUFBLFdBQUMsaUJBQWUsRUFBQ0YsS0FBSztJQUFBLEVBQU87RUFBQSxFQUM5QztBQUVmLENBQUM7QUFFRCxpRUFBZUYsb0JBQW9COzs7Ozs7Ozs7O0FDM0NuQztBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTs7QUFFQSxnQkFBZ0I7QUFDaEI7O0FBRUE7QUFDQTs7QUFFQSxrQkFBa0Isc0JBQXNCO0FBQ3hDO0FBQ0E7O0FBRUE7O0FBRUE7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTs7QUFFQSxLQUFLLEtBQTZCO0FBQ2xDO0FBQ0E7QUFDQSxHQUFHLFNBQVMsSUFBNEU7QUFDeEY7QUFDQSxFQUFFLGlDQUFxQixFQUFFLG1DQUFFO0FBQzNCO0FBQ0EsR0FBRztBQUFBLGtHQUFDO0FBQ0osR0FBRyxLQUFLLEVBRU47QUFDRixDQUFDOzs7Ozs7Ozs7Ozs7O0FDM0REIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vcmVhY3RfZnJvbnRlbmQvLi4vZXhlcmNpc2VzL3N0YXRpYy9leGVyY2lzZXMvZm9sbG93X2xpbmVfbmV3bWFuYWdlci93ZWItdGVtcGxhdGUvcmVhY3QtY29tcG9uZW50cy9UZXN0M0V4ZXJjaXNlTWFuYWdlci5qcyIsIndlYnBhY2s6Ly9yZWFjdF9mcm9udGVuZC8uL25vZGVfbW9kdWxlcy9jbGFzc25hbWVzL2luZGV4LmpzIiwid2VicGFjazovL3JlYWN0X2Zyb250ZW5kLy4uL2V4ZXJjaXNlcy9zdGF0aWMvZXhlcmNpc2VzL2ZvbGxvd19saW5lX25ld21hbmFnZXIvd2ViLXRlbXBsYXRlL3JlYWN0LWNvbXBvbmVudHMvY3NzL1Rlc3RFeGVyY2lzZU1hbmFnZXIzLmNzcz8yOWM5Il0sInNvdXJjZXNDb250ZW50IjpbImltcG9ydCAqIGFzIFJlYWN0IGZyb20gJ3JlYWN0JztcbmltcG9ydCBjbGFzc05hbWVzIGZyb20gJ2NsYXNzbmFtZXMnO1xuXG5pbXBvcnQgJy4vY3NzL1Rlc3RFeGVyY2lzZU1hbmFnZXIzLmNzcyc7XG5pbXBvcnQge0ZyYWdtZW50fSBmcm9tIFwicmVhY3RcIjtcblxuY29uc3QgVGVzdDNFeGVyY2lzZU1hbmFnZXIgPSAoKSA9PiB7XG4gIGNvbnN0IFtzdGF0ZSwgc2V0U3RhdGVdID0gUmVhY3QudXNlU3RhdGUoXCJJZGxlXCIpO1xuXG4gIGNvbnN0IGNsYXNzZXMgPSBjbGFzc05hbWVzKHtcbiAgICBcInRlc3QtZXhlcmNpc2UtbWFuYWdlci1zdGF0ZVwiOiB0cnVlLFxuICB9KTtcblxuICBSZWFjdC51c2VFZmZlY3QoKCkgPT4ge1xuICAgIGNvbnNvbGUubG9nKFwiVGVzdDNFeGVyY2lzZU1hbmFnZXIgc3Vic2NyaWJpbmcgdG8gWydzdGF0ZS1jaGFuZ2UnXSBldmVudHNcIik7XG5cbiAgICBjb25zdCBjYWxsYmFjayA9IChtZXNzYWdlKSA9PiB7XG4gICAgICAgICAgc2V0U3RhdGUobWVzc2FnZS5kYXRhLnN0YXRlKTtcbiAgICAgICAgICBjb25zb2xlLmxvZyhtZXNzYWdlKTtcbiAgICB9O1xuXG4gICAgUm9ib3RpY3NFeGVyY2lzZUNvbXBvbmVudHMuY29tbXNNYW5hZ2VyLnN1YnNjcmliZShbXG4gICAgICAgICAgUm9ib3RpY3NFeGVyY2lzZUNvbXBvbmVudHMuY29tbXNNYW5hZ2VyLmV2ZW50cy5TVEFURV9DSEFOR0VEXG4gICAgICAgIF0sXG4gICAgICAgIGNhbGxiYWNrKTtcblxuICAgIHJldHVybiAoKSA9PiB7XG4gICAgICBjb25zb2xlLmxvZyhcIlRlc3QyRXhlcmNpc2VNYW5hZ2VyIHVuc3Vic2NyaWJpbmcgZnJvbSBbJ3N0YXRlLWNoYW5nZWQnXSBldmVudHNcIik7XG4gICAgICBSb2JvdGljc0V4ZXJjaXNlQ29tcG9uZW50cy5jb21tc01hbmFnZXIudW5zdWJzY3JpYmUoW1xuICAgICAgICAgICAgUm9ib3RpY3NFeGVyY2lzZUNvbXBvbmVudHMuY29tbXNNYW5hZ2VyLmV2ZW50cy5TVEFURV9DSEFOR0VEXG4gICAgICAgICAgXSxcbiAgICAgICAgY2FsbGJhY2spO1xuICAgIH1cbiAgfSwgW10pO1xuXG4gIHJldHVybiAoXG4gICAgPEZyYWdtZW50PlxuICAgICAgICA8aHIgLz5cbiAgICAgICAgPGRpdiBjbGFzc05hbWU9e2NsYXNzZXN9PkNVUlJFTlQgU1RBVEU6IHtzdGF0ZX08L2Rpdj5cbiAgICA8L0ZyYWdtZW50PlxuICApXG59XG5cbmV4cG9ydCBkZWZhdWx0IFRlc3QzRXhlcmNpc2VNYW5hZ2VyOyIsIi8qIVxuXHRDb3B5cmlnaHQgKGMpIDIwMTggSmVkIFdhdHNvbi5cblx0TGljZW5zZWQgdW5kZXIgdGhlIE1JVCBMaWNlbnNlIChNSVQpLCBzZWVcblx0aHR0cDovL2plZHdhdHNvbi5naXRodWIuaW8vY2xhc3NuYW1lc1xuKi9cbi8qIGdsb2JhbCBkZWZpbmUgKi9cblxuKGZ1bmN0aW9uICgpIHtcblx0J3VzZSBzdHJpY3QnO1xuXG5cdHZhciBoYXNPd24gPSB7fS5oYXNPd25Qcm9wZXJ0eTtcblx0dmFyIG5hdGl2ZUNvZGVTdHJpbmcgPSAnW25hdGl2ZSBjb2RlXSc7XG5cblx0ZnVuY3Rpb24gY2xhc3NOYW1lcygpIHtcblx0XHR2YXIgY2xhc3NlcyA9IFtdO1xuXG5cdFx0Zm9yICh2YXIgaSA9IDA7IGkgPCBhcmd1bWVudHMubGVuZ3RoOyBpKyspIHtcblx0XHRcdHZhciBhcmcgPSBhcmd1bWVudHNbaV07XG5cdFx0XHRpZiAoIWFyZykgY29udGludWU7XG5cblx0XHRcdHZhciBhcmdUeXBlID0gdHlwZW9mIGFyZztcblxuXHRcdFx0aWYgKGFyZ1R5cGUgPT09ICdzdHJpbmcnIHx8IGFyZ1R5cGUgPT09ICdudW1iZXInKSB7XG5cdFx0XHRcdGNsYXNzZXMucHVzaChhcmcpO1xuXHRcdFx0fSBlbHNlIGlmIChBcnJheS5pc0FycmF5KGFyZykpIHtcblx0XHRcdFx0aWYgKGFyZy5sZW5ndGgpIHtcblx0XHRcdFx0XHR2YXIgaW5uZXIgPSBjbGFzc05hbWVzLmFwcGx5KG51bGwsIGFyZyk7XG5cdFx0XHRcdFx0aWYgKGlubmVyKSB7XG5cdFx0XHRcdFx0XHRjbGFzc2VzLnB1c2goaW5uZXIpO1xuXHRcdFx0XHRcdH1cblx0XHRcdFx0fVxuXHRcdFx0fSBlbHNlIGlmIChhcmdUeXBlID09PSAnb2JqZWN0Jykge1xuXHRcdFx0XHRpZiAoYXJnLnRvU3RyaW5nICE9PSBPYmplY3QucHJvdG90eXBlLnRvU3RyaW5nICYmICFhcmcudG9TdHJpbmcudG9TdHJpbmcoKS5pbmNsdWRlcygnW25hdGl2ZSBjb2RlXScpKSB7XG5cdFx0XHRcdFx0Y2xhc3Nlcy5wdXNoKGFyZy50b1N0cmluZygpKTtcblx0XHRcdFx0XHRjb250aW51ZTtcblx0XHRcdFx0fVxuXG5cdFx0XHRcdGZvciAodmFyIGtleSBpbiBhcmcpIHtcblx0XHRcdFx0XHRpZiAoaGFzT3duLmNhbGwoYXJnLCBrZXkpICYmIGFyZ1trZXldKSB7XG5cdFx0XHRcdFx0XHRjbGFzc2VzLnB1c2goa2V5KTtcblx0XHRcdFx0XHR9XG5cdFx0XHRcdH1cblx0XHRcdH1cblx0XHR9XG5cblx0XHRyZXR1cm4gY2xhc3Nlcy5qb2luKCcgJyk7XG5cdH1cblxuXHRpZiAodHlwZW9mIG1vZHVsZSAhPT0gJ3VuZGVmaW5lZCcgJiYgbW9kdWxlLmV4cG9ydHMpIHtcblx0XHRjbGFzc05hbWVzLmRlZmF1bHQgPSBjbGFzc05hbWVzO1xuXHRcdG1vZHVsZS5leHBvcnRzID0gY2xhc3NOYW1lcztcblx0fSBlbHNlIGlmICh0eXBlb2YgZGVmaW5lID09PSAnZnVuY3Rpb24nICYmIHR5cGVvZiBkZWZpbmUuYW1kID09PSAnb2JqZWN0JyAmJiBkZWZpbmUuYW1kKSB7XG5cdFx0Ly8gcmVnaXN0ZXIgYXMgJ2NsYXNzbmFtZXMnLCBjb25zaXN0ZW50IHdpdGggbnBtIHBhY2thZ2UgbmFtZVxuXHRcdGRlZmluZSgnY2xhc3NuYW1lcycsIFtdLCBmdW5jdGlvbiAoKSB7XG5cdFx0XHRyZXR1cm4gY2xhc3NOYW1lcztcblx0XHR9KTtcblx0fSBlbHNlIHtcblx0XHR3aW5kb3cuY2xhc3NOYW1lcyA9IGNsYXNzTmFtZXM7XG5cdH1cbn0oKSk7XG4iLCIvLyBleHRyYWN0ZWQgYnkgbWluaS1jc3MtZXh0cmFjdC1wbHVnaW5cbmV4cG9ydCB7fTsiXSwibmFtZXMiOlsiUmVhY3QiLCJjbGFzc05hbWVzIiwiRnJhZ21lbnQiLCJUZXN0M0V4ZXJjaXNlTWFuYWdlciIsInVzZVN0YXRlIiwic3RhdGUiLCJzZXRTdGF0ZSIsImNsYXNzZXMiLCJ1c2VFZmZlY3QiLCJjb25zb2xlIiwibG9nIiwiY2FsbGJhY2siLCJtZXNzYWdlIiwiZGF0YSIsIlJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzIiwiY29tbXNNYW5hZ2VyIiwic3Vic2NyaWJlIiwiZXZlbnRzIiwiU1RBVEVfQ0hBTkdFRCIsInVuc3Vic2NyaWJlIl0sInNvdXJjZVJvb3QiOiIifQ==