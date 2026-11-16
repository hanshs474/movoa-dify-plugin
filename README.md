# Movoa for Dify: text to video and photo to video with sound

Unlimited AI video generator with sound: on paid plans the tenth take of a shot costs what the first did, and your first clip is free to make right now. This is the official Dify plugin for [Movoa](https://movoa.ai/?utm_source=dify&utm_medium=plugin): it puts the Movoa API behind two tools so a workflow or agent can turn a prompt or a photo into an MP4 clip with synchronized sound.

## Tools

| Tool | What it does |
|---|---|
| `generate_video` | Prompt in, MP4 URL out, with sound. Supports [text to video](https://movoa.ai/video/text-to-video) and [photo to video](https://movoa.ai/video/photo-to-video) via an optional `image_url`, returning [AI video with audio](https://movoa.ai/video/ai-video-with-audio) |
| `check_status` | Task id in, MP4 URL out once the run is ready; otherwise reports whether it is still generating or queued |

Models available: `minimax-h3` (default), [Seedance 2.5](https://movoa.ai/video/seedance-2-5), `seedance-2`, `seedance-2-fast`, `seedance-2-mini`, and [Veo 3](https://movoa.ai/video/google-veo-3).

Video generation takes minutes. `generate_video` waits up to about four minutes; a longer run returns a `task_id`, and `check_status` picks it up later so workflows never hit Dify's tool timeout.

## Setup and connection requirements

1. Sign in on [Movoa](https://movoa.ai/?utm_source=dify&utm_medium=plugin) and create an API key at <https://movoa.ai/settings/apikeys>.
2. Install the plugin, open its credentials, and paste the key. The key is verified with a read-only credits lookup that starts no run.
3. Runs cost credits on your Movoa account, at the prices on <https://movoa.ai/pricing>.

The tools call `https://movoa.ai` over HTTPS and results are served from `https://cdn.movoa.ai`, so your Dify instance needs outbound network access to those two hosts.

## Source

<https://github.com/hanshs474/movoa-dify-plugin>. Issues and pull requests welcome there.
