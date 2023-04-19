(self["webpackChunkreact_frontend"] = self["webpackChunkreact_frontend"] || []).push([["exercises_static_exercises_follow_line_newmanager_web-template_react-components_TestExerciseM-214626"],{

/***/ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/TestExerciseManager.js":
/*!*****************************************************************************************************************!*\
  !*** ../exercises/static/exercises/follow_line_newmanager/web-template/react-components/TestExerciseManager.js ***!
  \*****************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! react */ "./node_modules/react/index.js");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var loglevel__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! loglevel */ "./node_modules/loglevel/lib/loglevel.js");
/* harmony import */ var loglevel__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(loglevel__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var classnames__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! classnames */ "./node_modules/classnames/index.js");
/* harmony import */ var classnames__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(classnames__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _css_TestExerciseManager_css__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./css/TestExerciseManager.css */ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestExerciseManager.css");
/* harmony import */ var react_jsx_runtime__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! react/jsx-runtime */ "./node_modules/react/jsx-runtime.js");
function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }
function _iterableToArrayLimit(arr, i) { var _i = arr == null ? null : typeof Symbol !== "undefined" && arr[Symbol.iterator] || arr["@@iterator"]; if (_i == null) return; var _arr = []; var _n = true; var _d = false; var _s, _e; try { for (_i = _i.call(arr); !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"] != null) _i["return"](); } finally { if (_d) throw _e; } } return _arr; }
function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }







var TestExerciseManager = function TestExerciseManager(props) {
  var _useState = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(""),
    _useState2 = _slicedToArray(_useState, 2),
    message = _useState2[0],
    setMessage = _useState2[1];
  var _useState3 = (0,react__WEBPACK_IMPORTED_MODULE_0__.useState)(false),
    _useState4 = _slicedToArray(_useState3, 2),
    iserror = _useState4[0],
    setIserror = _useState4[1];
  var classes = classnames__WEBPACK_IMPORTED_MODULE_2___default()({
    "test-exercise-manager-message": true,
    "error": iserror
  });
  var launch = function launch(command) {
    var config = JSON.parse(document.getElementById("exercise-config").textContent);
    RoboticsExerciseComponents.commsManager.launch(config).then(function (message) {
      setMessage("Ready");
      setIserror(false);
    })["catch"](function (response) {
      setMessage("Message not received, reason: ".concat(response.data.message));
      setIserror(true);
    });
  };
  var connect = function connect(command) {
    RoboticsExerciseComponents.commsManager.connect().then(function (message) {
      setMessage("Connected");
      setIserror(false);
    })["catch"](function (response) {
      setMessage("Message not received, reason: ".concat(response.data.message));
      setIserror(true);
    });
  };
  return /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_4__.jsxs)(react__WEBPACK_IMPORTED_MODULE_0__.Fragment, {
    children: [/*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_4__.jsx)("div", {
      className: "test-exercise-manager",
      onClick: connect,
      children: "Connect"
    }), /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_4__.jsx)("div", {
      className: "test-exercise-manager",
      onClick: launch,
      children: "Launch"
    }), /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_4__.jsx)("div", {
      className: classes,
      children: message
    })]
  });
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (TestExerciseManager);

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

/***/ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestExerciseManager.css":
/*!**********************************************************************************************************************!*\
  !*** ../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestExerciseManager.css ***!
  \**********************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ })

}]);
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvZXhlcmNpc2VzX3N0YXRpY19leGVyY2lzZXNfZm9sbG93X2xpbmVfbmV3bWFuYWdlcl93ZWItdGVtcGxhdGVfcmVhY3QtY29tcG9uZW50c19UZXN0RXhlcmNpc2VNLTIxNDYyNi5hOGY5MDU0Mi5qcyIsIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUFBK0I7QUFDcUI7QUFDcEI7QUFDSTtBQUVHO0FBQUE7QUFBQTtBQUV2QyxJQUFNTSxtQkFBbUIsR0FBRyxTQUF0QkEsbUJBQW1CLENBQUlDLEtBQUssRUFBSztFQUNyQyxnQkFBOEJKLCtDQUFRLENBQUMsRUFBRSxDQUFDO0lBQUE7SUFBbkNLLE9BQU87SUFBRUMsVUFBVTtFQUMxQixpQkFBOEJOLCtDQUFRLENBQUMsS0FBSyxDQUFDO0lBQUE7SUFBdENPLE9BQU87SUFBRUMsVUFBVTtFQUMxQixJQUFNQyxPQUFPLEdBQUdQLGlEQUFVLENBQUM7SUFDekIsK0JBQStCLEVBQUUsSUFBSTtJQUNyQyxPQUFPLEVBQUVLO0VBQ1gsQ0FBQyxDQUFDO0VBRUYsSUFBTUcsTUFBTSxHQUFHLFNBQVRBLE1BQU0sQ0FBSUMsT0FBTyxFQUFLO0lBQzFCLElBQU1DLE1BQU0sR0FBR0MsSUFBSSxDQUFDQyxLQUFLLENBQUNDLFFBQVEsQ0FBQ0MsY0FBYyxDQUFDLGlCQUFpQixDQUFDLENBQUNDLFdBQVcsQ0FBQztJQUVqRkMsMEJBQTBCLENBQUNDLFlBQVksQ0FBQ1QsTUFBTSxDQUFDRSxNQUFNLENBQUMsQ0FDckRRLElBQUksQ0FBQyxVQUFDZixPQUFPLEVBQUs7TUFDakJDLFVBQVUsQ0FBQyxPQUFPLENBQUM7TUFDbkJFLFVBQVUsQ0FBQyxLQUFLLENBQUM7SUFDbkIsQ0FBQyxDQUFDLFNBQU0sQ0FBQyxVQUFDYSxRQUFRLEVBQUs7TUFDckJmLFVBQVUseUNBQWtDZSxRQUFRLENBQUNDLElBQUksQ0FBQ2pCLE9BQU8sRUFBRztNQUNwRUcsVUFBVSxDQUFDLElBQUksQ0FBQztJQUNsQixDQUFDLENBQUM7RUFDSixDQUFDO0VBRUQsSUFBTWUsT0FBTyxHQUFHLFNBQVZBLE9BQU8sQ0FBSVosT0FBTyxFQUFLO0lBQzNCTywwQkFBMEIsQ0FBQ0MsWUFBWSxDQUFDSSxPQUFPLEVBQUUsQ0FDaERILElBQUksQ0FBQyxVQUFDZixPQUFPLEVBQUs7TUFDakJDLFVBQVUsQ0FBQyxXQUFXLENBQUM7TUFDdkJFLFVBQVUsQ0FBQyxLQUFLLENBQUM7SUFDbkIsQ0FBQyxDQUFDLFNBQU0sQ0FBQyxVQUFDYSxRQUFRLEVBQUs7TUFDckJmLFVBQVUseUNBQWtDZSxRQUFRLENBQUNDLElBQUksQ0FBQ2pCLE9BQU8sRUFBRztNQUNwRUcsVUFBVSxDQUFDLElBQUksQ0FBQztJQUNsQixDQUFDLENBQUM7RUFDSixDQUFDO0VBRUQsb0JBQ0ksd0RBQUMsMkNBQVE7SUFBQSx3QkFDUDtNQUFLLFNBQVMsRUFBRSx1QkFBd0I7TUFBQyxPQUFPLEVBQUVlLE9BQVE7TUFBQSxVQUFDO0lBQU8sRUFBTSxlQUN4RTtNQUFLLFNBQVMsRUFBRSx1QkFBd0I7TUFBQyxPQUFPLEVBQUViLE1BQU87TUFBQSxVQUFDO0lBQU0sRUFBTSxlQUV0RTtNQUFLLFNBQVMsRUFBRUQsT0FBUTtNQUFBLFVBQUVKO0lBQU8sRUFBTztFQUFBLEVBQy9CO0FBRWpCLENBQUM7QUFFRCxpRUFBZUYsbUJBQW1COzs7Ozs7Ozs7O0FDakRsQztBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTs7QUFFQSxnQkFBZ0I7QUFDaEI7O0FBRUE7QUFDQTs7QUFFQSxrQkFBa0Isc0JBQXNCO0FBQ3hDO0FBQ0E7O0FBRUE7O0FBRUE7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTs7QUFFQSxLQUFLLEtBQTZCO0FBQ2xDO0FBQ0E7QUFDQSxHQUFHLFNBQVMsSUFBNEU7QUFDeEY7QUFDQSxFQUFFLGlDQUFxQixFQUFFLG1DQUFFO0FBQzNCO0FBQ0EsR0FBRztBQUFBLGtHQUFDO0FBQ0osR0FBRyxLQUFLLEVBRU47QUFDRixDQUFDOzs7Ozs7Ozs7Ozs7O0FDM0REIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vcmVhY3RfZnJvbnRlbmQvLi4vZXhlcmNpc2VzL3N0YXRpYy9leGVyY2lzZXMvZm9sbG93X2xpbmVfbmV3bWFuYWdlci93ZWItdGVtcGxhdGUvcmVhY3QtY29tcG9uZW50cy9UZXN0RXhlcmNpc2VNYW5hZ2VyLmpzIiwid2VicGFjazovL3JlYWN0X2Zyb250ZW5kLy4vbm9kZV9tb2R1bGVzL2NsYXNzbmFtZXMvaW5kZXguanMiLCJ3ZWJwYWNrOi8vcmVhY3RfZnJvbnRlbmQvLi4vZXhlcmNpc2VzL3N0YXRpYy9leGVyY2lzZXMvZm9sbG93X2xpbmVfbmV3bWFuYWdlci93ZWItdGVtcGxhdGUvcmVhY3QtY29tcG9uZW50cy9jc3MvVGVzdEV4ZXJjaXNlTWFuYWdlci5jc3M/YzM4ZSJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgKiBhcyBSZWFjdCBmcm9tICdyZWFjdCc7XG5pbXBvcnQge0ZyYWdtZW50LCB1c2VFZmZlY3QsIHVzZVN0YXRlfSBmcm9tICdyZWFjdCc7XG5pbXBvcnQgKiBhcyBsb2cgZnJvbSAnbG9nbGV2ZWwnO1xuaW1wb3J0IGNsYXNzTmFtZXMgZnJvbSAnY2xhc3NuYW1lcyc7XG5cbmltcG9ydCAnLi9jc3MvVGVzdEV4ZXJjaXNlTWFuYWdlci5jc3MnO1xuXG5jb25zdCBUZXN0RXhlcmNpc2VNYW5hZ2VyID0gKHByb3BzKSA9PiB7XG4gIGNvbnN0IFttZXNzYWdlLCBzZXRNZXNzYWdlXSA9IHVzZVN0YXRlKFwiXCIpO1xuICBjb25zdCBbaXNlcnJvciwgc2V0SXNlcnJvcl0gPSB1c2VTdGF0ZShmYWxzZSk7XG4gIGNvbnN0IGNsYXNzZXMgPSBjbGFzc05hbWVzKHtcbiAgICBcInRlc3QtZXhlcmNpc2UtbWFuYWdlci1tZXNzYWdlXCI6IHRydWUsXG4gICAgXCJlcnJvclwiOiBpc2Vycm9yXG4gIH0pO1xuXG4gIGNvbnN0IGxhdW5jaCA9IChjb21tYW5kKSA9PiB7XG4gICAgY29uc3QgY29uZmlnID0gSlNPTi5wYXJzZShkb2N1bWVudC5nZXRFbGVtZW50QnlJZChcImV4ZXJjaXNlLWNvbmZpZ1wiKS50ZXh0Q29udGVudCk7XG5cbiAgICBSb2JvdGljc0V4ZXJjaXNlQ29tcG9uZW50cy5jb21tc01hbmFnZXIubGF1bmNoKGNvbmZpZylcbiAgICAudGhlbigobWVzc2FnZSkgPT4ge1xuICAgICAgc2V0TWVzc2FnZShcIlJlYWR5XCIpO1xuICAgICAgc2V0SXNlcnJvcihmYWxzZSk7XG4gICAgfSkuY2F0Y2goKHJlc3BvbnNlKSA9PiB7XG4gICAgICBzZXRNZXNzYWdlKGBNZXNzYWdlIG5vdCByZWNlaXZlZCwgcmVhc29uOiAke3Jlc3BvbnNlLmRhdGEubWVzc2FnZX1gKTtcbiAgICAgIHNldElzZXJyb3IodHJ1ZSk7XG4gICAgfSlcbiAgfTtcblxuICBjb25zdCBjb25uZWN0ID0gKGNvbW1hbmQpID0+IHtcbiAgICBSb2JvdGljc0V4ZXJjaXNlQ29tcG9uZW50cy5jb21tc01hbmFnZXIuY29ubmVjdCgpXG4gICAgLnRoZW4oKG1lc3NhZ2UpID0+IHtcbiAgICAgIHNldE1lc3NhZ2UoXCJDb25uZWN0ZWRcIik7XG4gICAgICBzZXRJc2Vycm9yKGZhbHNlKTtcbiAgICB9KS5jYXRjaCgocmVzcG9uc2UpID0+IHtcbiAgICAgIHNldE1lc3NhZ2UoYE1lc3NhZ2Ugbm90IHJlY2VpdmVkLCByZWFzb246ICR7cmVzcG9uc2UuZGF0YS5tZXNzYWdlfWApO1xuICAgICAgc2V0SXNlcnJvcih0cnVlKTtcbiAgICB9KVxuICB9O1xuXG4gIHJldHVybiAoXG4gICAgICA8RnJhZ21lbnQ+XG4gICAgICAgIDxkaXYgY2xhc3NOYW1lPXtcInRlc3QtZXhlcmNpc2UtbWFuYWdlclwifSBvbkNsaWNrPXtjb25uZWN0fT5Db25uZWN0PC9kaXY+XG4gICAgICAgIDxkaXYgY2xhc3NOYW1lPXtcInRlc3QtZXhlcmNpc2UtbWFuYWdlclwifSBvbkNsaWNrPXtsYXVuY2h9PkxhdW5jaDwvZGl2PlxuICAgICAgICBcbiAgICAgICAgPGRpdiBjbGFzc05hbWU9e2NsYXNzZXN9PnttZXNzYWdlfTwvZGl2PlxuICAgICAgPC9GcmFnbWVudD5cbiAgKTtcbn07XG5cbmV4cG9ydCBkZWZhdWx0IFRlc3RFeGVyY2lzZU1hbmFnZXI7IiwiLyohXG5cdENvcHlyaWdodCAoYykgMjAxOCBKZWQgV2F0c29uLlxuXHRMaWNlbnNlZCB1bmRlciB0aGUgTUlUIExpY2Vuc2UgKE1JVCksIHNlZVxuXHRodHRwOi8vamVkd2F0c29uLmdpdGh1Yi5pby9jbGFzc25hbWVzXG4qL1xuLyogZ2xvYmFsIGRlZmluZSAqL1xuXG4oZnVuY3Rpb24gKCkge1xuXHQndXNlIHN0cmljdCc7XG5cblx0dmFyIGhhc093biA9IHt9Lmhhc093blByb3BlcnR5O1xuXHR2YXIgbmF0aXZlQ29kZVN0cmluZyA9ICdbbmF0aXZlIGNvZGVdJztcblxuXHRmdW5jdGlvbiBjbGFzc05hbWVzKCkge1xuXHRcdHZhciBjbGFzc2VzID0gW107XG5cblx0XHRmb3IgKHZhciBpID0gMDsgaSA8IGFyZ3VtZW50cy5sZW5ndGg7IGkrKykge1xuXHRcdFx0dmFyIGFyZyA9IGFyZ3VtZW50c1tpXTtcblx0XHRcdGlmICghYXJnKSBjb250aW51ZTtcblxuXHRcdFx0dmFyIGFyZ1R5cGUgPSB0eXBlb2YgYXJnO1xuXG5cdFx0XHRpZiAoYXJnVHlwZSA9PT0gJ3N0cmluZycgfHwgYXJnVHlwZSA9PT0gJ251bWJlcicpIHtcblx0XHRcdFx0Y2xhc3Nlcy5wdXNoKGFyZyk7XG5cdFx0XHR9IGVsc2UgaWYgKEFycmF5LmlzQXJyYXkoYXJnKSkge1xuXHRcdFx0XHRpZiAoYXJnLmxlbmd0aCkge1xuXHRcdFx0XHRcdHZhciBpbm5lciA9IGNsYXNzTmFtZXMuYXBwbHkobnVsbCwgYXJnKTtcblx0XHRcdFx0XHRpZiAoaW5uZXIpIHtcblx0XHRcdFx0XHRcdGNsYXNzZXMucHVzaChpbm5lcik7XG5cdFx0XHRcdFx0fVxuXHRcdFx0XHR9XG5cdFx0XHR9IGVsc2UgaWYgKGFyZ1R5cGUgPT09ICdvYmplY3QnKSB7XG5cdFx0XHRcdGlmIChhcmcudG9TdHJpbmcgIT09IE9iamVjdC5wcm90b3R5cGUudG9TdHJpbmcgJiYgIWFyZy50b1N0cmluZy50b1N0cmluZygpLmluY2x1ZGVzKCdbbmF0aXZlIGNvZGVdJykpIHtcblx0XHRcdFx0XHRjbGFzc2VzLnB1c2goYXJnLnRvU3RyaW5nKCkpO1xuXHRcdFx0XHRcdGNvbnRpbnVlO1xuXHRcdFx0XHR9XG5cblx0XHRcdFx0Zm9yICh2YXIga2V5IGluIGFyZykge1xuXHRcdFx0XHRcdGlmIChoYXNPd24uY2FsbChhcmcsIGtleSkgJiYgYXJnW2tleV0pIHtcblx0XHRcdFx0XHRcdGNsYXNzZXMucHVzaChrZXkpO1xuXHRcdFx0XHRcdH1cblx0XHRcdFx0fVxuXHRcdFx0fVxuXHRcdH1cblxuXHRcdHJldHVybiBjbGFzc2VzLmpvaW4oJyAnKTtcblx0fVxuXG5cdGlmICh0eXBlb2YgbW9kdWxlICE9PSAndW5kZWZpbmVkJyAmJiBtb2R1bGUuZXhwb3J0cykge1xuXHRcdGNsYXNzTmFtZXMuZGVmYXVsdCA9IGNsYXNzTmFtZXM7XG5cdFx0bW9kdWxlLmV4cG9ydHMgPSBjbGFzc05hbWVzO1xuXHR9IGVsc2UgaWYgKHR5cGVvZiBkZWZpbmUgPT09ICdmdW5jdGlvbicgJiYgdHlwZW9mIGRlZmluZS5hbWQgPT09ICdvYmplY3QnICYmIGRlZmluZS5hbWQpIHtcblx0XHQvLyByZWdpc3RlciBhcyAnY2xhc3NuYW1lcycsIGNvbnNpc3RlbnQgd2l0aCBucG0gcGFja2FnZSBuYW1lXG5cdFx0ZGVmaW5lKCdjbGFzc25hbWVzJywgW10sIGZ1bmN0aW9uICgpIHtcblx0XHRcdHJldHVybiBjbGFzc05hbWVzO1xuXHRcdH0pO1xuXHR9IGVsc2Uge1xuXHRcdHdpbmRvdy5jbGFzc05hbWVzID0gY2xhc3NOYW1lcztcblx0fVxufSgpKTtcbiIsIi8vIGV4dHJhY3RlZCBieSBtaW5pLWNzcy1leHRyYWN0LXBsdWdpblxuZXhwb3J0IHt9OyJdLCJuYW1lcyI6WyJSZWFjdCIsIkZyYWdtZW50IiwidXNlRWZmZWN0IiwidXNlU3RhdGUiLCJsb2ciLCJjbGFzc05hbWVzIiwiVGVzdEV4ZXJjaXNlTWFuYWdlciIsInByb3BzIiwibWVzc2FnZSIsInNldE1lc3NhZ2UiLCJpc2Vycm9yIiwic2V0SXNlcnJvciIsImNsYXNzZXMiLCJsYXVuY2giLCJjb21tYW5kIiwiY29uZmlnIiwiSlNPTiIsInBhcnNlIiwiZG9jdW1lbnQiLCJnZXRFbGVtZW50QnlJZCIsInRleHRDb250ZW50IiwiUm9ib3RpY3NFeGVyY2lzZUNvbXBvbmVudHMiLCJjb21tc01hbmFnZXIiLCJ0aGVuIiwicmVzcG9uc2UiLCJkYXRhIiwiY29ubmVjdCJdLCJzb3VyY2VSb290IjoiIn0=