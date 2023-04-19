(self["webpackChunkreact_frontend"] = self["webpackChunkreact_frontend"] || []).push([["exercises_static_exercises_follow_line_newmanager_web-template_react-components_TestShowScreen_js"],{

/***/ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/TestShowScreen.js":
/*!************************************************************************************************************!*\
  !*** ../exercises/static/exercises/follow_line_newmanager/web-template/react-components/TestShowScreen.js ***!
  \************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! react */ "./node_modules/react/index.js");
/* harmony import */ var react__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(react__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _css_TestShowScreen_css__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./css/TestShowScreen.css */ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestShowScreen.css");
/* harmony import */ var classnames__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! classnames */ "./node_modules/classnames/index.js");
/* harmony import */ var classnames__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(classnames__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! react/jsx-runtime */ "./node_modules/react/jsx-runtime.js");
function _slicedToArray(arr, i) { return _arrayWithHoles(arr) || _iterableToArrayLimit(arr, i) || _unsupportedIterableToArray(arr, i) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(o, minLen) { if (!o) return; if (typeof o === "string") return _arrayLikeToArray(o, minLen); var n = Object.prototype.toString.call(o).slice(8, -1); if (n === "Object" && o.constructor) n = o.constructor.name; if (n === "Map" || n === "Set") return Array.from(o); if (n === "Arguments" || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)) return _arrayLikeToArray(o, minLen); }
function _arrayLikeToArray(arr, len) { if (len == null || len > arr.length) len = arr.length; for (var i = 0, arr2 = new Array(len); i < len; i++) { arr2[i] = arr[i]; } return arr2; }
function _iterableToArrayLimit(arr, i) { var _i = arr == null ? null : typeof Symbol !== "undefined" && arr[Symbol.iterator] || arr["@@iterator"]; if (_i == null) return; var _arr = []; var _n = true; var _d = false; var _s, _e; try { for (_i = _i.call(arr); !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"] != null) _i["return"](); } finally { if (_d) throw _e; } } return _arr; }
function _arrayWithHoles(arr) { if (Array.isArray(arr)) return arr; }





var TestShowScreen = function TestShowScreen(props) {
  var _React$useState = react__WEBPACK_IMPORTED_MODULE_0___default().useState(null),
    _React$useState2 = _slicedToArray(_React$useState, 2),
    image = _React$useState2[0],
    setImage = _React$useState2[1];
  var _React$useState3 = react__WEBPACK_IMPORTED_MODULE_0___default().useState(""),
    _React$useState4 = _slicedToArray(_React$useState3, 2),
    code = _React$useState4[0],
    setCode = _React$useState4[1];
  var classes = classnames__WEBPACK_IMPORTED_MODULE_2___default()({
    "test-show-screen": true
  });
  react__WEBPACK_IMPORTED_MODULE_0___default().useEffect(function () {
    console.log("TestShowScreen subscribing to ['update'] events");
    setImage("https://via.placeholder.com/800x600.png?text=No%20image%20received%20from%20exercise");
    var callback = function callback(message) {
      var update = message.data.update;
      if (update.image) {
        var _image = JSON.parse(update.image);
        setImage("data:image/png;base64,".concat(_image.image));
      } else {
        setImage("https://via.placeholder.com/800x600.png?text=No%20image%20received%20from%20exercise");
      }
    };
    RoboticsExerciseComponents.commsManager.subscribe([RoboticsExerciseComponents.commsManager.events.UPDATE], callback);
    return function () {
      console.log("TestShowScreen unsubscribing from ['state-changed'] events");
      RoboticsExerciseComponents.commsManager.unsubscribe([RoboticsExerciseComponents.commsManager.events.UPDATE], callback);
    };
  }, []);
  var changeCode = function changeCode(event) {
    setCode(event.target.value);
  };
  var sendCode = function sendCode(event) {
    RoboticsExerciseComponents.commsManager.send("load", {
      code: code
    }).then(function (message) {
      console.log("code loaded");
    })["catch"](function (response) {
      console.error(response);
    });
  };
  return /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsxs)("div", {
    className: "panel-parent",
    children: [/*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsxs)("div", {
      className: "panel",
      children: [/*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsx)("textarea", {
        value: code,
        onChange: changeCode,
        cols: 80
      }), /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsx)("div", {
        className: classes,
        onClick: sendCode,
        children: "Load code"
      })]
    }), /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsx)("div", {
      className: "panel",
      children: /*#__PURE__*/(0,react_jsx_runtime__WEBPACK_IMPORTED_MODULE_3__.jsx)("img", {
        src: image,
        alt: "Exercise screen",
        className: classes
      })
    })]
  });
};
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (TestShowScreen);

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

/***/ "../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestShowScreen.css":
/*!*****************************************************************************************************************!*\
  !*** ../exercises/static/exercises/follow_line_newmanager/web-template/react-components/css/TestShowScreen.css ***!
  \*****************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

"use strict";
__webpack_require__.r(__webpack_exports__);
// extracted by mini-css-extract-plugin


/***/ })

}]);
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvZXhlcmNpc2VzX3N0YXRpY19leGVyY2lzZXNfZm9sbG93X2xpbmVfbmV3bWFuYWdlcl93ZWItdGVtcGxhdGVfcmVhY3QtY29tcG9uZW50c19UZXN0U2hvd1NjcmVlbl9qcy42MDIyMDI4Ny5qcyIsIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQXNDO0FBQ0o7QUFDRTtBQUFBO0FBQUE7QUFFcEMsSUFBTUcsY0FBYyxHQUFHLFNBQWpCQSxjQUFjLENBQUlDLEtBQUssRUFBSztFQUM5QixzQkFBMEJKLHFEQUFjLENBQUMsSUFBSSxDQUFDO0lBQUE7SUFBdkNNLEtBQUs7SUFBRUMsUUFBUTtFQUN0Qix1QkFBd0JQLHFEQUFjLENBQUMsRUFBRSxDQUFDO0lBQUE7SUFBbkNRLElBQUk7SUFBRUMsT0FBTztFQUVwQixJQUFNQyxPQUFPLEdBQUdSLGlEQUFVLENBQUM7SUFDdkIsa0JBQWtCLEVBQUU7RUFDeEIsQ0FBQyxDQUFDO0VBRUZGLHNEQUFlLENBQUMsWUFBTTtJQUNsQlksT0FBTyxDQUFDQyxHQUFHLENBQUMsaURBQWlELENBQUM7SUFDOUROLFFBQVEsQ0FBQyxzRkFBc0YsQ0FBQztJQUVoRyxJQUFNTyxRQUFRLEdBQUcsU0FBWEEsUUFBUSxDQUFJQyxPQUFPLEVBQUs7TUFDMUIsSUFBTUMsTUFBTSxHQUFHRCxPQUFPLENBQUNFLElBQUksQ0FBQ0QsTUFBTTtNQUNsQyxJQUFJQSxNQUFNLENBQUNWLEtBQUssRUFBRTtRQUNkLElBQU1BLE1BQUssR0FBR1ksSUFBSSxDQUFDQyxLQUFLLENBQUNILE1BQU0sQ0FBQ1YsS0FBSyxDQUFDO1FBQ3RDQyxRQUFRLGlDQUEwQkQsTUFBSyxDQUFDQSxLQUFLLEVBQUc7TUFDcEQsQ0FBQyxNQUFNO1FBQ0hDLFFBQVEsQ0FBQyxzRkFBc0YsQ0FBQztNQUNwRztJQUNKLENBQUM7SUFFRGEsMEJBQTBCLENBQUNDLFlBQVksQ0FBQ0MsU0FBUyxDQUFDLENBQzFDRiwwQkFBMEIsQ0FBQ0MsWUFBWSxDQUFDRSxNQUFNLENBQUNDLE1BQU0sQ0FDeEQsRUFDRFYsUUFBUSxDQUFDO0lBRWIsT0FBTyxZQUFNO01BQ1RGLE9BQU8sQ0FBQ0MsR0FBRyxDQUFDLDREQUE0RCxDQUFDO01BQ3pFTywwQkFBMEIsQ0FBQ0MsWUFBWSxDQUFDSSxXQUFXLENBQUMsQ0FDNUNMLDBCQUEwQixDQUFDQyxZQUFZLENBQUNFLE1BQU0sQ0FBQ0MsTUFBTSxDQUN4RCxFQUNEVixRQUFRLENBQUM7SUFDakIsQ0FBQztFQUNMLENBQUMsRUFBRSxFQUFFLENBQUM7RUFFTixJQUFNWSxVQUFVLEdBQUcsU0FBYkEsVUFBVSxDQUFJQyxLQUFLLEVBQUs7SUFDMUJsQixPQUFPLENBQUNrQixLQUFLLENBQUNDLE1BQU0sQ0FBQ0MsS0FBSyxDQUFDO0VBQy9CLENBQUM7RUFFRCxJQUFNQyxRQUFRLEdBQUcsU0FBWEEsUUFBUSxDQUFJSCxLQUFLLEVBQUs7SUFDeEJQLDBCQUEwQixDQUFDQyxZQUFZLENBQUNVLElBQUksQ0FBQyxNQUFNLEVBQUU7TUFDakR2QixJQUFJLEVBQUVBO0lBQ1YsQ0FBQyxDQUFDLENBQUN3QixJQUFJLENBQUMsVUFBQWpCLE9BQU8sRUFBSTtNQUNmSCxPQUFPLENBQUNDLEdBQUcsQ0FBQyxhQUFhLENBQUM7SUFDOUIsQ0FBQyxDQUFDLFNBQU0sQ0FBQyxVQUFBb0IsUUFBUSxFQUFJO01BQ2pCckIsT0FBTyxDQUFDc0IsS0FBSyxDQUFDRCxRQUFRLENBQUM7SUFDM0IsQ0FBQyxDQUFDO0VBQ04sQ0FBQztFQUVELG9CQUNJO0lBQUssU0FBUyxFQUFFLGNBQWU7SUFBQSx3QkFDM0I7TUFBSyxTQUFTLEVBQUUsT0FBUTtNQUFBLHdCQUNwQjtRQUFVLEtBQUssRUFBRXpCLElBQUs7UUFBQyxRQUFRLEVBQUVrQixVQUFXO1FBQUMsSUFBSSxFQUFFO01BQUcsRUFBRSxlQUN4RDtRQUFLLFNBQVMsRUFBRWhCLE9BQVE7UUFBQyxPQUFPLEVBQUVvQixRQUFTO1FBQUEsVUFBQztNQUFTLEVBQU07SUFBQSxFQUN6RCxlQUNOO01BQUssU0FBUyxFQUFFLE9BQVE7TUFBQSx1QkFDcEI7UUFBSyxHQUFHLEVBQUV4QixLQUFNO1FBQUMsR0FBRyxFQUFFLGlCQUFrQjtRQUFDLFNBQVMsRUFBRUk7TUFBUTtJQUFFLEVBQzVEO0VBQUEsRUFDSjtBQUVkLENBQUM7QUFFRCxpRUFBZVAsY0FBYzs7Ozs7Ozs7OztBQ25FN0I7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQUVBO0FBQ0E7O0FBRUEsZ0JBQWdCO0FBQ2hCOztBQUVBO0FBQ0E7O0FBRUEsa0JBQWtCLHNCQUFzQjtBQUN4QztBQUNBOztBQUVBOztBQUVBO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsS0FBSztBQUNMO0FBQ0E7QUFDQTtBQUNBOztBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQUVBO0FBQ0E7O0FBRUEsS0FBSyxLQUE2QjtBQUNsQztBQUNBO0FBQ0EsR0FBRyxTQUFTLElBQTRFO0FBQ3hGO0FBQ0EsRUFBRSxpQ0FBcUIsRUFBRSxtQ0FBRTtBQUMzQjtBQUNBLEdBQUc7QUFBQSxrR0FBQztBQUNKLEdBQUcsS0FBSyxFQUVOO0FBQ0YsQ0FBQzs7Ozs7Ozs7Ozs7OztBQzNERCIsInNvdXJjZXMiOlsid2VicGFjazovL3JlYWN0X2Zyb250ZW5kLy4uL2V4ZXJjaXNlcy9zdGF0aWMvZXhlcmNpc2VzL2ZvbGxvd19saW5lX25ld21hbmFnZXIvd2ViLXRlbXBsYXRlL3JlYWN0LWNvbXBvbmVudHMvVGVzdFNob3dTY3JlZW4uanMiLCJ3ZWJwYWNrOi8vcmVhY3RfZnJvbnRlbmQvLi9ub2RlX21vZHVsZXMvY2xhc3NuYW1lcy9pbmRleC5qcyIsIndlYnBhY2s6Ly9yZWFjdF9mcm9udGVuZC8uLi9leGVyY2lzZXMvc3RhdGljL2V4ZXJjaXNlcy9mb2xsb3dfbGluZV9uZXdtYW5hZ2VyL3dlYi10ZW1wbGF0ZS9yZWFjdC1jb21wb25lbnRzL2Nzcy9UZXN0U2hvd1NjcmVlbi5jc3M/MGM4OSJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgUmVhY3QsIHtGcmFnbWVudH0gZnJvbSBcInJlYWN0XCI7XG5pbXBvcnQgJy4vY3NzL1Rlc3RTaG93U2NyZWVuLmNzcyc7XG5pbXBvcnQgY2xhc3NOYW1lcyBmcm9tIFwiY2xhc3NuYW1lc1wiO1xuXG5jb25zdCBUZXN0U2hvd1NjcmVlbiA9IChwcm9wcykgPT4ge1xuICAgIGNvbnN0IFtpbWFnZSwgc2V0SW1hZ2VdID0gUmVhY3QudXNlU3RhdGUobnVsbCk7XG4gICAgY29uc3QgW2NvZGUsIHNldENvZGVdID0gUmVhY3QudXNlU3RhdGUoXCJcIik7XG5cbiAgICBjb25zdCBjbGFzc2VzID0gY2xhc3NOYW1lcyh7XG4gICAgICAgIFwidGVzdC1zaG93LXNjcmVlblwiOiB0cnVlLFxuICAgIH0pO1xuXG4gICAgUmVhY3QudXNlRWZmZWN0KCgpID0+IHtcbiAgICAgICAgY29uc29sZS5sb2coXCJUZXN0U2hvd1NjcmVlbiBzdWJzY3JpYmluZyB0byBbJ3VwZGF0ZSddIGV2ZW50c1wiKTtcbiAgICAgICAgc2V0SW1hZ2UoXCJodHRwczovL3ZpYS5wbGFjZWhvbGRlci5jb20vODAweDYwMC5wbmc/dGV4dD1ObyUyMGltYWdlJTIwcmVjZWl2ZWQlMjBmcm9tJTIwZXhlcmNpc2VcIik7XG5cbiAgICAgICAgY29uc3QgY2FsbGJhY2sgPSAobWVzc2FnZSkgPT4ge1xuICAgICAgICAgICAgY29uc3QgdXBkYXRlID0gbWVzc2FnZS5kYXRhLnVwZGF0ZTtcbiAgICAgICAgICAgIGlmICh1cGRhdGUuaW1hZ2UpIHtcbiAgICAgICAgICAgICAgICBjb25zdCBpbWFnZSA9IEpTT04ucGFyc2UodXBkYXRlLmltYWdlKTtcbiAgICAgICAgICAgICAgICBzZXRJbWFnZShgZGF0YTppbWFnZS9wbmc7YmFzZTY0LCR7aW1hZ2UuaW1hZ2V9YCk7XG4gICAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgICAgIHNldEltYWdlKFwiaHR0cHM6Ly92aWEucGxhY2Vob2xkZXIuY29tLzgwMHg2MDAucG5nP3RleHQ9Tm8lMjBpbWFnZSUyMHJlY2VpdmVkJTIwZnJvbSUyMGV4ZXJjaXNlXCIpO1xuICAgICAgICAgICAgfVxuICAgICAgICB9O1xuXG4gICAgICAgIFJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzLmNvbW1zTWFuYWdlci5zdWJzY3JpYmUoW1xuICAgICAgICAgICAgICAgIFJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzLmNvbW1zTWFuYWdlci5ldmVudHMuVVBEQVRFXG4gICAgICAgICAgICBdLFxuICAgICAgICAgICAgY2FsbGJhY2spO1xuXG4gICAgICAgIHJldHVybiAoKSA9PiB7XG4gICAgICAgICAgICBjb25zb2xlLmxvZyhcIlRlc3RTaG93U2NyZWVuIHVuc3Vic2NyaWJpbmcgZnJvbSBbJ3N0YXRlLWNoYW5nZWQnXSBldmVudHNcIik7XG4gICAgICAgICAgICBSb2JvdGljc0V4ZXJjaXNlQ29tcG9uZW50cy5jb21tc01hbmFnZXIudW5zdWJzY3JpYmUoW1xuICAgICAgICAgICAgICAgICAgICBSb2JvdGljc0V4ZXJjaXNlQ29tcG9uZW50cy5jb21tc01hbmFnZXIuZXZlbnRzLlVQREFURVxuICAgICAgICAgICAgICAgIF0sXG4gICAgICAgICAgICAgICAgY2FsbGJhY2spO1xuICAgICAgICB9XG4gICAgfSwgW10pO1xuXG4gICAgY29uc3QgY2hhbmdlQ29kZSA9IChldmVudCkgPT4ge1xuICAgICAgICBzZXRDb2RlKGV2ZW50LnRhcmdldC52YWx1ZSk7XG4gICAgfTtcblxuICAgIGNvbnN0IHNlbmRDb2RlID0gKGV2ZW50KSA9PiB7XG4gICAgICAgIFJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzLmNvbW1zTWFuYWdlci5zZW5kKFwibG9hZFwiLCB7XG4gICAgICAgICAgICBjb2RlOiBjb2RlXG4gICAgICAgIH0pLnRoZW4obWVzc2FnZSA9PiB7XG4gICAgICAgICAgICBjb25zb2xlLmxvZyhcImNvZGUgbG9hZGVkXCIpO1xuICAgICAgICB9KS5jYXRjaChyZXNwb25zZSA9PiB7XG4gICAgICAgICAgICBjb25zb2xlLmVycm9yKHJlc3BvbnNlKTtcbiAgICAgICAgfSlcbiAgICB9O1xuXG4gICAgcmV0dXJuIChcbiAgICAgICAgPGRpdiBjbGFzc05hbWU9e1wicGFuZWwtcGFyZW50XCJ9PlxuICAgICAgICAgICAgPGRpdiBjbGFzc05hbWU9e1wicGFuZWxcIn0+XG4gICAgICAgICAgICAgICAgPHRleHRhcmVhIHZhbHVlPXtjb2RlfSBvbkNoYW5nZT17Y2hhbmdlQ29kZX0gY29scz17ODB9Lz5cbiAgICAgICAgICAgICAgICA8ZGl2IGNsYXNzTmFtZT17Y2xhc3Nlc30gb25DbGljaz17c2VuZENvZGV9PkxvYWQgY29kZTwvZGl2PlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzTmFtZT17XCJwYW5lbFwifT5cbiAgICAgICAgICAgICAgICA8aW1nIHNyYz17aW1hZ2V9IGFsdD17XCJFeGVyY2lzZSBzY3JlZW5cIn0gY2xhc3NOYW1lPXtjbGFzc2VzfS8+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG4gICAgKTtcbn07XG5cbmV4cG9ydCBkZWZhdWx0IFRlc3RTaG93U2NyZWVuOyIsIi8qIVxuXHRDb3B5cmlnaHQgKGMpIDIwMTggSmVkIFdhdHNvbi5cblx0TGljZW5zZWQgdW5kZXIgdGhlIE1JVCBMaWNlbnNlIChNSVQpLCBzZWVcblx0aHR0cDovL2plZHdhdHNvbi5naXRodWIuaW8vY2xhc3NuYW1lc1xuKi9cbi8qIGdsb2JhbCBkZWZpbmUgKi9cblxuKGZ1bmN0aW9uICgpIHtcblx0J3VzZSBzdHJpY3QnO1xuXG5cdHZhciBoYXNPd24gPSB7fS5oYXNPd25Qcm9wZXJ0eTtcblx0dmFyIG5hdGl2ZUNvZGVTdHJpbmcgPSAnW25hdGl2ZSBjb2RlXSc7XG5cblx0ZnVuY3Rpb24gY2xhc3NOYW1lcygpIHtcblx0XHR2YXIgY2xhc3NlcyA9IFtdO1xuXG5cdFx0Zm9yICh2YXIgaSA9IDA7IGkgPCBhcmd1bWVudHMubGVuZ3RoOyBpKyspIHtcblx0XHRcdHZhciBhcmcgPSBhcmd1bWVudHNbaV07XG5cdFx0XHRpZiAoIWFyZykgY29udGludWU7XG5cblx0XHRcdHZhciBhcmdUeXBlID0gdHlwZW9mIGFyZztcblxuXHRcdFx0aWYgKGFyZ1R5cGUgPT09ICdzdHJpbmcnIHx8IGFyZ1R5cGUgPT09ICdudW1iZXInKSB7XG5cdFx0XHRcdGNsYXNzZXMucHVzaChhcmcpO1xuXHRcdFx0fSBlbHNlIGlmIChBcnJheS5pc0FycmF5KGFyZykpIHtcblx0XHRcdFx0aWYgKGFyZy5sZW5ndGgpIHtcblx0XHRcdFx0XHR2YXIgaW5uZXIgPSBjbGFzc05hbWVzLmFwcGx5KG51bGwsIGFyZyk7XG5cdFx0XHRcdFx0aWYgKGlubmVyKSB7XG5cdFx0XHRcdFx0XHRjbGFzc2VzLnB1c2goaW5uZXIpO1xuXHRcdFx0XHRcdH1cblx0XHRcdFx0fVxuXHRcdFx0fSBlbHNlIGlmIChhcmdUeXBlID09PSAnb2JqZWN0Jykge1xuXHRcdFx0XHRpZiAoYXJnLnRvU3RyaW5nICE9PSBPYmplY3QucHJvdG90eXBlLnRvU3RyaW5nICYmICFhcmcudG9TdHJpbmcudG9TdHJpbmcoKS5pbmNsdWRlcygnW25hdGl2ZSBjb2RlXScpKSB7XG5cdFx0XHRcdFx0Y2xhc3Nlcy5wdXNoKGFyZy50b1N0cmluZygpKTtcblx0XHRcdFx0XHRjb250aW51ZTtcblx0XHRcdFx0fVxuXG5cdFx0XHRcdGZvciAodmFyIGtleSBpbiBhcmcpIHtcblx0XHRcdFx0XHRpZiAoaGFzT3duLmNhbGwoYXJnLCBrZXkpICYmIGFyZ1trZXldKSB7XG5cdFx0XHRcdFx0XHRjbGFzc2VzLnB1c2goa2V5KTtcblx0XHRcdFx0XHR9XG5cdFx0XHRcdH1cblx0XHRcdH1cblx0XHR9XG5cblx0XHRyZXR1cm4gY2xhc3Nlcy5qb2luKCcgJyk7XG5cdH1cblxuXHRpZiAodHlwZW9mIG1vZHVsZSAhPT0gJ3VuZGVmaW5lZCcgJiYgbW9kdWxlLmV4cG9ydHMpIHtcblx0XHRjbGFzc05hbWVzLmRlZmF1bHQgPSBjbGFzc05hbWVzO1xuXHRcdG1vZHVsZS5leHBvcnRzID0gY2xhc3NOYW1lcztcblx0fSBlbHNlIGlmICh0eXBlb2YgZGVmaW5lID09PSAnZnVuY3Rpb24nICYmIHR5cGVvZiBkZWZpbmUuYW1kID09PSAnb2JqZWN0JyAmJiBkZWZpbmUuYW1kKSB7XG5cdFx0Ly8gcmVnaXN0ZXIgYXMgJ2NsYXNzbmFtZXMnLCBjb25zaXN0ZW50IHdpdGggbnBtIHBhY2thZ2UgbmFtZVxuXHRcdGRlZmluZSgnY2xhc3NuYW1lcycsIFtdLCBmdW5jdGlvbiAoKSB7XG5cdFx0XHRyZXR1cm4gY2xhc3NOYW1lcztcblx0XHR9KTtcblx0fSBlbHNlIHtcblx0XHR3aW5kb3cuY2xhc3NOYW1lcyA9IGNsYXNzTmFtZXM7XG5cdH1cbn0oKSk7XG4iLCIvLyBleHRyYWN0ZWQgYnkgbWluaS1jc3MtZXh0cmFjdC1wbHVnaW5cbmV4cG9ydCB7fTsiXSwibmFtZXMiOlsiUmVhY3QiLCJGcmFnbWVudCIsImNsYXNzTmFtZXMiLCJUZXN0U2hvd1NjcmVlbiIsInByb3BzIiwidXNlU3RhdGUiLCJpbWFnZSIsInNldEltYWdlIiwiY29kZSIsInNldENvZGUiLCJjbGFzc2VzIiwidXNlRWZmZWN0IiwiY29uc29sZSIsImxvZyIsImNhbGxiYWNrIiwibWVzc2FnZSIsInVwZGF0ZSIsImRhdGEiLCJKU09OIiwicGFyc2UiLCJSb2JvdGljc0V4ZXJjaXNlQ29tcG9uZW50cyIsImNvbW1zTWFuYWdlciIsInN1YnNjcmliZSIsImV2ZW50cyIsIlVQREFURSIsInVuc3Vic2NyaWJlIiwiY2hhbmdlQ29kZSIsImV2ZW50IiwidGFyZ2V0IiwidmFsdWUiLCJzZW5kQ29kZSIsInNlbmQiLCJ0aGVuIiwicmVzcG9uc2UiLCJlcnJvciJdLCJzb3VyY2VSb290IjoiIn0=