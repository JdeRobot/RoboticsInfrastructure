"use strict";
(self["webpackChunkreact_frontend"] = self["webpackChunkreact_frontend"] || []).push([["src_helpers_3DReconstruction_pose3d_js"],{

/***/ "./src/helpers/3DReconstruction/pose3d.js":
/*!************************************************!*\
  !*** ./src/helpers/3DReconstruction/pose3d.js ***!
  \************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "getPitch": () => (/* binding */ getPitch),
/* harmony export */   "getRoll": () => (/* binding */ getRoll),
/* harmony export */   "getYaw": () => (/* binding */ getYaw)
/* harmony export */ });
function getYaw(qw, qx, qy, qz) {
  var rotateZa0 = 2.0 * (qx * qy + qw * qz);
  var rotateZa1 = qw * qw + qx * qx - qy * qy - qz * qz;
  if (rotateZa0 !== 0.0 && rotateZa1 !== 0.0) {
    return Math.atan2(rotateZa0, rotateZa1);
  }
  return 0.0;
}
function getRoll(qw, qx, qy, qz) {
  var rotateXa0 = 2.0 * (qy * qz + qw * qx);
  var rotateXa1 = qw * qw - qx * qx - qy * qy + qz * qz;
  if (rotateXa0 !== 0.0 && rotateXa1 !== 0.0) {
    return Math.atan2(rotateXa0, rotateXa1);
  }
  return 0.0;
}
function getPitch(qw, qx, qy, qz) {
  var rotateYa0 = -2.0 * (qx * qz - qw * qy);
  if (rotateYa0 >= 1.0) {
    return Math.PI / 2.0;
  } else if (rotateYa0 <= -1.0) {
    return -Math.PI / 2.0;
  } else {
    return Math.asin(rotateYa0);
  }
}

