(self["webpackChunkreact_frontend"] = self["webpackChunkreact_frontend"] || []).push([["exercises_static_exercises_follow_line_newmanager_web-template_react-components_Test2Exercise-4d63b4"],{

/***/ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/Test2ExerciseManager.js":
/*!******************************************************************************************************************!*\
  !*** ../exercises/static/exercises/follow_line_newmanager/web-template/react-components/Test2ExerciseManager.js ***!
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
/* harmony import */ var _css_TestExerciseManager2_css__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./css/TestExerciseManager2.css */ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestExerciseManager2.css");
/* harmony import */ var react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! react/jsx-runtime */ "./node_modules/react/jsx-runtime.js");
function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }
function _iterableToArrayLimit(arr, i) { var _i = arr == null ? null : typeof Symbol !== "undefined" && arr[Symbol.iterator] || arr["@@iterator"]; if (_i == null) return; var _arr = []; var _n = true; var _d = false; var _s, _e; try { for (_i = _i.call(arr); !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"] != null) _i["return"](); } finally { if (_d) throw _e; } } return _arr; }
function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }






var Test2ExerciseManager = function Test2ExerciseManager() {
  var _React$useState = react__WEBPACK_IMPORTED_MODULE_0__.useState("No responses received"),
    _React$useState2 = _slicedToArray(_React$useState, 2),
    message = _React$useState2[0],
    setMessage = _React$useState2[1];
  var _React$useState3 = react__WEBPACK_IMPORTED_MODULE_0__.useState(false),
    _React$useState4 = _slicedToArray(_React$useState3, 2),
    iserror = _React$useState4[0],
    setIsError = _React$useState4[1];
  var classes = classnames__WEBPACK_IMPORTED_MODULE_1___default()({
    "test-exercise-manager-message": true,
    "error": iserror
  });
  react__WEBPACK_IMPORTED_MODULE_0__.useEffect(function () {
    console.log("Test2ExerciseManager subscribing to ['ack','error'] events");
    var callback = function callback(message) {
      setIsError(message.command === 'error');
      setMessage(message.data.message);
      console.log(message.data.message);
    };
    RoboticsExerciseComponents.commsManager.subscribe(['ack', 'error'], callback);
    return function () {
      console.log("Test2ExerciseManager unsubscribing from ['ack','error'] events");
      RoboticsExerciseComponents.commsManager.unsubscribe(['ack', 'error'], callback);
    };
  }, []);
  return /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsxs)(react__WEBPACK_IMPORTED_MODULE_0__.Fragment, {
    children: [/*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsx)("hr", {}), /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsx)("div", {
      className: classes,
      children: message
    })]
  });
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (Test2ExerciseManager);

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

/***/ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestExerciseManager2.css":
/*!***********************************************************************************************************************!*\
  !*** ../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestExerciseManager2.css ***!
  \***********************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ })

}]);
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvZXhlcmNpc2VzX3N0YXRpY19leGVyY2lzZXNfZm9sbG93X2xpbmVfbmV3bWFuYWdlcl93ZWItdGVtcGxhdGVfcmVhY3QtY29tcG9uZW50c19UZXN0MkV4ZXJjaXNlLTRkNjNiNC41NzJmYTI4ZS5qcyIsIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQStCO0FBQ0s7QUFFSTtBQUNUO0FBQUE7QUFBQTtBQUUvQixJQUFNRyxvQkFBb0IsR0FBRyxTQUF2QkEsb0JBQW9CLEdBQVM7RUFDL0Isc0JBQThCSCwyQ0FBYyxDQUFDLHVCQUF1QixDQUFDO0lBQUE7SUFBOURLLE9BQU87SUFBRUMsVUFBVTtFQUMxQix1QkFBOEJOLDJDQUFjLENBQUMsS0FBSyxDQUFDO0lBQUE7SUFBNUNPLE9BQU87SUFBRUMsVUFBVTtFQUUxQixJQUFNQyxPQUFPLEdBQUdSLGlEQUFVLENBQUM7SUFDdkIsK0JBQStCLEVBQUUsSUFBSTtJQUNyQyxPQUFPLEVBQUVNO0VBQ2IsQ0FBQyxDQUFDO0VBRUZQLDRDQUFlLENBQUMsWUFBTTtJQUNsQlcsT0FBTyxDQUFDQyxHQUFHLENBQUMsNERBQTRELENBQUM7SUFDekUsSUFBTUMsUUFBUSxHQUFHLFNBQVhBLFFBQVEsQ0FBSVIsT0FBTyxFQUFLO01BQzFCRyxVQUFVLENBQUNILE9BQU8sQ0FBQ1MsT0FBTyxLQUFLLE9BQU8sQ0FBQztNQUN2Q1IsVUFBVSxDQUFDRCxPQUFPLENBQUNVLElBQUksQ0FBQ1YsT0FBTyxDQUFDO01BQ2hDTSxPQUFPLENBQUNDLEdBQUcsQ0FBQ1AsT0FBTyxDQUFDVSxJQUFJLENBQUNWLE9BQU8sQ0FBQztJQUNyQyxDQUFDO0lBRURXLDBCQUEwQixDQUFDQyxZQUFZLENBQUNDLFNBQVMsQ0FBQyxDQUFDLEtBQUssRUFBRSxPQUFPLENBQUMsRUFDOURMLFFBQVEsQ0FBQztJQUViLE9BQU8sWUFBTTtNQUNURixPQUFPLENBQUNDLEdBQUcsQ0FBQyxnRUFBZ0UsQ0FBQztNQUM3RUksMEJBQTBCLENBQUNDLFlBQVksQ0FBQ0UsV0FBVyxDQUFDLENBQUMsS0FBSyxFQUFFLE9BQU8sQ0FBQyxFQUNoRU4sUUFBUSxDQUFDO0lBQ2pCLENBQUM7RUFDTCxDQUFDLEVBQUUsRUFBRSxDQUFDO0VBRU4sb0JBQ0ksd0RBQUMsMkNBQVE7SUFBQSx3QkFDTCxnRUFBTSxlQUNOO01BQUssU0FBUyxFQUFFSixPQUFRO01BQUEsVUFBRUo7SUFBTyxFQUFPO0VBQUEsRUFDakM7QUFFbkIsQ0FBQztBQUVELGlFQUFlRixvQkFBb0I7Ozs7Ozs7Ozs7QUN6Q25DO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBOztBQUVBLGdCQUFnQjtBQUNoQjs7QUFFQTtBQUNBOztBQUVBLGtCQUFrQixzQkFBc0I7QUFDeEM7QUFDQTs7QUFFQTs7QUFFQTtBQUNBO0FBQ0EsS0FBSztBQUNMO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBOztBQUVBLEtBQUssS0FBNkI7QUFDbEM7QUFDQTtBQUNBLEdBQUcsU0FBUyxJQUE0RTtBQUN4RjtBQUNBLEVBQUUsaUNBQXFCLEVBQUUsbUNBQUU7QUFDM0I7QUFDQSxHQUFHO0FBQUEsa0dBQUM7QUFDSixHQUFHLEtBQUssRUFFTjtBQUNGLENBQUM7Ozs7Ozs7Ozs7Ozs7QUMzREQiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly9yZWFjdF9mcm9udGVuZC8uLi9leGVyY2lzZXMvc3RhdGljL2V4ZXJjaXNlcy9mb2xsb3dfbGluZV9uZXdtYW5hZ2VyL3dlYi10ZW1wbGF0ZS9yZWFjdC1jb21wb25lbnRzL1Rlc3QyRXhlcmNpc2VNYW5hZ2VyLmpzIiwid2VicGFjazovL3JlYWN0X2Zyb250ZW5kLy4vbm9kZV9tb2R1bGVzL2NsYXNzbmFtZXMvaW5kZXguanMiLCJ3ZWJwYWNrOi8vcmVhY3RfZnJvbnRlbmQvLi4vZXhlcmNpc2VzL3N0YXRpYy9leGVyY2lzZXMvZm9sbG93X2xpbmVfbmV3bWFuYWdlci93ZWItdGVtcGxhdGUvcmVhY3QtY29tcG9uZW50cy9jc3MvVGVzdEV4ZXJjaXNlTWFuYWdlcjIuY3NzPzliZWYiXSwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0ICogYXMgUmVhY3QgZnJvbSAncmVhY3QnO1xuaW1wb3J0IGNsYXNzTmFtZXMgZnJvbSAnY2xhc3NuYW1lcyc7XG5cbmltcG9ydCAnLi9jc3MvVGVzdEV4ZXJjaXNlTWFuYWdlcjIuY3NzJztcbmltcG9ydCB7RnJhZ21lbnR9IGZyb20gXCJyZWFjdFwiO1xuXG5jb25zdCBUZXN0MkV4ZXJjaXNlTWFuYWdlciA9ICgpID0+IHtcbiAgICBjb25zdCBbbWVzc2FnZSwgc2V0TWVzc2FnZV0gPSBSZWFjdC51c2VTdGF0ZShcIk5vIHJlc3BvbnNlcyByZWNlaXZlZFwiKTtcbiAgICBjb25zdCBbaXNlcnJvciwgc2V0SXNFcnJvcl0gPSBSZWFjdC51c2VTdGF0ZShmYWxzZSk7XG5cbiAgICBjb25zdCBjbGFzc2VzID0gY2xhc3NOYW1lcyh7XG4gICAgICAgIFwidGVzdC1leGVyY2lzZS1tYW5hZ2VyLW1lc3NhZ2VcIjogdHJ1ZSxcbiAgICAgICAgXCJlcnJvclwiOiBpc2Vycm9yXG4gICAgfSk7XG5cbiAgICBSZWFjdC51c2VFZmZlY3QoKCkgPT4ge1xuICAgICAgICBjb25zb2xlLmxvZyhcIlRlc3QyRXhlcmNpc2VNYW5hZ2VyIHN1YnNjcmliaW5nIHRvIFsnYWNrJywnZXJyb3InXSBldmVudHNcIik7XG4gICAgICAgIGNvbnN0IGNhbGxiYWNrID0gKG1lc3NhZ2UpID0+IHtcbiAgICAgICAgICAgIHNldElzRXJyb3IobWVzc2FnZS5jb21tYW5kID09PSAnZXJyb3InKTtcbiAgICAgICAgICAgIHNldE1lc3NhZ2UobWVzc2FnZS5kYXRhLm1lc3NhZ2UpO1xuICAgICAgICAgICAgY29uc29sZS5sb2cobWVzc2FnZS5kYXRhLm1lc3NhZ2UpO1xuICAgICAgICB9O1xuXG4gICAgICAgIFJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzLmNvbW1zTWFuYWdlci5zdWJzY3JpYmUoWydhY2snLCAnZXJyb3InXSxcbiAgICAgICAgICAgIGNhbGxiYWNrKTtcblxuICAgICAgICByZXR1cm4gKCkgPT4ge1xuICAgICAgICAgICAgY29uc29sZS5sb2coXCJUZXN0MkV4ZXJjaXNlTWFuYWdlciB1bnN1YnNjcmliaW5nIGZyb20gWydhY2snLCdlcnJvciddIGV2ZW50c1wiKTtcbiAgICAgICAgICAgIFJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzLmNvbW1zTWFuYWdlci51bnN1YnNjcmliZShbJ2FjaycsICdlcnJvciddLFxuICAgICAgICAgICAgICAgIGNhbGxiYWNrKTtcbiAgICAgICAgfVxuICAgIH0sIFtdKTtcblxuICAgIHJldHVybiAoXG4gICAgICAgIDxGcmFnbWVudD5cbiAgICAgICAgICAgIDxociAvPlxuICAgICAgICAgICAgPGRpdiBjbGFzc05hbWU9e2NsYXNzZXN9PnttZXNzYWdlfTwvZGl2PlxuICAgICAgICA8L0ZyYWdtZW50PlxuICAgIClcbn1cblxuZXhwb3J0IGRlZmF1bHQgVGVzdDJFeGVyY2lzZU1hbmFnZXI7IiwiLyohXG5cdENvcHlyaWdodCAoYykgMjAxOCBKZWQgV2F0c29uLlxuXHRMaWNlbnNlZCB1bmRlciB0aGUgTUlUIExpY2Vuc2UgKE1JVCksIHNlZVxuXHRodHRwOi8vamVkd2F0c29uLmdpdGh1Yi5pby9jbGFzc25hbWVzXG4qL1xuLyogZ2xvYmFsIGRlZmluZSAqL1xuXG4oZnVuY3Rpb24gKCkge1xuXHQndXNlIHN0cmljdCc7XG5cblx0dmFyIGhhc093biA9IHt9Lmhhc093blByb3BlcnR5O1xuXHR2YXIgbmF0aXZlQ29kZVN0cmluZyA9ICdbbmF0aXZlIGNvZGVdJztcblxuXHRmdW5jdGlvbiBjbGFzc05hbWVzKCkge1xuXHRcdHZhciBjbGFzc2VzID0gW107XG5cblx0XHRmb3IgKHZhciBpID0gMDsgaSA8IGFyZ3VtZW50cy5sZW5ndGg7IGkrKykge1xuXHRcdFx0dmFyIGFyZyA9IGFyZ3VtZW50c1tpXTtcblx0XHRcdGlmICghYXJnKSBjb250aW51ZTtcblxuXHRcdFx0dmFyIGFyZ1R5cGUgPSB0eXBlb2YgYXJnO1xuXG5cdFx0XHRpZiAoYXJnVHlwZSA9PT0gJ3N0cmluZycgfHwgYXJnVHlwZSA9PT0gJ251bWJlcicpIHtcblx0XHRcdFx0Y2xhc3Nlcy5wdXNoKGFyZyk7XG5cdFx0XHR9IGVsc2UgaWYgKEFycmF5LmlzQXJyYXkoYXJnKSkge1xuXHRcdFx0XHRpZiAoYXJnLmxlbmd0aCkge1xuXHRcdFx0XHRcdHZhciBpbm5lciA9IGNsYXNzTmFtZXMuYXBwbHkobnVsbCwgYXJnKTtcblx0XHRcdFx0XHRpZiAoaW5uZXIpIHtcblx0XHRcdFx0XHRcdGNsYXNzZXMucHVzaChpbm5lcik7XG5cdFx0XHRcdFx0fVxuXHRcdFx0XHR9XG5cdFx0XHR9IGVsc2UgaWYgKGFyZ1R5cGUgPT09ICdvYmplY3QnKSB7XG5cdFx0XHRcdGlmIChhcmcudG9TdHJpbmcgIT09IE9iamVjdC5wcm90b3R5cGUudG9TdHJpbmcgJiYgIWFyZy50b1N0cmluZy50b1N0cmluZygpLmluY2x1ZGVzKCdbbmF0aXZlIGNvZGVdJykpIHtcblx0XHRcdFx0XHRjbGFzc2VzLnB1c2goYXJnLnRvU3RyaW5nKCkpO1xuXHRcdFx0XHRcdGNvbnRpbnVlO1xuXHRcdFx0XHR9XG5cblx0XHRcdFx0Zm9yICh2YXIga2V5IGluIGFyZykge1xuXHRcdFx0XHRcdGlmIChoYXNPd24uY2FsbChhcmcsIGtleSkgJiYgYXJnW2tleV0pIHtcblx0XHRcdFx0XHRcdGNsYXNzZXMucHVzaChrZXkpO1xuXHRcdFx0XHRcdH1cblx0XHRcdFx0fVxuXHRcdFx0fVxuXHRcdH1cblxuXHRcdHJldHVybiBjbGFzc2VzLmpvaW4oJyAnKTtcblx0fVxuXG5cdGlmICh0eXBlb2YgbW9kdWxlICE9PSAndW5kZWZpbmVkJyAmJiBtb2R1bGUuZXhwb3J0cykge1xuXHRcdGNsYXNzTmFtZXMuZGVmYXVsdCA9IGNsYXNzTmFtZXM7XG5cdFx0bW9kdWxlLmV4cG9ydHMgPSBjbGFzc05hbWVzO1xuXHR9IGVsc2UgaWYgKHR5cGVvZiBkZWZpbmUgPT09ICdmdW5jdGlvbicgJiYgdHlwZW9mIGRlZmluZS5hbWQgPT09ICdvYmplY3QnICYmIGRlZmluZS5hbWQpIHtcblx0XHQvLyByZWdpc3RlciBhcyAnY2xhc3NuYW1lcycsIGNvbnNpc3RlbnQgd2l0aCBucG0gcGFja2FnZSBuYW1lXG5cdFx0ZGVmaW5lKCdjbGFzc25hbWVzJywgW10sIGZ1bmN0aW9uICgpIHtcblx0XHRcdHJldHVybiBjbGFzc05hbWVzO1xuXHRcdH0pO1xuXHR9IGVsc2Uge1xuXHRcdHdpbmRvdy5jbGFzc05hbWVzID0gY2xhc3NOYW1lcztcblx0fVxufSgpKTtcbiIsIi8vIGV4dHJhY3RlZCBieSBtaW5pLWNzcy1leHRyYWN0LXBsdWdpblxuZXhwb3J0IHt9OyJdLCJuYW1lcyI6WyJSZWFjdCIsImNsYXNzTmFtZXMiLCJGcmFnbWVudCIsIlRlc3QyRXhlcmNpc2VNYW5hZ2VyIiwidXNlU3RhdGUiLCJtZXNzYWdlIiwic2V0TWVzc2FnZSIsImlzZXJyb3IiLCJzZXRJc0Vycm9yIiwiY2xhc3NlcyIsInVzZUVmZmVjdCIsImNvbnNvbGUiLCJsb2ciLCJjYWxsYmFjayIsImNvbW1hbmQiLCJkYXRhIiwiUm9ib3RpY3NFeGVyY2lzZUNvbXBvbmVudHMiLCJjb21tc01hbmFnZXIiLCJzdWJzY3JpYmUiLCJ1bnN1YnNjcmliZSJdLCJzb3VyY2VSb290IjoiIn0=