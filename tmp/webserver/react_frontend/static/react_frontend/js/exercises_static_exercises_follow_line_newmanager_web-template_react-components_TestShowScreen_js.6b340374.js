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
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvZXhlcmNpc2VzX3N0YXRpY19leGVyY2lzZXNfZm9sbG93X2xpbmVfbmV3bWFuYWdlcl93ZWItdGVtcGxhdGVfcmVhY3QtY29tcG9uZW50c19UZXN0U2hvd1NjcmVlbl9qcy42YjM0MDM3NC5qcyIsIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQXNDO0FBQ0o7QUFDRTtBQUFBO0FBQUE7QUFFcEMsSUFBTUcsY0FBYyxHQUFHLFNBQWpCQSxjQUFjLENBQUlDLEtBQUssRUFBSztFQUM5QixzQkFBMEJKLHFEQUFjLENBQUMsSUFBSSxDQUFDO0lBQUE7SUFBdkNNLEtBQUs7SUFBRUMsUUFBUTtFQUN0Qix1QkFBd0JQLHFEQUFjLENBQUMsRUFBRSxDQUFDO0lBQUE7SUFBbkNRLElBQUk7SUFBRUMsT0FBTztFQUVwQixJQUFNQyxPQUFPLEdBQUdSLGlEQUFVLENBQUM7SUFDdkIsa0JBQWtCLEVBQUU7RUFDeEIsQ0FBQyxDQUFDO0VBRUZGLHNEQUFlLENBQUMsWUFBTTtJQUNsQlksT0FBTyxDQUFDQyxHQUFHLENBQUMsaURBQWlELENBQUM7SUFDOUROLFFBQVEsQ0FBQyxzRkFBc0YsQ0FBQztJQUVoRyxJQUFNTyxRQUFRLEdBQUcsU0FBWEEsUUFBUSxDQUFJQyxPQUFPLEVBQUs7TUFDMUIsSUFBTUMsTUFBTSxHQUFHRCxPQUFPLENBQUNFLElBQUksQ0FBQ0QsTUFBTTtNQUNsQyxJQUFJQSxNQUFNLENBQUNWLEtBQUssRUFBRTtRQUNkLElBQU1BLE1BQUssR0FBR1ksSUFBSSxDQUFDQyxLQUFLLENBQUNILE1BQU0sQ0FBQ1YsS0FBSyxDQUFDO1FBQ3RDQyxRQUFRLGlDQUEwQkQsTUFBSyxDQUFDQSxLQUFLLEVBQUc7TUFDcEQsQ0FBQyxNQUFNO1FBQ0hDLFFBQVEsQ0FBQyxzRkFBc0YsQ0FBQztNQUNwRztJQUNKLENBQUM7SUFFRGEsMEJBQTBCLENBQUNDLFlBQVksQ0FBQ0MsU0FBUyxDQUFDLENBQzFDRiwwQkFBMEIsQ0FBQ0MsWUFBWSxDQUFDRSxNQUFNLENBQUNDLE1BQU0sQ0FDeEQsRUFDRFYsUUFBUSxDQUFDO0lBRWIsT0FBTyxZQUFNO01BQ1RGLE9BQU8sQ0FBQ0MsR0FBRyxDQUFDLDREQUE0RCxDQUFDO01BQ3pFTywwQkFBMEIsQ0FBQ0MsWUFBWSxDQUFDSSxXQUFXLENBQUMsQ0FDNUNMLDBCQUEwQixDQUFDQyxZQUFZLENBQUNFLE1BQU0sQ0FBQ0MsTUFBTSxDQUN4RCxFQUNEVixRQUFRLENBQUM7SUFDakIsQ0FBQztFQUNMLENBQUMsRUFBRSxFQUFFLENBQUM7RUFFTixJQUFNWSxVQUFVLEdBQUcsU0FBYkEsVUFBVSxDQUFJQyxLQUFLLEVBQUs7SUFDMUJsQixPQUFPLENBQUNrQixLQUFLLENBQUNDLE1BQU0sQ0FBQ0MsS0FBSyxDQUFDO0VBQy9CLENBQUM7RUFFRCxJQUFNQyxRQUFRLEdBQUcsU0FBWEEsUUFBUSxDQUFJSCxLQUFLLEVBQUs7SUFDeEJQLDBCQUEwQixDQUFDQyxZQUFZLENBQUNVLElBQUksQ0FBQyxNQUFNLEVBQUU7TUFDakR2QixJQUFJLEVBQUVBO0lBQ1YsQ0FBQyxDQUFDLENBQUN3QixJQUFJLENBQUMsVUFBQWpCLE9BQU8sRUFBSTtNQUNmSCxPQUFPLENBQUNDLEdBQUcsQ0FBQyxhQUFhLENBQUM7SUFDOUIsQ0FBQyxDQUFDLFNBQU0sQ0FBQyxVQUFBb0IsUUFBUSxFQUFJO01BQ2pCckIsT0FBTyxDQUFDc0IsS0FBSyxDQUFDRCxRQUFRLENBQUM7SUFDM0IsQ0FBQyxDQUFDO0VBQ04sQ0FBQztFQUVELG9CQUNJO0lBQUssU0FBUyxFQUFFLGNBQWU7SUFBQSx3QkFDM0I7TUFBSyxTQUFTLEVBQUUsT0FBUTtNQUFBLHdCQUNwQjtRQUFVLEtBQUssRUFBRXpCLElBQUs7UUFBQyxRQUFRLEVBQUVrQixVQUFXO1FBQUMsSUFBSSxFQUFFO01BQUcsRUFBRSxlQUN4RDtRQUFLLFNBQVMsRUFBRWhCLE9BQVE7UUFBQyxPQUFPLEVBQUVvQixRQUFTO1FBQUE7TUFBQSxFQUFnQjtJQUFBLEVBQ3pELGVBQ047TUFBSyxTQUFTLEVBQUUsT0FBUTtNQUFBLHVCQUNwQjtRQUFLLEdBQUcsRUFBRXhCLEtBQU07UUFBQyxHQUFHLEVBQUUsaUJBQWtCO1FBQUMsU0FBUyxFQUFFSTtNQUFRO0lBQUUsRUFDNUQ7RUFBQSxFQUNKO0FBRWQsQ0FBQztBQUVELGlFQUFlUCxjQUFjOzs7Ozs7Ozs7O0FDbkU3QjtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTs7QUFFQSxnQkFBZ0I7QUFDaEI7O0FBRUE7QUFDQTs7QUFFQSxrQkFBa0Isc0JBQXNCO0FBQ3hDO0FBQ0E7O0FBRUE7O0FBRUE7QUFDQTtBQUNBLEtBQUs7QUFDTDtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FBRUE7QUFDQTs7QUFFQSxLQUFLLEtBQTZCO0FBQ2xDO0FBQ0E7QUFDQSxHQUFHLFNBQVMsSUFBNEU7QUFDeEY7QUFDQSxFQUFFLGlDQUFxQixFQUFFLG1DQUFFO0FBQzNCO0FBQ0EsR0FBRztBQUFBLGtHQUFDO0FBQ0osR0FBRyxLQUFLLEVBRU47QUFDRixDQUFDOzs7Ozs7Ozs7Ozs7O0FDM0REIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vcmVhY3RfZnJvbnRlbmQvLi4vZXhlcmNpc2VzL3N0YXRpYy9leGVyY2lzZXMvZm9sbG93X2xpbmVfbmV3bWFuYWdlci93ZWItdGVtcGxhdGUvcmVhY3QtY29tcG9uZW50cy9UZXN0U2hvd1NjcmVlbi5qcyIsIndlYnBhY2s6Ly9yZWFjdF9mcm9udGVuZC8uL25vZGVfbW9kdWxlcy9jbGFzc25hbWVzL2luZGV4LmpzIiwid2VicGFjazovL3JlYWN0X2Zyb250ZW5kLy4uL2V4ZXJjaXNlcy9zdGF0aWMvZXhlcmNpc2VzL2ZvbGxvd19saW5lX25ld21hbmFnZXIvd2ViLXRlbXBsYXRlL3JlYWN0LWNvbXBvbmVudHMvY3NzL1Rlc3RTaG93U2NyZWVuLmNzcz8wYzg5Il0sInNvdXJjZXNDb250ZW50IjpbImltcG9ydCBSZWFjdCwge0ZyYWdtZW50fSBmcm9tIFwicmVhY3RcIjtcbmltcG9ydCAnLi9jc3MvVGVzdFNob3dTY3JlZW4uY3NzJztcbmltcG9ydCBjbGFzc05hbWVzIGZyb20gXCJjbGFzc25hbWVzXCI7XG5cbmNvbnN0IFRlc3RTaG93U2NyZWVuID0gKHByb3BzKSA9PiB7XG4gICAgY29uc3QgW2ltYWdlLCBzZXRJbWFnZV0gPSBSZWFjdC51c2VTdGF0ZShudWxsKTtcbiAgICBjb25zdCBbY29kZSwgc2V0Q29kZV0gPSBSZWFjdC51c2VTdGF0ZShcIlwiKTtcblxuICAgIGNvbnN0IGNsYXNzZXMgPSBjbGFzc05hbWVzKHtcbiAgICAgICAgXCJ0ZXN0LXNob3ctc2NyZWVuXCI6IHRydWUsXG4gICAgfSk7XG5cbiAgICBSZWFjdC51c2VFZmZlY3QoKCkgPT4ge1xuICAgICAgICBjb25zb2xlLmxvZyhcIlRlc3RTaG93U2NyZWVuIHN1YnNjcmliaW5nIHRvIFsndXBkYXRlJ10gZXZlbnRzXCIpO1xuICAgICAgICBzZXRJbWFnZShcImh0dHBzOi8vdmlhLnBsYWNlaG9sZGVyLmNvbS84MDB4NjAwLnBuZz90ZXh0PU5vJTIwaW1hZ2UlMjByZWNlaXZlZCUyMGZyb20lMjBleGVyY2lzZVwiKTtcblxuICAgICAgICBjb25zdCBjYWxsYmFjayA9IChtZXNzYWdlKSA9PiB7XG4gICAgICAgICAgICBjb25zdCB1cGRhdGUgPSBtZXNzYWdlLmRhdGEudXBkYXRlO1xuICAgICAgICAgICAgaWYgKHVwZGF0ZS5pbWFnZSkge1xuICAgICAgICAgICAgICAgIGNvbnN0IGltYWdlID0gSlNPTi5wYXJzZSh1cGRhdGUuaW1hZ2UpO1xuICAgICAgICAgICAgICAgIHNldEltYWdlKGBkYXRhOmltYWdlL3BuZztiYXNlNjQsJHtpbWFnZS5pbWFnZX1gKTtcbiAgICAgICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgICAgICAgc2V0SW1hZ2UoXCJodHRwczovL3ZpYS5wbGFjZWhvbGRlci5jb20vODAweDYwMC5wbmc/dGV4dD1ObyUyMGltYWdlJTIwcmVjZWl2ZWQlMjBmcm9tJTIwZXhlcmNpc2VcIik7XG4gICAgICAgICAgICB9XG4gICAgICAgIH07XG5cbiAgICAgICAgUm9ib3RpY3NFeGVyY2lzZUNvbXBvbmVudHMuY29tbXNNYW5hZ2VyLnN1YnNjcmliZShbXG4gICAgICAgICAgICAgICAgUm9ib3RpY3NFeGVyY2lzZUNvbXBvbmVudHMuY29tbXNNYW5hZ2VyLmV2ZW50cy5VUERBVEVcbiAgICAgICAgICAgIF0sXG4gICAgICAgICAgICBjYWxsYmFjayk7XG5cbiAgICAgICAgcmV0dXJuICgpID0+IHtcbiAgICAgICAgICAgIGNvbnNvbGUubG9nKFwiVGVzdFNob3dTY3JlZW4gdW5zdWJzY3JpYmluZyBmcm9tIFsnc3RhdGUtY2hhbmdlZCddIGV2ZW50c1wiKTtcbiAgICAgICAgICAgIFJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzLmNvbW1zTWFuYWdlci51bnN1YnNjcmliZShbXG4gICAgICAgICAgICAgICAgICAgIFJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzLmNvbW1zTWFuYWdlci5ldmVudHMuVVBEQVRFXG4gICAgICAgICAgICAgICAgXSxcbiAgICAgICAgICAgICAgICBjYWxsYmFjayk7XG4gICAgICAgIH1cbiAgICB9LCBbXSk7XG5cbiAgICBjb25zdCBjaGFuZ2VDb2RlID0gKGV2ZW50KSA9PiB7XG4gICAgICAgIHNldENvZGUoZXZlbnQudGFyZ2V0LnZhbHVlKTtcbiAgICB9O1xuXG4gICAgY29uc3Qgc2VuZENvZGUgPSAoZXZlbnQpID0+IHtcbiAgICAgICAgUm9ib3RpY3NFeGVyY2lzZUNvbXBvbmVudHMuY29tbXNNYW5hZ2VyLnNlbmQoXCJsb2FkXCIsIHtcbiAgICAgICAgICAgIGNvZGU6IGNvZGVcbiAgICAgICAgfSkudGhlbihtZXNzYWdlID0+IHtcbiAgICAgICAgICAgIGNvbnNvbGUubG9nKFwiY29kZSBsb2FkZWRcIik7XG4gICAgICAgIH0pLmNhdGNoKHJlc3BvbnNlID0+IHtcbiAgICAgICAgICAgIGNvbnNvbGUuZXJyb3IocmVzcG9uc2UpO1xuICAgICAgICB9KVxuICAgIH07XG5cbiAgICByZXR1cm4gKFxuICAgICAgICA8ZGl2IGNsYXNzTmFtZT17XCJwYW5lbC1wYXJlbnRcIn0+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzTmFtZT17XCJwYW5lbFwifT5cbiAgICAgICAgICAgICAgICA8dGV4dGFyZWEgdmFsdWU9e2NvZGV9IG9uQ2hhbmdlPXtjaGFuZ2VDb2RlfSBjb2xzPXs4MH0vPlxuICAgICAgICAgICAgICAgIDxkaXYgY2xhc3NOYW1lPXtjbGFzc2VzfSBvbkNsaWNrPXtzZW5kQ29kZX0+TG9hZCBjb2RlPC9kaXY+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICAgIDxkaXYgY2xhc3NOYW1lPXtcInBhbmVsXCJ9PlxuICAgICAgICAgICAgICAgIDxpbWcgc3JjPXtpbWFnZX0gYWx0PXtcIkV4ZXJjaXNlIHNjcmVlblwifSBjbGFzc05hbWU9e2NsYXNzZXN9Lz5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICA8L2Rpdj5cbiAgICApO1xufTtcblxuZXhwb3J0IGRlZmF1bHQgVGVzdFNob3dTY3JlZW47IiwiLyohXG5cdENvcHlyaWdodCAoYykgMjAxOCBKZWQgV2F0c29uLlxuXHRMaWNlbnNlZCB1bmRlciB0aGUgTUlUIExpY2Vuc2UgKE1JVCksIHNlZVxuXHRodHRwOi8vamVkd2F0c29uLmdpdGh1Yi5pby9jbGFzc25hbWVzXG4qL1xuLyogZ2xvYmFsIGRlZmluZSAqL1xuXG4oZnVuY3Rpb24gKCkge1xuXHQndXNlIHN0cmljdCc7XG5cblx0dmFyIGhhc093biA9IHt9Lmhhc093blByb3BlcnR5O1xuXHR2YXIgbmF0aXZlQ29kZVN0cmluZyA9ICdbbmF0aXZlIGNvZGVdJztcblxuXHRmdW5jdGlvbiBjbGFzc05hbWVzKCkge1xuXHRcdHZhciBjbGFzc2VzID0gW107XG5cblx0XHRmb3IgKHZhciBpID0gMDsgaSA8IGFyZ3VtZW50cy5sZW5ndGg7IGkrKykge1xuXHRcdFx0dmFyIGFyZyA9IGFyZ3VtZW50c1tpXTtcblx0XHRcdGlmICghYXJnKSBjb250aW51ZTtcblxuXHRcdFx0dmFyIGFyZ1R5cGUgPSB0eXBlb2YgYXJnO1xuXG5cdFx0XHRpZiAoYXJnVHlwZSA9PT0gJ3N0cmluZycgfHwgYXJnVHlwZSA9PT0gJ251bWJlcicpIHtcblx0XHRcdFx0Y2xhc3Nlcy5wdXNoKGFyZyk7XG5cdFx0XHR9IGVsc2UgaWYgKEFycmF5LmlzQXJyYXkoYXJnKSkge1xuXHRcdFx0XHRpZiAoYXJnLmxlbmd0aCkge1xuXHRcdFx0XHRcdHZhciBpbm5lciA9IGNsYXNzTmFtZXMuYXBwbHkobnVsbCwgYXJnKTtcblx0XHRcdFx0XHRpZiAoaW5uZXIpIHtcblx0XHRcdFx0XHRcdGNsYXNzZXMucHVzaChpbm5lcik7XG5cdFx0XHRcdFx0fVxuXHRcdFx0XHR9XG5cdFx0XHR9IGVsc2UgaWYgKGFyZ1R5cGUgPT09ICdvYmplY3QnKSB7XG5cdFx0XHRcdGlmIChhcmcudG9TdHJpbmcgIT09IE9iamVjdC5wcm90b3R5cGUudG9TdHJpbmcgJiYgIWFyZy50b1N0cmluZy50b1N0cmluZygpLmluY2x1ZGVzKCdbbmF0aXZlIGNvZGVdJykpIHtcblx0XHRcdFx0XHRjbGFzc2VzLnB1c2goYXJnLnRvU3RyaW5nKCkpO1xuXHRcdFx0XHRcdGNvbnRpbnVlO1xuXHRcdFx0XHR9XG5cblx0XHRcdFx0Zm9yICh2YXIga2V5IGluIGFyZykge1xuXHRcdFx0XHRcdGlmIChoYXNPd24uY2FsbChhcmcsIGtleSkgJiYgYXJnW2tleV0pIHtcblx0XHRcdFx0XHRcdGNsYXNzZXMucHVzaChrZXkpO1xuXHRcdFx0XHRcdH1cblx0XHRcdFx0fVxuXHRcdFx0fVxuXHRcdH1cblxuXHRcdHJldHVybiBjbGFzc2VzLmpvaW4oJyAnKTtcblx0fVxuXG5cdGlmICh0eXBlb2YgbW9kdWxlICE9PSAndW5kZWZpbmVkJyAmJiBtb2R1bGUuZXhwb3J0cykge1xuXHRcdGNsYXNzTmFtZXMuZGVmYXVsdCA9IGNsYXNzTmFtZXM7XG5cdFx0bW9kdWxlLmV4cG9ydHMgPSBjbGFzc05hbWVzO1xuXHR9IGVsc2UgaWYgKHR5cGVvZiBkZWZpbmUgPT09ICdmdW5jdGlvbicgJiYgdHlwZW9mIGRlZmluZS5hbWQgPT09ICdvYmplY3QnICYmIGRlZmluZS5hbWQpIHtcblx0XHQvLyByZWdpc3RlciBhcyAnY2xhc3NuYW1lcycsIGNvbnNpc3RlbnQgd2l0aCBucG0gcGFja2FnZSBuYW1lXG5cdFx0ZGVmaW5lKCdjbGFzc25hbWVzJywgW10sIGZ1bmN0aW9uICgpIHtcblx0XHRcdHJldHVybiBjbGFzc05hbWVzO1xuXHRcdH0pO1xuXHR9IGVsc2Uge1xuXHRcdHdpbmRvdy5jbGFzc05hbWVzID0gY2xhc3NOYW1lcztcblx0fVxufSgpKTtcbiIsIi8vIGV4dHJhY3RlZCBieSBtaW5pLWNzcy1leHRyYWN0LXBsdWdpblxuZXhwb3J0IHt9OyJdLCJuYW1lcyI6WyJSZWFjdCIsIkZyYWdtZW50IiwiY2xhc3NOYW1lcyIsIlRlc3RTaG93U2NyZWVuIiwicHJvcHMiLCJ1c2VTdGF0ZSIsImltYWdlIiwic2V0SW1hZ2UiLCJjb2RlIiwic2V0Q29kZSIsImNsYXNzZXMiLCJ1c2VFZmZlY3QiLCJjb25zb2xlIiwibG9nIiwiY2FsbGJhY2siLCJtZXNzYWdlIiwidXBkYXRlIiwiZGF0YSIsIkpTT04iLCJwYXJzZSIsIlJvYm90aWNzRXhlcmNpc2VDb21wb25lbnRzIiwiY29tbXNNYW5hZ2VyIiwic3Vic2NyaWJlIiwiZXZlbnRzIiwiVVBEQVRFIiwidW5zdWJzY3JpYmUiLCJjaGFuZ2VDb2RlIiwiZXZlbnQiLCJ0YXJnZXQiLCJ2YWx1ZSIsInNlbmRDb2RlIiwic2VuZCIsInRoZW4iLCJyZXNwb25zZSIsImVycm9yIl0sInNvdXJjZVJvb3QiOiIifQ==