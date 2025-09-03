import unreal

def get_current_weather(actor: unreal.Actor):
    return actor.get_editor_property("Time of Day")

def set_current_weather_to_rain(actor: unreal.Actor, weather: unreal.DataAsset):
    actor.set_editor_property("Time of Day", weather)

level_editor_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

actors = unreal.EditorLevelLibrary.get_all_level_actors()

rain: unreal.DataAsset = unreal.load_asset("/Game/UltraDynamicSky/Blueprints/Weather_Effects/Weather_Presets/Rain.Rain")

for actor in actors:
    if actor.get_name() == "Ultra_Dynamic_Weather_C_0":
        weather = actor.get_editor_property("weather")
        print(weather)
        break

if actor.get_name() == "Ultra_Dynamic_Weather_C_0":
    set_current_weather_to_rain(actor, rain)
    print(get_current_weather(actor))