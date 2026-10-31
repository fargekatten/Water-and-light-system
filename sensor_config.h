#pragma once
// EXAMPLES ONLY: measure your sensor in dry soil and wet/drained soil first.
const int SOIL_DRY_RAW = 800;
const int SOIL_WET_RAW = 350;
const int SOIL_DRY_PERCENT = 30;
const unsigned long SIMULATION_MS = 5000;
static_assert(SOIL_DRY_RAW != SOIL_WET_RAW, "Soil calibration endpoints must differ");
