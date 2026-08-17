#ifndef SF_DWA_LOCAL_PLANNER_LATERAL_VELOCITY_COST_FUNCTION_H_
#define SF_DWA_LOCAL_PLANNER_LATERAL_VELOCITY_COST_FUNCTION_H_

#include <cmath>
#include <base_local_planner/trajectory_cost_function.h>

namespace sf_dwa_local_planner {

class LateralVelocityCostFunction
    : public base_local_planner::TrajectoryCostFunction {
public:
  LateralVelocityCostFunction()
      : base_local_planner::TrajectoryCostFunction(0.0) {
  }

  bool prepare() {
    return true;
  }

  double scoreTrajectory(base_local_planner::Trajectory &traj) {
    return std::fabs(traj.yv_);
  }
};

}  // namespace sf_dwa_local_planner

#endif
