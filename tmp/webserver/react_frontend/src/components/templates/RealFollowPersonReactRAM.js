import * as React from "react";
import { Box } from "@mui/material";
import { ViewProvider } from "../../contexts/ViewContext";
import { ExerciseProvider } from "../../contexts/NewManagerExerciseContext";
import NewManagerExerciseContext from "../../contexts/NewManagerExerciseContext";
import MainAppBar from "../common/MainAppBar";
import View from "../common/View";
import { THEORY_URL } from "../../helpers/TheoryUrlGetter";
import RAMRealFollowPersonExerciseView from "../views/RAM/RAMRealFollowPersonExerciseView";

function RealFollowPersonReactRAM() {
  return (
    <Box>
      <ViewProvider>
        <ExerciseProvider>
          <MainAppBar
            exerciseName={" Real Follow Person RR"}
          />
          <View
            url={THEORY_URL.FollowPerson}
            exerciseId={
              <RAMRealFollowPersonExerciseView context={NewManagerExerciseContext} />
            }
          />
        </ExerciseProvider>
      </ViewProvider>
    </Box>
  );
}

export default RealFollowPersonReactRAM;
