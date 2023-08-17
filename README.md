

# Chaos Nightmare ![ChatGPT](https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white) ![Twitch](https://img.shields.io/badge/Twitch-9347FF?style=for-the-badge&logo=twitch&logoColor=white)


[![AUP](https://img.shields.io/badge/Acceptable%20Use%20Policy-Read%20Now-blue)](./ACCEPTABLE_USE_POLICY.md)

This is a prototype for a crowd-sourced generative ai chatbot. Essentially, the objective was to take all chat within a twitch channel and use that as prompts for stable diffusion. Prompts then drive a virtual webcam to provide back to twitch 


## Setup/Requirements

- As of writing, the virtualcamera library is hardcoded to used the Open Broadcaster Software (OBS) backend [here](https://obsproject.com/)
- For simplicity, image generation is done through automatic1111's webui that can be exposed locally. [here] https://github.com/AUTOMATIC1111/stable-diffusion-webui
    - make sure that commandline arguments include `--api` for startup
    - you own setup may vary depending on use case, but it is heavily encouraged that you include a script similar to [this](https://github.com/AUTOMATIC1111/stable-diffusion-webui-nsfw-censor)
- Module is managed by [poetry](https://python-poetry.org/docs/)
- Optional, including a chatgpt token in your environment (see environment variables below) will cause the chatbot to ask chatgpt for prompts when chat has be silent during prompt collection windows

## BYO Images and Prompts

The following directories need to be created and populated with 1024x1024 images. The code loads these at runtime and randomly selects from them under certain situations:
- `./error_images` - used whenever there is an error interacting with automic1111
- `./loading_images`- used while waiting for a response from automic1111. Images are cycled at a set cadence
- `./safe_images` - used when an image in flag and censored by the nsfw filter (ie a black image is return). 

- `./gpt_prompt.json` - a json array of prompts to randomly use when interacting with chatgpt
- `./random_prompts.json` - a json array of prompts to randomly use with stable diffusion if chatgpt is not enabled



## Install
Local install can be accomplished with 

 `poetry install`

Entry point for the bot is chaos_nightmare/app.py


## Notes

- This was a sort of weekend project that could be heavily improved. There is *some* error handling and *some* attempts at good organization for QoL and maintenance, but not a lot. 

- There is a local patch to twitchio that requires [this PR](https://github.com/PythonistaGuild/TwitchIO/pull/416) to be approved for the timer calculation to work

## Acceptable Use Policy

Please read and adhere to our [Acceptable Use Policy](./ACCEPTABLE_USE_POLICY.md) before using this bot. By using the bot or its code, you agree to comply with the guidelines outlined in the policy.


## Credit
- Greatly inspired by the work of zeetwii's [hackable rover](https://github.com/zeetwii/llmRover)
- Heavily enabled by the foundational chatbot work by the [PythonistaGuild](https://github.com/PythonistaGuild/TwitchIO)




