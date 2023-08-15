from chaos_nightmare.config import config

HELP_TEXT = f"""
This is an experiment in crowd-sourced image generation: Images are generated based on current prompts at a set cadence (currently {config.image_gen_rate_seconds} seconds). Once an image has been created, that image will be used for successive generations for {config.iteration_thresh} iterations. Everything will be reset afterwards. List all current commands with !list_commands. Used the !explain command to get an explanation about a specific command. Ex !explain list_commands
"""
