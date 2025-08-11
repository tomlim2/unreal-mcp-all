import unreal

def get_time_of_day(actor: unreal.Actor):
    return actor.get_editor_property("Time of Day")

def set_time_of_day(actor: unreal.Actor, time_of_day: float):
    actor.set_editor_property("Time of Day", time_of_day)

level_editor_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

actors = unreal.EditorLevelLibrary.get_all_level_actors()

for actor in actors:
    if actor.get_name() == "Ultra_Dynamic_Sky_C_0":
        tod = actor.get_editor_property("Time of Day")
        print(tod)
        break

if actor.get_name() == "Ultra_Dynamic_Sky_C_0":
    set_time_of_day(actor, 1000)
    print(get_time_of_day(actor))