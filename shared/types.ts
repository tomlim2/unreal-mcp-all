/**
 * TypeScript interfaces for MegaMelange Unreal MCP Communication
 * Based on cross-checked C++ implementations in UnrealMCPActorCommands.cpp
 */

// ============================
// ULTRA DYNAMIC SKY TYPES
// ============================

export interface UltraDynamicSkyRequest {
  /** Name of the Ultra Dynamic Sky actor (default: "Ultra_Dynamic_Sky_C_0") */
  sky_name?: string;
  
  /** Time in HHMM format (1430 = 2:30 PM) or decimal hours (0-24), range: 0-2400 */
  time_of_day?: number;
  
  /** Color temperature in Kelvin, range: 1500-15000 */
  color_temperature?: number;
}

export interface UltraDynamicSkyResponse {
  /** Name of the sky actor */
  sky_name?: string;
  
  /** Current time of day value */
  time_of_day?: number;
  
  /** Current color temperature in Kelvin */
  color_temperature?: number;
  
  /** Whether the operation succeeded */
  success: boolean;
  
  /** Status message */
  message?: string;
  
  /** Property name that was modified (for set operations) */
  property_name?: string;
  
  /** Property type (e.g., "float") */
  property_type?: string;
  
  /** Value that was set (for set operations) */
  value?: number;
}

// ============================
// MM CONTROL LIGHT TYPES
// ============================

export interface Vector3 {
  /** X coordinate (forward in Unreal coordinate system) */
  x: number;
  
  /** Y coordinate (right in Unreal coordinate system) */
  y: number;
  
  /** Z coordinate (up in Unreal coordinate system) */
  z: number;
}

export interface RGBColor {
  /** Red component (0-255, converted to 0-1 internally by Unreal) */
  r: number;
  
  /** Green component (0-255, converted to 0-1 internally by Unreal) */
  g: number;
  
  /** Blue component (0-255, converted to 0-1 internally by Unreal) */
  b: number;
}

export interface MMControlLightRequest {
  /** Unique name for the light (required for create/update/delete) */
  light_name?: string;
  
  /** Light position in Unreal coordinates (default: {x: 0, y: 0, z: 100}) */
  location?: Vector3;
  
  /** Light intensity value (default: 1000.0) */
  intensity?: number;
  
  /** Light color in RGB 0-255 range (default: {r: 255, g: 255, b: 255}) */
  color?: RGBColor;
}

export interface MMControlLightInfo {
  /** Name of the light */
  light_name: string;
  
  /** Light position */
  location: Vector3;
  
  /** Light intensity */
  intensity: number;
  
  /** Light color in RGB 0-255 range */
  color: RGBColor;
}

export interface MMControlLightResponse {
  /** Name of the light */
  light_name?: string;
  
  /** Light position */
  location?: Vector3;
  
  /** Light intensity */
  intensity?: number;
  
  /** Light color in RGB 0-255 range */
  color?: RGBColor;
  
  /** Whether the operation succeeded */
  success: boolean;
  
  /** Status message */
  message?: string;
  
  /** Full actor name in Unreal Engine */
  actor_name?: string;
  
  /** Array of lights (for get_mm_control_lights command) */
  lights?: MMControlLightInfo[];
}

// ============================
// COMMAND WRAPPERS
// ============================

export type SkyCommand = 
  | 'get_ultra_dynamic_sky'
  | 'set_time_of_day'
  | 'set_color_temperature';

export type LightCommand = 
  | 'create_mm_control_light'
  | 'get_mm_control_lights'
  | 'update_mm_control_light'
  | 'delete_mm_control_light';

export type UnrealCommand = SkyCommand | LightCommand;

export interface UnrealCommandRequest {
  /** Command type */
  command: UnrealCommand;
  
  /** Command parameters */
  parameters: UltraDynamicSkyRequest | MMControlLightRequest;
}

export interface UnrealCommandResponse {
  /** Command result */
  result?: UltraDynamicSkyResponse | MMControlLightResponse;
  
