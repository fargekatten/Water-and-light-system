#pragma once
// Measure both endpoints in your own pot before trusting the percentage.
const int SOIL_DRY_RAW = 800;
const int SOIL_WET_RAW = 350;
const int SOIL_DRY_PERCENT = 30;
// Grove light sensor raw >= this value means bright; adjust at the window.
const int LIGHT_BRIGHT_THRESHOLD = 500;
const unsigned long SIMULATION_MS = 5000;
static_assert(SOIL_DRY_RAW != SOIL_WET_RAW, "Soil calibration endpoints must differ");