/***/ })

}]);
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvc3JjX2hlbHBlcnNfM0RSZWNvbnN0cnVjdGlvbl9wb3NlM2RfanMuYmI2YTNiYzguanMiLCJtYXBwaW5ncyI6Ijs7Ozs7Ozs7Ozs7Ozs7O0FBQU8sU0FBU0EsTUFBTSxDQUFDQyxFQUFFLEVBQUVDLEVBQUUsRUFBRUMsRUFBRSxFQUFFQyxFQUFFLEVBQUU7RUFDckMsSUFBTUMsU0FBUyxHQUFHLEdBQUcsSUFBSUgsRUFBRSxHQUFHQyxFQUFFLEdBQUdGLEVBQUUsR0FBR0csRUFBRSxDQUFDO0VBQzNDLElBQU1FLFNBQVMsR0FBR0wsRUFBRSxHQUFHQSxFQUFFLEdBQUdDLEVBQUUsR0FBR0EsRUFBRSxHQUFHQyxFQUFFLEdBQUdBLEVBQUUsR0FBR0MsRUFBRSxHQUFHQSxFQUFFO0VBQ3ZELElBQUlDLFNBQVMsS0FBSyxHQUFHLElBQUlDLFNBQVMsS0FBSyxHQUFHLEVBQUU7SUFDMUMsT0FBT0MsSUFBSSxDQUFDQyxLQUFLLENBQUNILFNBQVMsRUFBRUMsU0FBUyxDQUFDO0VBQ3pDO0VBQ0EsT0FBTyxHQUFHO0FBQ1o7QUFFTyxTQUFTRyxPQUFPLENBQUNSLEVBQUUsRUFBRUMsRUFBRSxFQUFFQyxFQUFFLEVBQUVDLEVBQUUsRUFBRTtFQUN0QyxJQUFNTSxTQUFTLEdBQUcsR0FBRyxJQUFJUCxFQUFFLEdBQUdDLEVBQUUsR0FBR0gsRUFBRSxHQUFHQyxFQUFFLENBQUM7RUFDM0MsSUFBTVMsU0FBUyxHQUFHVixFQUFFLEdBQUdBLEVBQUUsR0FBR0MsRUFBRSxHQUFHQSxFQUFFLEdBQUdDLEVBQUUsR0FBR0EsRUFBRSxHQUFHQyxFQUFFLEdBQUdBLEVBQUU7RUFFdkQsSUFBSU0sU0FBUyxLQUFLLEdBQUcsSUFBSUMsU0FBUyxLQUFLLEdBQUcsRUFBRTtJQUMxQyxPQUFPSixJQUFJLENBQUNDLEtBQUssQ0FBQ0UsU0FBUyxFQUFFQyxTQUFTLENBQUM7RUFDekM7RUFDQSxPQUFPLEdBQUc7QUFDWjtBQUNPLFNBQVNDLFFBQVEsQ0FBQ1gsRUFBRSxFQUFFQyxFQUFFLEVBQUVDLEVBQUUsRUFBRUMsRUFBRSxFQUFFO0VBQ3ZDLElBQU1TLFNBQVMsR0FBRyxDQUFDLEdBQUcsSUFBSVgsRUFBRSxHQUFHRSxFQUFFLEdBQUdILEVBQUUsR0FBR0UsRUFBRSxDQUFDO0VBQzVDLElBQUlVLFNBQVMsSUFBSSxHQUFHLEVBQUU7SUFDcEIsT0FBT04sSUFBSSxDQUFDTyxFQUFFLEdBQUcsR0FBRztFQUN0QixDQUFDLE1BQU0sSUFBSUQsU0FBUyxJQUFJLENBQUMsR0FBRyxFQUFFO0lBQzVCLE9BQU8sQ0FBQ04sSUFBSSxDQUFDTyxFQUFFLEdBQUcsR0FBRztFQUN2QixDQUFDLE1BQU07SUFDTCxPQUFPUCxJQUFJLENBQUNRLElBQUksQ0FBQ0YsU0FBUyxDQUFDO0VBQzdCO0FBQ0YiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly9yZWFjdF9mcm9udGVuZC8uL3NyYy9oZWxwZXJzLzNEUmVjb25zdHJ1Y3Rpb24vcG9zZTNkLmpzIl0sInNvdXJjZXNDb250ZW50IjpbImV4cG9ydCBmdW5jdGlvbiBnZXRZYXcocXcsIHF4LCBxeSwgcXopIHtcbiAgY29uc3Qgcm90YXRlWmEwID0gMi4wICogKHF4ICogcXkgKyBxdyAqIHF6KTtcbiAgY29uc3Qgcm90YXRlWmExID0gcXcgKiBxdyArIHF4ICogcXggLSBxeSAqIHF5IC0gcXogKiBxejtcbiAgaWYgKHJvdGF0ZVphMCAhPT0gMC4wICYmIHJvdGF0ZVphMSAhPT0gMC4wKSB7XG4gICAgcmV0dXJuIE1hdGguYXRhbjIocm90YXRlWmEwLCByb3RhdGVaYTEpO1xuICB9XG4gIHJldHVybiAwLjA7XG59XG5cbmV4cG9ydCBmdW5jdGlvbiBnZXRSb2xsKHF3LCBxeCwgcXksIHF6KSB7XG4gIGNvbnN0IHJvdGF0ZVhhMCA9IDIuMCAqIChxeSAqIHF6ICsgcXcgKiBxeCk7XG4gIGNvbnN0IHJvdGF0ZVhhMSA9IHF3ICogcXcgLSBxeCAqIHF4IC0gcXkgKiBxeSArIHF6ICogcXo7XG5cbiAgaWYgKHJvdGF0ZVhhMCAhPT0gMC4wICYmIHJvdGF0ZVhhMSAhPT0gMC4wKSB7XG4gICAgcmV0dXJuIE1hdGguYXRhbjIocm90YXRlWGEwLCByb3RhdGVYYTEpO1xuICB9XG4gIHJldHVybiAwLjA7XG59XG5leHBvcnQgZnVuY3Rpb24gZ2V0UGl0Y2gocXcsIHF4LCBxeSwgcXopIHtcbiAgY29uc3Qgcm90YXRlWWEwID0gLTIuMCAqIChxeCAqIHF6IC0gcXcgKiBxeSk7XG4gIGlmIChyb3RhdGVZYTAgPj0gMS4wKSB7XG4gICAgcmV0dXJuIE1hdGguUEkgLyAyLjA7XG4gIH0gZWxzZSBpZiAocm90YXRlWWEwIDw9IC0xLjApIHtcbiAgICByZXR1cm4gLU1hdGguUEkgLyAyLjA7XG4gIH0gZWxzZSB7XG4gICAgcmV0dXJuIE1hdGguYXNpbihyb3RhdGVZYTApO1xuICB9XG59XG4iXSwibmFtZXMiOlsiZ2V0WWF3IiwicXciLCJxeCIsInF5IiwicXoiLCJyb3RhdGVaYTAiLCJyb3RhdGVaYTEiLCJNYXRoIiwiYXRhbjIiLCJnZXRSb2xsIiwicm90YXRlWGEwIiwicm90YXRlWGExIiwiZ2V0UGl0Y2giLCJyb3RhdGVZYTAiLCJQSSIsImFzaW4iXSwic291cmNlUm9vdCI6IiJ9