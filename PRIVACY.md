# Privacy Policy

## What this plugin sends

When a tool is invoked, the plugin sends to `https://movoa.ai`:

- the prompt text you or your workflow supplied
- the model, duration, resolution, and aspect ratio you picked
- for photo to video, the first-frame image URL you supplied
- for `check_status`, the task id
- your Movoa API key, as a Bearer token, to authenticate the request

Nothing else leaves the plugin.

## What this plugin stores

Nothing. The API key is held by Dify's credential storage, not by the plugin, and the plugin keeps no state between calls.

## What the service does with it

Prompts and generated videos are processed by Movoa to produce the result and are served from its CDN (`cdn.movoa.ai`) at a public URL; treat that URL as public. Each run is recorded on your Movoa account and draws credits at the prices on <https://movoa.ai/pricing>. Movoa's privacy policy applies: <https://movoa.ai/privacy-policy>

## Contact

support@movoa.ai, or <https://github.com/hanshs474/movoa-dify-plugin/issues>