  /** Response status */
  status?: 'success' | 'error';
  
  /** Error message if status is error */
  error?: string;
}

// ============================
// VALIDATION CONSTANTS
// ============================

export const SKY_CONSTRAINTS = {
  /** Valid time range in HHMM format */
  TIME_RANGE: { min: 0, max: 2400 },
  
  /** Valid color temperature range in Kelvin */
  COLOR_TEMP_RANGE: { min: 1500, max: 15000 },
  
  /** Default sky actor name from C++ implementation */
  DEFAULT_SKY_NAME: 'Ultra_Dynamic_Sky_C_0',
  
  /** Default sky class name from C++ */
  SKY_CLASS_NAME: 'Ultra_Dynamic_Sky_C',
} as const;

export const LIGHT_CONSTRAINTS = {
  /** Default light intensity from C++ implementation */
  DEFAULT_INTENSITY: 1000.0,
  
  /** Default light position from C++ implementation */
  DEFAULT_LOCATION: { x: 0.0, y: 0.0, z: 100.0 },
  
  /** Default light color from C++ implementation */
  DEFAULT_COLOR: { r: 255, g: 255, b: 255 },
  
  /** Valid RGB color component range */
  COLOR_RANGE: { min: 0, max: 255 },
} as const;

// ============================
// TYPE GUARDS
// ============================

export function isSkyCommand(command: string): command is SkyCommand {
  return ['get_ultra_dynamic_sky', 'set_time_of_day', 'set_color_temperature'].includes(command);
}

export function isLightCommand(command: string): command is LightCommand {
  return ['create_mm_control_light', 'get_mm_control_lights', 'update_mm_control_light', 'delete_mm_control_light'].includes(command);
}

export function isValidTimeOfDay(time: number): boolean {
  return time >= SKY_CONSTRAINTS.TIME_RANGE.min && time <= SKY_CONSTRAINTS.TIME_RANGE.max;
}

export function isValidColorTemperature(temp: number): boolean {
  return temp >= SKY_CONSTRAINTS.COLOR_TEMP_RANGE.min && temp <= SKY_CONSTRAINTS.COLOR_TEMP_RANGE.max;
}

export function isValidRGBComponent(value: number): boolean {
  return Number.isInteger(value) && value >= LIGHT_CONSTRAINTS.COLOR_RANGE.min && value <= LIGHT_CONSTRAINTS.COLOR_RANGE.max;
}

export function isValidVector3(vec: any): vec is Vector3 {
  return typeof vec === 'object' && 
         vec !== null &&
         typeof vec.x === 'number' && 
         typeof vec.y === 'number' && 
         typeof vec.z === 'number';
}

export function isValidRGBColor(color: any): color is RGBColor {
  return typeof color === 'object' && 
         color !== null &&
         isValidRGBComponent(color.r) &&
         isValidRGBComponent(color.g) &&
         isValidRGBComponent(color.b);
}

// ============================
// UTILITY FUNCTIONS
// ============================

/** Convert RGB 0-255 to Linear 0-1 (matches Unreal's internal conversion) */
export function rgbToLinear(color: RGBColor): { r: number; g: number; b: number } {
  return {
    r: color.r / 255.0,
    g: color.g / 255.0,
    b: color.b / 255.0
  };
}

/** Convert Linear 0-1 to RGB 0-255 */
export function linearToRgb(color: { r: number; g: number; b: number }): RGBColor {
  return {
    r: Math.round(color.r * 255),
    g: Math.round(color.g * 255),
    b: Math.round(color.b * 255)
  };
}

/** Convert HHMM format to decimal hours */
export function hhmmToDecimal(hhmm: number): number {
  const hours = Math.floor(hhmm / 100);
  const minutes = hhmm % 100;
  return hours + (minutes / 60);
}

/** Convert decimal hours to HHMM format */
export function decimalToHhmm(decimal: number): number {
  const hours = Math.floor(decimal);
  const minutes = Math.round((decimal - hours) * 60);
  return (hours * 100) + minutes;
}