from pathlib import Path

DEBUG = True


ROOT_DIR = Path.cwd().joinpath("tests", ".agentl") if DEBUG else Path.home().joinpath(".agentl")
