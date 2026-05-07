from agent_builder.core.memory import SharedMemory


def test_memory_save_and_load(tmp_path):
    mem = SharedMemory(data_dir=str(tmp_path))
    mem.save("x", {"y": 1})
    assert mem.load("x") == {"y": 1}
