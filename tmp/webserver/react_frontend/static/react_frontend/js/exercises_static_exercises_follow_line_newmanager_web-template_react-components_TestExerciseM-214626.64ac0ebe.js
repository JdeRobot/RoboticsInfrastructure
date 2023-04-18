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
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvZXhlcmNpc2VzX3N0YXRpY19leGVyY2lzZXNfZm9sbG93X2xpbmVfbmV3bWFuYWdlcl93ZWItdGVtcGxhdGVfcmVhY3QtY29tcG9uZW50c19UZXN0RXhlcmNpc2VNLTIxNDYyNi42NGFjMGViZS5qcyIsIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUFBK0I7QUFDcUI7QUFDcEI7QUFDSTtBQUVHO0FBQUE7QUFBQTtBQUV2QyxJQUFNTSxtQkFBbUIsR0FBRyxTQUF0QkEsbUJBQW1CLENBQUlDLEtBQUssRUFBSztFQUNyQyxnQkFBOEJKLCtDQUFRLENBQUMsRUFBRSxDQUFDO0lBQUE7SUFBbkNLLE9BQU87SUFBRUMsVUFBVTtFQUMxQixpQkFBOEJOLCtDQUFRLENBQUMsS0FBSyxDQUFDO0lBQUE7SUFBdENPLE9BQU87SUFBRUMsVUFBVTtFQUMxQixJQUFNQyxPQUFPLEdBQUdQLGlEQUFVLENBQUM7SUFDekIsK0JBQStCLEVBQUUsSUFBSTtJQUNyQyxPQUFPLEVBQUVLO0VBQ1gsQ0FBQyxDQUFDO0VBRUYsSUFBTUcsTUFBTSxHQUFHLFNBQVRBLE1BQU0sQ0FBSUMsT0FBTyxFQUFLO0lBQzFCLElBQU1DLE1BQU0sR0FBR0MsSUFBSSxDQUFDQyxLQUFLLENBQUNDLFFBQVEsQ0FBQ0MsY0FBYyxDQUFDLGlCQUFpQixDQUFDLENBQUNDLFdBQVcsQ0FBQztJQUVqRkMsMEJBQTBCLENBQUNDLFlBQVksQ0FBQ1QsTUFBTSxDQUFDRSxNQUFNLENBQUMsQ0FDckRRLElBQUksQ0FBQyxVQUFDZixPQUFPLEVBQUs7TUFDakJDLFVBQVUsQ0FBQyxPQUFPLENBQUM7TUFDbkJFLFVBQVUsQ0FBQyxLQUFLLENBQUM7SUFDbkIsQ0FBQyxDQUFDLFNBQU0sQ0FBQyxVQUFDYSxRQUFRLEVBQUs7TUFDckJmLFVBQVUseUNBQWtDZSxRQUFRLENBQUNDLElBQUksQ0FBQ2pCLE9BQU8sRUFBRztNQUNwRUcsVUFBVSxDQUFDLElBQUksQ0FBQztJQUNsQixDQUFDLENBQUM7RUFDSixDQUFDO0VBRUQsSUFBTWUsT0FBTyxHQUFHLFNBQVZBLE9BQU8sQ0FBSVosT0FBTyxFQUFLO0lBQzNCTywwQkFBMEIsQ0FBQ0MsWUFBWSxDQUFDSSxPQUFPLEVBQUUsQ0FDaERILElBQUksQ0FBQyxVQUFDZixPQUFPLEVBQUs7TUFDakJDLFVBQVUsQ0FBQyxXQUFXLENBQUM7TUFDdkJFLFVBQVUsQ0FBQyxLQUFLLENBQUM7SUFDbkIsQ0FBQyxDQUFDLFNBQU0sQ0FBQyxVQUFDYSxRQUFRLEVBQUs7TUFDckJmLFVBQVUseUNBQWtDZSxRQUFRLENBQUNDLElBQUksQ0FBQ2pCLE9BQU8sRUFBRztNQUNwRUcsVUFBVSxDQUFDLElBQUksQ0FBQztJQUNsQixDQUFDLENBQUM7RUFDSixDQUFDO0VBRUQsb0JBQ0ksd0RBQUMsMkNBQVE7SUFBQSx3QkFDUDtNQUFLLFNBQVMsRUFBRSx1QkFBd0I7TUFBQyxPQUFPLEVBQUVlLE9BQVE7TUFBQTtJQUFBLEVBQWMsZUFDeEU7TUFBSyxTQUFTLEVBQUUsdUJBQXdCO01BQUMsT0FBTyxFQUFFYixNQUFPO01BQUE7SUFBQSxFQUFhLGVBRXRFO01BQUssU0FBUyxFQUFFRCxPQUFRO01BQUEsVUFBRUo7SUFBTyxFQUFPO0VBQUEsRUFDL0I7QUFFakIsQ0FBQztBQUVELGlFQUFlRixtQkFBbUI7Ozs7Ozs7Ozs7QUNqRGxDO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBOztBQUVBLGdCQUFnQjtBQUNoQjs7QUFFQTtBQUNBOztBQUVBLGtCQUFrQixzQkFBc0I7QUFDeEM7QUFDQTs7QUFFQTs7QUFFQTtBQUNBO0FBQ0EsS0FBSztBQUNMO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUFFQTtBQUNBOztBQUVBLEtBQUssS0FBNkI7QUFDbEM7QUFDQTtBQUNBLEdBQUcsU0FBUyxJQUE0RTtBQUN4RjtBQUNBLEVBQUUsaUNBQXFCLEVBQUUsbUNBQUU7QUFDM0I7QUFDQSxHQUFHO0FBQUEsa0dBQUM7QUFDSixHQUFHLEtBQUssRUFFTjtBQUNGLENBQUM7Ozs7Ozs7Ozs7Ozs7QUMzREQiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly9yZWFjdF9mcm9udGVuZC8uLi9leGVyY2lzZXMvc3RhdGljL2V4ZXJjaXNlcy9mb2xsb3dfbGluZV9uZXdtYW5hZ2VyL3dlYi10ZW1wbGF0ZS9yZWFjdC1jb21wb25lbnRzL1Rlc3RFeGVyY2lzZU1hbmFnZXIuanMiLCJ3ZWJwYWNrOi8vcmVhY3RfZnJvbnRlbmQvLi9ub2RlX21vZHVsZXMvY2xhc3NuYW1lcy9pbmRleC5qcyIsIndlYnBhY2s6Ly9yZWFjdF9mcm9udGVuZC8uLi9leGVyY2lzZXMvc3RhdGljL2V4ZXJjaXNlcy9mb2xsb3dfbGluZV9uZXdtYW5hZ2VyL3dlYi10ZW1wbGF0ZS9yZWFjdC1jb21wb25lbnRzL2Nzcy9UZXN0RXhlcmNpc2VNYW5hZ2VyLmNzcz9jMzhlIl0sInNvdXJjZXNDb250ZW50IjpbImltcG9ydCAqIGFzIFJlYWN0IGZyb20gJ3JlYWN0JztcbmltcG9ydCB7RnJhZ21lbnQsIHVzZUVmZmVjdCwgdXNlU3RhdGV9IGZyb20gJ3JlYWN0JztcbmltcG9ydCAqIGFzIGxvZyBmcm9tICdsb2dsZXZlbCc7XG5pbXBvcnQgY2xhc3NOYW1lcyBmcm9tICdjbGFzc25hbWVzJztcblxuaW1wb3J0ICcuL2Nzcy9UZXN0RXhlcmNpc2VNYW5hZ2VyLmNzcyc7XG5cbmNvbnN0IFRlc3RFeGVyY2lzZU1hbmFnZXIgPSAocHJvcHMpID0+IHtcbiAgY29uc3QgW21lc3NhZ2UsIHNldE1lc3NhZ2VdID0gdXNlU3RhdGUoXCJcIik7XG4gIGNvbnN0IFtpc2Vycm9yLCBzZXRJc2Vycm9yXSA9IHVzZVN0YXRlKGZhbHNlKTtcbiAgY29uc3QgY2xhc3NlcyA9IGNsYXNzTmFtZXMoe1xuICAgIFwidGVzdC1leGVyY2lzZS1tYW5hZ2VyLW1lc3NhZ2VcIjogdHJ1ZSxcbiAgICBcImVycm9yXCI6IGlzZXJyb3JcbiAgfSk7XG5cbiAgY29uc3QgbGF1bmNoID0gKGNvbW1hbmQpID0+IHtcbiAgICBjb25zdCBjb25maWcgPSBKU09OLnBhcnNlKGRvY3VtZW50LmdldEVsZW1lbnRCeUlkKFwiZXhlcmNpc2UtY29uZmlnXCIpLnRleHRDb250ZW50KTtcblxuICAgIFJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzLmNvbW1zTWFuYWdlci5sYXVuY2goY29uZmlnKVxuICAgIC50aGVuKChtZXNzYWdlKSA9PiB7XG4gICAgICBzZXRNZXNzYWdlKFwiUmVhZHlcIik7XG4gICAgICBzZXRJc2Vycm9yKGZhbHNlKTtcbiAgICB9KS5jYXRjaCgocmVzcG9uc2UpID0+IHtcbiAgICAgIHNldE1lc3NhZ2UoYE1lc3NhZ2Ugbm90IHJlY2VpdmVkLCByZWFzb246ICR7cmVzcG9uc2UuZGF0YS5tZXNzYWdlfWApO1xuICAgICAgc2V0SXNlcnJvcih0cnVlKTtcbiAgICB9KVxuICB9O1xuXG4gIGNvbnN0IGNvbm5lY3QgPSAoY29tbWFuZCkgPT4ge1xuICAgIFJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzLmNvbW1zTWFuYWdlci5jb25uZWN0KClcbiAgICAudGhlbigobWVzc2FnZSkgPT4ge1xuICAgICAgc2V0TWVzc2FnZShcIkNvbm5lY3RlZFwiKTtcbiAgICAgIHNldElzZXJyb3IoZmFsc2UpO1xuICAgIH0pLmNhdGNoKChyZXNwb25zZSkgPT4ge1xuICAgICAgc2V0TWVzc2FnZShgTWVzc2FnZSBub3QgcmVjZWl2ZWQsIHJlYXNvbjogJHtyZXNwb25zZS5kYXRhLm1lc3NhZ2V9YCk7XG4gICAgICBzZXRJc2Vycm9yKHRydWUpO1xuICAgIH0pXG4gIH07XG5cbiAgcmV0dXJuIChcbiAgICAgIDxGcmFnbWVudD5cbiAgICAgICAgPGRpdiBjbGFzc05hbWU9e1widGVzdC1leGVyY2lzZS1tYW5hZ2VyXCJ9IG9uQ2xpY2s9e2Nvbm5lY3R9PkNvbm5lY3Q8L2Rpdj5cbiAgICAgICAgPGRpdiBjbGFzc05hbWU9e1widGVzdC1leGVyY2lzZS1tYW5hZ2VyXCJ9IG9uQ2xpY2s9e2xhdW5jaH0+TGF1bmNoPC9kaXY+XG4gICAgICAgIFxuICAgICAgICA8ZGl2IGNsYXNzTmFtZT17Y2xhc3Nlc30+e21lc3NhZ2V9PC9kaXY+XG4gICAgICA8L0ZyYWdtZW50PlxuICApO1xufTtcblxuZXhwb3J0IGRlZmF1bHQgVGVzdEV4ZXJjaXNlTWFuYWdlcjsiLCIvKiFcblx0Q29weXJpZ2h0IChjKSAyMDE4IEplZCBXYXRzb24uXG5cdExpY2Vuc2VkIHVuZGVyIHRoZSBNSVQgTGljZW5zZSAoTUlUKSwgc2VlXG5cdGh0dHA6Ly9qZWR3YXRzb24uZ2l0aHViLmlvL2NsYXNzbmFtZXNcbiovXG4vKiBnbG9iYWwgZGVmaW5lICovXG5cbihmdW5jdGlvbiAoKSB7XG5cdCd1c2Ugc3RyaWN0JztcblxuXHR2YXIgaGFzT3duID0ge30uaGFzT3duUHJvcGVydHk7XG5cdHZhciBuYXRpdmVDb2RlU3RyaW5nID0gJ1tuYXRpdmUgY29kZV0nO1xuXG5cdGZ1bmN0aW9uIGNsYXNzTmFtZXMoKSB7XG5cdFx0dmFyIGNsYXNzZXMgPSBbXTtcblxuXHRcdGZvciAodmFyIGkgPSAwOyBpIDwgYXJndW1lbnRzLmxlbmd0aDsgaSsrKSB7XG5cdFx0XHR2YXIgYXJnID0gYXJndW1lbnRzW2ldO1xuXHRcdFx0aWYgKCFhcmcpIGNvbnRpbnVlO1xuXG5cdFx0XHR2YXIgYXJnVHlwZSA9IHR5cGVvZiBhcmc7XG5cblx0XHRcdGlmIChhcmdUeXBlID09PSAnc3RyaW5nJyB8fCBhcmdUeXBlID09PSAnbnVtYmVyJykge1xuXHRcdFx0XHRjbGFzc2VzLnB1c2goYXJnKTtcblx0XHRcdH0gZWxzZSBpZiAoQXJyYXkuaXNBcnJheShhcmcpKSB7XG5cdFx0XHRcdGlmIChhcmcubGVuZ3RoKSB7XG5cdFx0XHRcdFx0dmFyIGlubmVyID0gY2xhc3NOYW1lcy5hcHBseShudWxsLCBhcmcpO1xuXHRcdFx0XHRcdGlmIChpbm5lcikge1xuXHRcdFx0XHRcdFx0Y2xhc3Nlcy5wdXNoKGlubmVyKTtcblx0XHRcdFx0XHR9XG5cdFx0XHRcdH1cblx0XHRcdH0gZWxzZSBpZiAoYXJnVHlwZSA9PT0gJ29iamVjdCcpIHtcblx0XHRcdFx0aWYgKGFyZy50b1N0cmluZyAhPT0gT2JqZWN0LnByb3RvdHlwZS50b1N0cmluZyAmJiAhYXJnLnRvU3RyaW5nLnRvU3RyaW5nKCkuaW5jbHVkZXMoJ1tuYXRpdmUgY29kZV0nKSkge1xuXHRcdFx0XHRcdGNsYXNzZXMucHVzaChhcmcudG9TdHJpbmcoKSk7XG5cdFx0XHRcdFx0Y29udGludWU7XG5cdFx0XHRcdH1cblxuXHRcdFx0XHRmb3IgKHZhciBrZXkgaW4gYXJnKSB7XG5cdFx0XHRcdFx0aWYgKGhhc093bi5jYWxsKGFyZywga2V5KSAmJiBhcmdba2V5XSkge1xuXHRcdFx0XHRcdFx0Y2xhc3Nlcy5wdXNoKGtleSk7XG5cdFx0XHRcdFx0fVxuXHRcdFx0XHR9XG5cdFx0XHR9XG5cdFx0fVxuXG5cdFx0cmV0dXJuIGNsYXNzZXMuam9pbignICcpO1xuXHR9XG5cblx0aWYgKHR5cGVvZiBtb2R1bGUgIT09ICd1bmRlZmluZWQnICYmIG1vZHVsZS5leHBvcnRzKSB7XG5cdFx0Y2xhc3NOYW1lcy5kZWZhdWx0ID0gY2xhc3NOYW1lcztcblx0XHRtb2R1bGUuZXhwb3J0cyA9IGNsYXNzTmFtZXM7XG5cdH0gZWxzZSBpZiAodHlwZW9mIGRlZmluZSA9PT0gJ2Z1bmN0aW9uJyAmJiB0eXBlb2YgZGVmaW5lLmFtZCA9PT0gJ29iamVjdCcgJiYgZGVmaW5lLmFtZCkge1xuXHRcdC8vIHJlZ2lzdGVyIGFzICdjbGFzc25hbWVzJywgY29uc2lzdGVudCB3aXRoIG5wbSBwYWNrYWdlIG5hbWVcblx0XHRkZWZpbmUoJ2NsYXNzbmFtZXMnLCBbXSwgZnVuY3Rpb24gKCkge1xuXHRcdFx0cmV0dXJuIGNsYXNzTmFtZXM7XG5cdFx0fSk7XG5cdH0gZWxzZSB7XG5cdFx0d2luZG93LmNsYXNzTmFtZXMgPSBjbGFzc05hbWVzO1xuXHR9XG59KCkpO1xuIiwiLy8gZXh0cmFjdGVkIGJ5IG1pbmktY3NzLWV4dHJhY3QtcGx1Z2luXG5leHBvcnQge307Il0sIm5hbWVzIjpbIlJlYWN0IiwiRnJhZ21lbnQiLCJ1c2VFZmZlY3QiLCJ1c2VTdGF0ZSIsImxvZyIsImNsYXNzTmFtZXMiLCJUZXN0RXhlcmNpc2VNYW5hZ2VyIiwicHJvcHMiLCJtZXNzYWdlIiwic2V0TWVzc2FnZSIsImlzZXJyb3IiLCJzZXRJc2Vycm9yIiwiY2xhc3NlcyIsImxhdW5jaCIsImNvbW1hbmQiLCJjb25maWciLCJKU09OIiwicGFyc2UiLCJkb2N1bWVudCIsImdldEVsZW1lbnRCeUlkIiwidGV4dENvbnRlbnQiLCJSb2JvdGljc0V4ZXJjaXNlQ29tcG9uZW50cyIsImNvbW1zTWFuYWdlciIsInRoZW4iLCJyZXNwb25zZSIsImRhdGEiLCJjb25uZWN0Il0sInNvdXJjZVJvb3QiOiIifQ==